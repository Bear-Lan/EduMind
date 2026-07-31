"""
EduMind Retrieval-Augmented Generation (RAG) Package

Exposes the RAG module and its singleton.
"""

from rag.service import RAGModule

rag_module = RAGModule()

__all__ = [
    "RAGModule",
    "rag_module",
]
