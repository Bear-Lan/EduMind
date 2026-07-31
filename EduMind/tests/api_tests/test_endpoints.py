"""
API Endpoints Integration Tests

Tests all REST endpoints (Auth, Profile, Plan, Chat, Assessment, Learning, Resources)
using httpx.AsyncClient against the FastAPI application.
"""

import sys
import os
import shutil
import unittest
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from main import app
from models import Base
from config.settings import settings
from core.dependencies import get_db
from rag import rag_module


class TestAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration test suite executing HTTP requests against local router endpoints."""

    async def asyncSetUp(self) -> None:
        # 1. Database Setup (SQLite in-memory)
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
        self.async_session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Override FastAPI dependency to inject the test database session
        async def override_get_db():
            async with self.async_session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = override_get_db

        # 2. Qdrant Setup (Local Path Mode)
        self.test_qdrant_path = (
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_api"
        )
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384
        settings.deepseek_api_key = ""  # Force mock LLM
        settings.jwt_secret_key = "test_secret_key_minimum_32_characters"

        rag_module._client = None

        # Build local transport client to route directly to ASGI application
        # Using ASGITransport instead of old app=app parameter for httpx >= 0.21.0
        self.client = AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self) -> None:
        app.dependency_overrides.clear()
        await self.client.aclose()
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await self.engine.dispose()

        if rag_module._client:
            await rag_module._client.close()
            rag_module._client = None

        if self.test_qdrant_path.exists():
            shutil.rmtree(self.test_qdrant_path, ignore_errors=True)

    async def test_full_student_lifecycle_api(self) -> None:
        """Validate registration, login, profile check, plan, chat, and step completion."""

        # 1. Registration
        reg_payload = {
            "username": "api_learner",
            "password": "secretpassword",
            "name": "API Learner",
            "grade": "Grade 10",
            "subject": "数学",
            "target_score": 95.0,
        }
        res = await self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertIn(res.status_code, (200, 201))
        res_json = res.json()
        self.assertTrue(res_json["success"])
        token = res_json["data"]["access_token"]
        self.assertIsNotNone(token)

        # Build Authorization header
        auth_headers = {"Authorization": f"Bearer {token}"}

        # 2. Duplicate registration check (should fail)
        res_dup = await self.client.post("/api/v1/auth/register", json=reg_payload)
        self.assertEqual(res_dup.status_code, 400)  # Bad request / Already exists

        # 3. Login
        login_payload = {"username": "api_learner", "password": "secretpassword"}
        res_login = await self.client.post("/api/v1/auth/login", json=login_payload)
        self.assertEqual(res_login.status_code, 200)
        self.assertEqual(res_login.json()["data"]["token_type"], "bearer")

        # 4. Get Profile (Protected)
        res_prof = await self.client.get("/api/v1/profile", headers=auth_headers)
        self.assertEqual(res_prof.status_code, 200)
        prof_data = res_prof.json()["data"]
        self.assertEqual(prof_data["current_goal"], "Grade 10 数学 (Target: 95.0)")
        self.assertEqual(prof_data["mastery_map"], {})

        # 5. Update Profile
        up_payload = {"current_goal": "Master algebra", "learning_preferences": {"pace": "fast"}}
        res_up = await self.client.put(
            "/api/v1/profile", json=up_payload, headers=auth_headers
        )
        self.assertEqual(res_up.status_code, 200)
        self.assertEqual(res_up.json()["data"]["current_goal"], "Master algebra")

        # 6. Retrieve Learning Plan (Auto-generation)
        res_plan = await self.client.get("/api/v1/plan/current", headers=auth_headers)
        self.assertEqual(res_plan.status_code, 200)
        plan_data = res_plan.json()["data"]
        target_topic = plan_data["target_topic"]
        self.assertIsNotNone(target_topic)
        self.assertEqual(len(plan_data["learning_steps"]), 3)
        plan_id = plan_data["plan_id"]

        # 7. Ask Chat Coach
        chat_payload = {"message": "Tell me about math variables."}
        res_chat = await self.client.post(
            "/api/v1/chat", json=chat_payload, headers=auth_headers
        )
        self.assertEqual(res_chat.status_code, 200)
        chat_data = res_chat.json()["data"]
        self.assertIn("[Mock AI Coach Response]", chat_data["response"])

        # Check Chat History
        res_hist = await self.client.get("/api/v1/chat/history", headers=auth_headers)
        self.assertEqual(res_hist.status_code, 200)
        self.assertEqual(len(res_hist.json()["data"]), 2)  # User message + AI message

        # 8. Complete Learning Step
        comp_payload = {
            "plan_id": plan_id,
            "step_number": 1,
            "score": 0.85,
            "duration": 120,
        }
        res_comp = await self.client.post(
            "/api/v1/learning/complete", json=comp_payload, headers=auth_headers
        )
        self.assertEqual(res_comp.status_code, 200)
        comp_data = res_comp.json()["data"]
        self.assertEqual(comp_data["step_completed"], 1)
        self.assertFalse(comp_data["all_steps_completed"])

        # Fetch Overall Progress
        res_prog = await self.client.get(
            "/api/v1/learning/progress", headers=auth_headers
        )
        self.assertEqual(res_prog.status_code, 200)
        prog_data = res_prog.json()["data"]
        self.assertEqual(prog_data["completions_count"], 1)
        self.assertAlmostEqual(prog_data["mastery_map"].get(target_topic), 1 / 3)

        # 9. Submit Assessment
        assess_payload = {
            "topic": target_topic,
            "score": 0.95,
            "duration": 400,
        }
        res_assess = await self.client.post(
            "/api/v1/assessment", json=assess_payload, headers=auth_headers
        )
        self.assertEqual(res_assess.status_code, 200)
        assess_data = res_assess.json()["data"]
        self.assertIsNotNone(assess_data.get("recommended_topic"))


if __name__ == "__main__":
    unittest.main()
