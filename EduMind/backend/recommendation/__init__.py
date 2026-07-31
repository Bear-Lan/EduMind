"""
EduMind Recommendation Engine Package

Exposes the recommendation engine and its singleton.
"""

from recommendation.service import RecommendationEngine

recommendation_engine = RecommendationEngine()

__all__ = [
    "RecommendationEngine",
    "recommendation_engine",
]
