"""Interference graph construction from instruction-level liveness."""

from dataclasses import dataclass

from .cfg import ControlFlowGraph
from .ir import Assign, Instruction
from .liveness import LivenessResult, uses_defs


@dataclass(frozen=True)
class InterferenceGraph:
    neighbors: dict[str, frozenset[str]]

    @property
    def variables(self) -> frozenset[str]:
        return frozenset(self.neighbors)

    def degree(self, variable: str) -> int:
        return len(self.neighbors[variable])


def build_interference(cfg: ControlFlowGraph, live: LivenessResult) -> InterferenceGraph:
    variables: set[str] = set()
    mutable: dict[str, set[str]] = {}
    for block in cfg.blocks:
        for offset, instruction in enumerate(block.instructions):
            used, defined = uses_defs(instruction)
            variables |= used | defined
            # Any two values simultaneously live at a program point must occupy
            # distinct registers, including values live into a function that
            # are not defined by this TAC fragment.
            for live_set in (live.instruction_in[(block.id, offset)],
                             live.instruction_out[(block.id, offset)]):
                for name in live_set:
                    mutable.setdefault(name, set())
                    mutable[name].update(live_set - {name})
            for dest in defined:
                mutable.setdefault(dest, set())
                for other in live.instruction_out[(block.id, offset)]:
                    copy_source = (isinstance(instruction, Assign)
                                   and instruction.value.is_variable
                                   and instruction.value.value == other)
                    if other != dest and not copy_source:
                        mutable.setdefault(other, set())
                        mutable[dest].add(other)
                        mutable[other].add(dest)
    for name in variables:
        mutable.setdefault(name, set())
    return InterferenceGraph({name: frozenset(adjacent) for name, adjacent in mutable.items()})
