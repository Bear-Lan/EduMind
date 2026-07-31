"""
EduMind Student Profile Module Package

Exposes the profile service and its singleton.
"""

from student_profile.service import StudentProfileService

student_profile_service = StudentProfileService()

__all__ = [
    "StudentProfileService",
    "student_profile_service",
]
