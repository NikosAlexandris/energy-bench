"""
Automated analysis tools for time series bias detection and method recommendation.
"""

from .bias_detection import (
    BiasDetectionResult,
    SubperiodRecommendation,
    detect_bias_patterns,
    recommend_adjustment_strategy,
)

__all__ = [
    "BiasDetectionResult",
    "SubperiodRecommendation",
    "detect_bias_patterns",
    "recommend_adjustment_strategy",
]
