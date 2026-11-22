"""Analysis package exports."""

from neuralshield.analysis.statistics import (
    compute_descriptive_statistics,
    identify_constant_features,
)
from neuralshield.analysis.distributions import (
    analyze_class_balance,
    compute_feature_quantiles,
)
from neuralshield.analysis.correlations import (
    compute_correlation_matrix,
    find_high_correlation_pairs,
)
from neuralshield.analysis.comparisons import (
    compare_benign_vs_attack,
)

__all__ = [
    "compute_descriptive_statistics",
    "identify_constant_features",
    "analyze_class_balance",
    "compute_feature_quantiles",
    "compute_correlation_matrix",
    "find_high_correlation_pairs",
    "compare_benign_vs_attack",
]
