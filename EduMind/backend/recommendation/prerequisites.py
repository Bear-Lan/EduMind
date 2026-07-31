"""
EduMind Curriculum Prerequisites Map

Defines topic dependencies for rule-based learning path recommendation.
"""

# Dict mapping Topic -> list of prerequisite topics
CURRICULUM_PREREQUISITES: dict[str, list[str]] = {
    "Basic Arithmetic": [],
    "Introduction to Algebra": ["Basic Arithmetic"],
    "Linear Equations": ["Introduction to Algebra"],
    "Quadratic Equations": ["Linear Equations"],
    "Basic Geometry": ["Basic Arithmetic"],
    "Coordinate Geometry": ["Linear Equations", "Basic Geometry"],
}
