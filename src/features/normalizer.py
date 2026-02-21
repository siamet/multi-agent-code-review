"""Feature value normalization to [0, 1] range."""

from typing import Dict, Optional, Tuple


# Default bounds for min-max normalization
DEFAULT_BOUNDS: Dict[str, Tuple[float, float]] = {
    "lines_of_code": (0, 500),
    "logical_lines": (0, 300),
    "cyclomatic_complexity": (1, 50),
    "nesting_depth_max": (0, 10),
    "nesting_depth_avg": (0, 5),
    "parameter_count": (0, 15),
    "return_count": (0, 10),
    "branch_count": (0, 30),
    "loop_count": (0, 15),
    "comment_count": (0, 50),
    "call_count": (0, 50),
    "fan_in": (0, 50),
    "fan_out": (0, 50),
    "afferent_coupling": (0, 50),
    "efferent_coupling": (0, 50),
    "coupling_between_objects": (0, 100),
    "lack_of_cohesion": (0, 1),
    "depth_of_inheritance": (0, 10),
    "number_of_children": (0, 20),
    "instability": (0, 1),
    "abstractness": (0, 1),
}


class FeatureNormalizer:
    """Normalizes metric values to [0, 1] using min-max scaling.

    Uses configurable bounds per metric name. Values outside bounds
    are clamped.
    """

    def __init__(
        self,
        bounds: Optional[Dict[str, Tuple[float, float]]] = None,
    ) -> None:
        self._bounds = bounds or dict(DEFAULT_BOUNDS)

    def normalize(self, value: float, metric_name: str) -> float:
        """Normalize a single value to [0, 1].

        Args:
            value: Raw metric value.
            metric_name: Name of the metric (used to look up bounds).

        Returns:
            Normalized value in [0, 1].
        """
        lo, hi = self._bounds.get(metric_name, (0, 1))
        if hi == lo:
            return 0.0
        normalized = (value - lo) / (hi - lo)
        return max(0.0, min(1.0, normalized))

    def set_bounds(self, metric_name: str, lo: float, hi: float) -> None:
        """Set or update normalization bounds for a metric."""
        self._bounds[metric_name] = (lo, hi)
