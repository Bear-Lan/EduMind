"""
EduMind LLM Service Package

Exposes the LLM service and its singleton.
"""

from llm.service import LLMService

llm_service = LLMService()

__all__ = [
    "LLMService",
    "llm_service",
]
