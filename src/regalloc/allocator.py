"""Graph-coloring allocation with simplify/select and explicit spill slots."""

from dataclasses import dataclass
from typing import Callable

from .interference import InterferenceGraph

SpillRanker = Callable[[str, InterferenceGraph], float]


@dataclass(frozen=True)
class Allocation:
    registers: dict[str, str]
    spills: dict[str, int]
    register_count: int


def traditional_spill_score(variable: str, graph: InterferenceGraph) -> float:
    """Lower means cheaper to spill; degree-only baseline for this phase."""
    return 1.0 / (graph.degree(variable) + 1)


def allocate(graph: InterferenceGraph, registers: list[str],
             spill_score: SpillRanker | None = None) -> Allocation:
    """Color the graph; failed colors receive unique abstract spill slots.

    ``spill_score`` is interpreted as spill cost (lower values are preferred
    when selecting a potential spill). Coloring remains the correctness gate.
    """
    if len(set(registers)) != len(registers):
        raise ValueError("register names must be unique")
    if not registers and graph.variables:
        raise ValueError("at least one register is required")
    ranker = spill_score or traditional_spill_score
    k = len(registers)
    remaining = set(graph.variables)
    stack: list[str] = []
    while remaining:
        low_degree = sorted((v for v in remaining
                             if len(graph.neighbors[v] & remaining) < k))
        if low_degree:
            chosen = low_degree[0]
        else:
            chosen = min(remaining, key=lambda v: (ranker(v, graph), v))
        stack.append(chosen)
        remaining.remove(chosen)

    colors: dict[str, str] = {}
    spilled: list[str] = []
    while stack:
        variable = stack.pop()
        unavailable = {colors[n] for n in graph.neighbors[variable] if n in colors}
        available = next((reg for reg in registers if reg not in unavailable), None)
        if available is None:
            spilled.append(variable)
        else:
            colors[variable] = available
    return Allocation(colors, {name: i for i, name in enumerate(sorted(spilled))}, k)


def validate_allocation(graph: InterferenceGraph, allocation: Allocation) -> list[str]:
    """Return all graph-coloring or coverage violations (empty means valid)."""
    errors: list[str] = []
    assigned = set(allocation.registers) | set(allocation.spills)
    missing = graph.variables - assigned
    extra = assigned - graph.variables
    if missing:
        errors.append(f"unallocated variables: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unknown variables allocated: {', '.join(sorted(extra))}")
    overlap = set(allocation.registers) & set(allocation.spills)
    if overlap:
        errors.append(f"variables both colored and spilled: {', '.join(sorted(overlap))}")
    for variable, adjacent in graph.neighbors.items():
        for neighbor in adjacent:
            if variable < neighbor and variable in allocation.registers and neighbor in allocation.registers:
                if allocation.registers[variable] == allocation.registers[neighbor]:
                    errors.append(f"interfering variables '{variable}' and '{neighbor}' share {allocation.registers[variable]}")
    if len(set(allocation.spills.values())) != len(allocation.spills):
        errors.append("spill slots must be unique")
    return errors
