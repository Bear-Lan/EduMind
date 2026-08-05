"""
Unit Tests for LLM Service Module

Verifies prompt formatting and mock response logic.
"""

import sys
import os
import unittest
from pathlib import Path

# Add backend directory to sys.path so we can import local modules
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from config.settings import settings
from llm import llm_service
from services.model_config import model_config_service


class TestLLMService(unittest.IsolatedAsyncioTestCase):
    """Asynchronous unit tests for LLMService."""

    async def asyncSetUp(self) -> None:
        # Save original API Key to restore it later
        self.original_api_key = settings.deepseek_api_key
        self.original_runtime = model_config_service.runtime
        # Force empty key to trigger the mock offline mode for tests
        settings.deepseek_api_key = ""
        model_config_service.reset_to_environment()

    async def asyncTearDown(self) -> None:
        # Restore original configuration
        settings.deepseek_api_key = self.original_api_key
        model_config_service._runtime = self.original_runtime

    async def test_generate_response_mock(self) -> None:
        """Verify mock responder output contains core indicators."""
        messages = [
            {"role": "system", "content": "Test System Prompt"},
            {"role": "user", "content": "How do I solve 2x + 5 = 15?"},
        ]
        response = await llm_service.generate_response(messages)

        self.assertIn("[Mock AI Coach Response]", response)
        self.assertIn("DEEPSEEK_API_KEY", response)

    async def test_chat_mock(self) -> None:
        """Verify chat prompt is generated and gets mocked."""
        prompt = "Explain algebra variables."
        context = "[Doc 1]: Variables like x are unknown numbers."
        profile_summary = "Algebra score: 0.5"

        response = await llm_service.chat(prompt, context, profile_summary)
        self.assertIn("[Mock AI Coach Response]", response)
        self.assertIn("DEEPSEEK_API_KEY", response)

    async def test_explain_mock(self) -> None:
        """Verify explain concept gets mocked."""
        response = await llm_service.explain(
            concept="Coordinate Geometry", context="Context data"
        )
        self.assertIn("[Mock AI Coach Response]", response)

    async def test_summarize_mock(self) -> None:
        """Verify summarize gets mocked."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"},
        ]
        response = await llm_service.summarize(history)
        self.assertEqual(response, "关于学习内容与方法的探究")


if __name__ == "__main__":
    unittest.main()
