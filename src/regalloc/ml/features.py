"""Program-derived features for estimating the cost of spilling variables."""

from dataclasses import dataclass

from ..interference import InterferenceGraph
from ..ir import Instruction
from ..liveness import LivenessResult, uses_defs


@dataclass(frozen=True)
class SpillFeatures:
    use_count: int
    live_range: int
    next_use_distance: int
    interference_degree: int

    def as_vector(self) -> list[float]:
        return [self.use_count, self.live_range, self.next_use_distance,
                self.interference_degree]


def extract_features(instructions: list[Instruction], graph: InterferenceGraph,
                     liveness: LivenessResult) -> dict[str, SpillFeatures]:
    """Measure use count, live extent, next-use distance and graph degree."""
    uses_at: dict[str, list[int]] = {name: [] for name in graph.variables}
    positions: dict[str, list[int]] = {name: [] for name in graph.variables}
    position = 0
    for position, instruction in enumerate(instructions):
        used, defined = uses_defs(instruction)
        for name in used:
            uses_at[name].append(position)
            positions[name].append(position)
        for name in defined:
            positions[name].append(position)
        position += 1
    # CFG blocks preserve source order; sorted (block, offset) pairs therefore
    # map the instruction-level live sets back to flat source positions.
    ordered_keys = sorted(liveness.instruction_in)
    if len(ordered_keys) == len(instructions):
        for position, key in enumerate(ordered_keys):
            live_names = liveness.instruction_in[key] | liveness.instruction_out[key]
            for name in live_names:
                positions[name].append(position)
    result: dict[str, SpillFeatures] = {}
    length = max(position, 1)
    for name in sorted(graph.variables):
        occurrences = positions[name]
        first = min(occurrences, default=0)
        last = max(occurrences, default=first)
        first_use = min(uses_at[name], default=length)
        next_distance = min((p - first_use for p in uses_at[name] if p > first_use),
                            default=length - first_use)
        result[name] = SpillFeatures(
            use_count=len(uses_at[name]),
            live_range=max(1, last - first + 1),
            next_use_distance=max(0, next_distance),
            interference_degree=graph.degree(name),
        )
    return result
