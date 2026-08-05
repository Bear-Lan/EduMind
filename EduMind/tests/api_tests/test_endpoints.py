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
from models import Base, AdminUser, SystemModelConfig
from config.settings import settings
from core.dependencies import get_db
from core.security import hash_password
from rag import rag_module
from services.model_config import model_config_service


class TestAPIEndpoints(unittest.IsolatedAsyncioTestCase):
    """Integration test suite executing HTTP requests against local router endpoints."""

    async def asyncSetUp(self) -> None:
        self.original_settings = {
            "qdrant_path": settings.qdrant_path,
            "embedding_dimensions": settings.embedding_dimensions,
            "embedding_api_key": settings.embedding_api_key,
            "deepseek_api_key": settings.deepseek_api_key,
            "jwt_secret_key": settings.jwt_secret_key,
        }
        self.original_runtime = model_config_service.runtime

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
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        app.dependency_overrides[get_db] = override_get_db

        # 2. Qdrant Setup (Local Path Mode)
        self.test_qdrant_path = (
            Path(__file__).resolve().parent / "test_data" / "test_qdrant_api"
        )
        shutil.rmtree(self.test_qdrant_path, ignore_errors=True)
        settings.qdrant_path = str(self.test_qdrant_path)
        settings.embedding_dimensions = 384
        settings.embedding_api_key = ""  # Tests must not depend on network access
        settings.deepseek_api_key = ""  # Force mock LLM
        settings.jwt_secret_key = "test_secret_key_minimum_32_characters"
        model_config_service.reset_to_environment()

        async with self.async_session_factory() as session:
            session.add(AdminUser(
                username="test_admin",
                hashed_password=hash_password("AdminTest#Password2026"),
                display_name="Test Administrator",
                must_change_password=True,
            ))
            session.add(SystemModelConfig(
                id=1,
                llm_base_url="https://example.com/v1",
                llm_model="test-chat-model",
                llm_max_tokens=512,
                llm_temperature=0.2,
                llm_enable_thinking=False,
                llm_timeout_seconds=30,
                embedding_base_url="https://example.com/v1",
                embedding_model="test-embedding-model",
                embedding_dimensions=384,
            ))
            await session.commit()

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

        for name, value in self.original_settings.items():
            setattr(settings, name, value)
        model_config_service._runtime = self.original_runtime

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

        # 10. Student account self-service
        account = await self.client.get("/api/v1/auth/account", headers=auth_headers)
        self.assertEqual(account.status_code, 200)
        self.assertEqual(account.json()["data"]["username"], "api_learner")
        account_update = await self.client.put(
            "/api/v1/auth/account",
            headers=auth_headers,
            json={
                "username": "api_learner",
                "name": "API Learner Updated",
                "grade": "Grade 10",
                "subject": "Mathematics",
                "target_score": 96,
            },
        )
        self.assertEqual(account_update.status_code, 200)
        self.assertEqual(account_update.json()["data"]["name"], "API Learner Updated")

        password_update = await self.client.put(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={"current_password": "secretpassword", "new_password": "NewStudent#Password2026"},
        )
        self.assertEqual(password_update.status_code, 200)
        new_login = await self.client.post(
            "/api/v1/auth/login",
            json={"username": "api_learner", "password": "NewStudent#Password2026"},
        )
        self.assertEqual(new_login.status_code, 200)

    async def test_admin_configuration_access_control(self) -> None:
        """Only administrator tokens may read or update encrypted model settings."""
        student_response = await self.client.post("/api/v1/auth/register", json={
            "username": "acl_student",
            "password": "studentpassword",
            "name": "ACL Student",
            "grade": "Grade 10",
            "subject": "Mathematics",
        })
        student_token = student_response.json()["data"]["access_token"]
        student_headers = {"Authorization": f"Bearer {student_token}"}
        denied = await self.client.get("/api/v1/admin/config", headers=student_headers)
        self.assertEqual(denied.status_code, 401)

        login = await self.client.post("/api/v1/admin/login", json={
            "username": "test_admin",
            "password": "AdminTest#Password2026",
        })
        self.assertEqual(login.status_code, 200)
        admin_token = login.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        config_response = await self.client.get("/api/v1/admin/config", headers=admin_headers)
        self.assertEqual(config_response.status_code, 200)
        self.assertNotIn("llm_api_key", config_response.json()["data"])

        payload = {
            "llm_api_key": "test-secret-not-real",
            "llm_base_url": "https://example.com/v1",
            "llm_model": "test-chat-model",
            "llm_max_tokens": 512,
            "llm_temperature": 0.2,
            "llm_enable_thinking": False,
            "llm_timeout_seconds": 30,
            "embedding_api_key": "test-embedding-secret",
            "embedding_base_url": "https://example.com/v1",
            "embedding_model": "test-embedding-model",
            "embedding_dimensions": 384,
        }
        updated = await self.client.put("/api/v1/admin/config", headers=admin_headers, json=payload)
        self.assertEqual(updated.status_code, 200)
        response_data = updated.json()["data"]
        self.assertTrue(response_data["llm_api_key_configured"])
        self.assertNotIn("test-secret-not-real", str(response_data))

        async with self.async_session_factory() as session:
            stored = await session.get(SystemModelConfig, 1)
            self.assertNotIn("test-secret-not-real", stored.llm_api_key_encrypted)

        admin_denied_student_api = await self.client.get("/api/v1/profile", headers=admin_headers)
        self.assertEqual(admin_denied_student_api.status_code, 401)

        student_list = await self.client.get("/api/v1/admin/students", headers=admin_headers)
        self.assertEqual(student_list.status_code, 200)
        self.assertEqual(student_list.json()["data"]["total"], 1)
        student_id = student_list.json()["data"]["items"][0]["id"]

        update_student = await self.client.put(
            f"/api/v1/admin/students/{student_id}",
            headers=admin_headers,
            json={
                "username": "acl_student",
                "name": "ACL Student Updated",
                "grade": "Grade 11",
                "subject": "Mathematics",
                "target_score": 92,
            },
        )
        self.assertEqual(update_student.status_code, 200)

        reset_password = await self.client.put(
            f"/api/v1/admin/students/{student_id}/password",
            headers=admin_headers,
            json={"new_password": "Temporary#Password2026"},
        )
        self.assertEqual(reset_password.status_code, 200)
        reset_login = await self.client.post(
            "/api/v1/auth/login",
            json={"username": "acl_student", "password": "Temporary#Password2026"},
        )
        self.assertEqual(reset_login.status_code, 200)
        self.assertTrue(reset_login.json()["data"]["must_change_password"])
        reset_student_headers = {
            "Authorization": f"Bearer {reset_login.json()['data']['access_token']}"
        }

        disable_student = await self.client.put(
            f"/api/v1/admin/students/{student_id}/status",
            headers=admin_headers,
            json={"is_active": False},
        )
        self.assertEqual(disable_student.status_code, 200)
        disabled_access = await self.client.get(
            "/api/v1/auth/account", headers=reset_student_headers
        )
        self.assertEqual(disabled_access.status_code, 401)

        reenable_student = await self.client.put(
            f"/api/v1/admin/students/{student_id}/status",
            headers=admin_headers,
            json={"is_active": True},
        )
        self.assertEqual(reenable_student.status_code, 200)


if __name__ == "__main__":
    unittest.main()
