"""Deterministic spill-cost estimator trained on a transparent proxy policy."""

from dataclasses import dataclass
import random

from sklearn.tree import DecisionTreeRegressor

from ..interference import InterferenceGraph
from .features import SpillFeatures


def _proxy_cost(features: SpillFeatures) -> float:
    """Synthetic cost: frequent/long-lived values cost more; high degree costs less."""
    return (3.0 * features.use_count + 1.0 * features.live_range
            + 0.25 * features.next_use_distance
            - 2.0 * features.interference_degree)


@dataclass
class MLSpillRanker:
    model: DecisionTreeRegressor
    features: dict[str, SpillFeatures]

    def __call__(self, variable: str, graph: InterferenceGraph) -> float:
        feature = self.features.get(variable)
        if feature is None:
            feature = SpillFeatures(0, 1, 0, graph.degree(variable))
        return float(self.model.predict([feature.as_vector()])[0])


def train_ranker(features: dict[str, SpillFeatures], *, samples: int = 512,
                 random_state: int = 42) -> MLSpillRanker:
    """Fit a small regressor to a deterministic synthetic spill-cost proxy.

    These labels do not measure runtime or prove improvement over a baseline;
    they provide a reproducible demonstration of feature-based ML ranking.
    """
    if samples < 16:
        raise ValueError("samples must be at least 16")
    rng = random.Random(random_state)
    matrix: list[list[float]] = []
    target: list[float] = []
    for _ in range(samples):
        item = SpillFeatures(rng.randint(0, 30), rng.randint(1, 40),
                             rng.randint(0, 40), rng.randint(0, 20))
        matrix.append(item.as_vector())
        target.append(_proxy_cost(item))
    model = DecisionTreeRegressor(max_depth=8, random_state=random_state)
    model.fit(matrix, target)
    return MLSpillRanker(model, dict(features))
