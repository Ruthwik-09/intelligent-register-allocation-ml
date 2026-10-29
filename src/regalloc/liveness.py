"""Use/definition extraction and fixed-point live-variable analysis."""

from dataclasses import dataclass

from .cfg import ControlFlowGraph
from .ir import Assign, BinaryOp, Goto, IfGoto, Instruction, Operand, Return


def _variables(*operands: Operand | None) -> set[str]:
    return {op.value for op in operands if op is not None and op.is_variable}


def uses_defs(instruction: Instruction) -> tuple[set[str], set[str]]:
    """Return variable uses and definitions for a TAC instruction."""
    if isinstance(instruction, Assign):
        return _variables(instruction.value), {instruction.dest}
    if isinstance(instruction, BinaryOp):
        return _variables(instruction.left, instruction.right), {instruction.dest}
    if isinstance(instruction, IfGoto):
        return _variables(instruction.left, instruction.right), set()
    if isinstance(instruction, Return):
        return _variables(instruction.value), set()
    if isinstance(instruction, Goto):
        return set(), set()
    return set(), set()


@dataclass(frozen=True)
class LivenessResult:
    block_use: dict[int, frozenset[str]]
    block_def: dict[int, frozenset[str]]
    live_in: dict[int, frozenset[str]]
    live_out: dict[int, frozenset[str]]
    instruction_in: dict[tuple[int, int], frozenset[str]]
    instruction_out: dict[tuple[int, int], frozenset[str]]


def analyze_liveness(cfg: ControlFlowGraph) -> LivenessResult:
    """Solve IN[b]=USE[b]∪(OUT[b]-DEF[b]), OUT[b]=∪IN[succ]."""
    uses: dict[int, set[str]] = {}
    defs: dict[int, set[str]] = {}
    for block in cfg.blocks:
        seen_defs: set[str] = set()
        block_uses: set[str] = set()
        for instruction in block.instructions:
            instruction_uses, instruction_defs = uses_defs(instruction)
            block_uses.update(instruction_uses - seen_defs)
            seen_defs.update(instruction_defs)
        uses[block.id], defs[block.id] = block_uses, seen_defs

    live_in = {block.id: set() for block in cfg.blocks}
    live_out = {block.id: set() for block in cfg.blocks}
    changed = True
    while changed:
        changed = False
        for block in reversed(cfg.blocks):
            out = set().union(*(live_in[s] for s in cfg.successors[block.id]))
            inside = uses[block.id] | (out - defs[block.id])
            if out != live_out[block.id] or inside != live_in[block.id]:
                live_out[block.id], live_in[block.id] = out, inside
                changed = True

    instruction_in: dict[tuple[int, int], frozenset[str]] = {}
    instruction_out: dict[tuple[int, int], frozenset[str]] = {}
    for block in cfg.blocks:
        live = set(live_out[block.id])
        for offset in range(len(block.instructions) - 1, -1, -1):
            instruction = block.instructions[offset]
            instruction_out[(block.id, offset)] = frozenset(live)
            used, defined = uses_defs(instruction)
            live = used | (live - defined)
            instruction_in[(block.id, offset)] = frozenset(live)

    return LivenessResult(
        {k: frozenset(v) for k, v in uses.items()},
        {k: frozenset(v) for k, v in defs.items()},
        {k: frozenset(v) for k, v in live_in.items()},
        {k: frozenset(v) for k, v in live_out.items()},
        instruction_in, instruction_out,
    )
