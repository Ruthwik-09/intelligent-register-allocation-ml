"""Basic-block partitioning and control-flow graph construction."""

from dataclasses import dataclass

from .ir import Goto, IfGoto, Instruction, Label, Return


@dataclass(frozen=True)
class BasicBlock:
    id: int
    instructions: tuple[Instruction, ...]
    label: str | None = None


@dataclass(frozen=True)
class ControlFlowGraph:
    blocks: tuple[BasicBlock, ...]
    successors: dict[int, frozenset[int]]
    entry: int | None

    @property
    def predecessors(self) -> dict[int, frozenset[int]]:
        pred: dict[int, set[int]] = {block.id: set() for block in self.blocks}
        for source, destinations in self.successors.items():
            for destination in destinations:
                pred[destination].add(source)
        return {node: frozenset(sources) for node, sources in pred.items()}


def build_cfg(instructions: list[Instruction]) -> ControlFlowGraph:
    """Partition instructions and connect fall-through and branch edges."""
    if not instructions:
        return ControlFlowGraph((), {}, None)

    labels: dict[str, int] = {}
    for index, instruction in enumerate(instructions):
        if isinstance(instruction, Label):
            if instruction.name in labels:
                raise ValueError(f"duplicate label '{instruction.name}'")
            labels[instruction.name] = index

    leaders = {0}
    for index, instruction in enumerate(instructions):
        if isinstance(instruction, Label):
            leaders.add(index)
        if isinstance(instruction, (Goto, IfGoto, Return)) and index + 1 < len(instructions):
            leaders.add(index + 1)
        if isinstance(instruction, (Goto, IfGoto)) and instruction.target not in labels:
            raise ValueError(f"undefined label '{instruction.target}'")

    starts = sorted(leaders)
    ranges = [(start, starts[i + 1] if i + 1 < len(starts) else len(instructions))
              for i, start in enumerate(starts)]
    blocks = tuple(
        BasicBlock(block_id, tuple(instructions[start:end]),
                   instructions[start].name if isinstance(instructions[start], Label) else None)
        for block_id, (start, end) in enumerate(ranges)
    )
    index_to_block = {index: block.id for block, (start, end) in zip(blocks, ranges)
                      for index in range(start, end)}
    label_to_block = {name: index_to_block[index] for name, index in labels.items()}

    edges: dict[int, set[int]] = {block.id: set() for block in blocks}
    for block_id, (start, end) in enumerate(ranges):
        last = instructions[end - 1]
        fallthrough = block_id + 1 if block_id + 1 < len(blocks) else None
        if isinstance(last, Goto):
            edges[block_id].add(label_to_block[last.target])
        elif isinstance(last, IfGoto):
            edges[block_id].add(label_to_block[last.target])
            if fallthrough is not None:
                edges[block_id].add(fallthrough)
        elif not isinstance(last, Return) and fallthrough is not None:
            edges[block_id].add(fallthrough)

    return ControlFlowGraph(blocks, {node: frozenset(destinations)
                                     for node, destinations in edges.items()}, 0)
