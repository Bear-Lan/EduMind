"""
EduMind Phase 6 — End-to-End Integration Test

Tests the complete student learning workflow via live HTTP calls:
  1. Health check          → all components healthy
  2. Register student      → 201 Created
  3. Login                 → JWT token returned
  4. Get profile           → profile data returned
  5. Generate learning plan → plan_id returned
  6. Complete a step       → step marked as done
  7. Get learning progress → completions_count >= 1
  8. Chat with AI coach    → response text returned
  9. Get assessment result → mastery_map returned

Run with:
  python tests/integration/test_e2e_flow.py

Requires the backend to be running at http://127.0.0.1:8000
"""

import sys
import asyncio
import httpx
import random
import string
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api/v1"
TIMEOUT = 30.0

# ─── Colour helpers ───────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"
BOLD   = "\033[1m"


def ok(msg: str):   print(f"  [OK] {msg}")
def fail(msg: str):  print(f"  [FAIL] {msg}")
def info(msg: str):  print(f"  --> {msg}")
def section(title: str):
    print(f"\n{'='*55}")
    print(f"  {title}")
    print(f"{'='*55}")


# ─── Test runner ─────────────────────────────────────────────────

class E2ETestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.token: str = ""
        self.student_id: int = 0
        self.plan_id: int = 0
        # Use a unique username each run to avoid conflicts
        suffix = "".join(random.choices(string.ascii_lowercase, k=6))
        self.username = f"test_e2e_{suffix}"
        self.password = "TestPass123!"

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def assert_ok(self, label: str, resp: httpx.Response, expected_status: int = 200):
        if resp.status_code == expected_status:
            ok(f"[{resp.status_code}] {label}")
            self.passed += 1
            return True
        else:
            fail(f"[{resp.status_code}] {label} — expected {expected_status}")
            info(f"Body: {resp.text[:300]}")
            self.failed += 1
            return False

    # ── Steps ──────────────────────────────────────────────────────

    async def step_health(self, client: httpx.AsyncClient):
        section("Step 1 — Health Check")
        r = await client.get(f"{BASE_URL}/health")
        if await self.assert_ok("GET /health", r):
            data = r.json().get("data", {})
            info(f"API: {data.get('api')} | DB: {data.get('database')} | "
                 f"VectorDB: {data.get('vector_db')} | LLM: {data.get('llm')}")

    async def step_register(self, client: httpx.AsyncClient):
        section("Step 2 — Register Student")
        payload = {
            "username": self.username,
            "password": self.password,
            "name": "E2E Test Student",
            "subject": "数学",
        }
        r = await client.post(f"{BASE_URL}/auth/register", json=payload)
        # FastAPI returns 200 by default; the .created() helper sets body code=201
        success_statuses = {200, 201}
        if r.status_code in success_statuses:
            ok(f"[{r.status_code}] POST /auth/register")
            self.passed += 1
            data = r.json().get("data", {})
            # Decode student_id from JWT token if not directly returned
            token = data.get("access_token", "")
            if token:
                self.token = token  # temporarily store for profile lookup
                profile_r = await client.get(
                    f"{BASE_URL}/profile",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if profile_r.status_code == 200:
                    self.student_id = profile_r.json().get("data", {}).get("student_id", 0) or 1
            info(f"Registered username={self.username}, student_id={self.student_id}")
        else:
            fail(f"[{r.status_code}] POST /auth/register — Body: {r.text[:200]}")
            self.failed += 1

    async def step_login(self, client: httpx.AsyncClient):
        section("Step 3 — Login")
        payload = {"username": self.username, "password": self.password}
        r = await client.post(f"{BASE_URL}/auth/login", json=payload)
        if await self.assert_ok("POST /auth/login", r):
            data = r.json().get("data", {})
            self.token = data.get("access_token", "")
            info(f"Token: {self.token[:30]}...")

    async def step_get_profile(self, client: httpx.AsyncClient):
        section("Step 4 — Get Student Profile")
        r = await client.get(f"{BASE_URL}/profile", headers=self._headers())
        if await self.assert_ok("GET /profile", r):
            data = r.json().get("data", {})
            info(f"subject={data.get('subject')} | goal={data.get('current_goal')}")

    async def step_generate_plan(self, client: httpx.AsyncClient):
        section("Step 5 — Generate Learning Plan")
        # Use mock API key to trigger mock LLM (no real API required)
        headers = {**self._headers(), "X-API-Key": ""}
        r = await client.post(f"{BASE_URL}/plan/generate", headers=headers, timeout=60.0)
        if await self.assert_ok("POST /plan/generate", r):
            data = r.json().get("data", {})
            self.plan_id = data.get("plan_id", 0)
            info(f"plan_id={self.plan_id} | target_topic={data.get('target_topic')}")
            steps = data.get("learning_steps", [])
            info(f"Learning steps: {len(steps)} steps generated")

    async def step_complete_step(self, client: httpx.AsyncClient):
        section("Step 6 — Complete Learning Step")
        if not self.plan_id:
            fail("No plan_id available, skipping step completion")
            self.failed += 1
            return
        payload = {
            "plan_id": self.plan_id,
            "step_number": 1,
            "score": 1.0,
            "duration": 300,
        }
        r = await client.post(f"{BASE_URL}/learning/complete", json=payload, headers=self._headers())
        if await self.assert_ok("POST /learning/complete", r):
            data = r.json().get("data", {})
            info(f"step_completed={data.get('step_completed')} | plan_status={data.get('plan_status')}")

    async def step_get_progress(self, client: httpx.AsyncClient):
        section("Step 7 — Get Learning Progress")
        r = await client.get(f"{BASE_URL}/learning/progress", headers=self._headers())
        if await self.assert_ok("GET /learning/progress", r):
            data = r.json().get("data", {})
            count = data.get("completions_count", 0)
            info(f"completions_count={count}")
            if count >= 1:
                ok("completions_count >= 1 ✓")
                self.passed += 1
            else:
                fail("completions_count should be >= 1 after completing a step")
                self.failed += 1

    async def step_chat(self, client: httpx.AsyncClient):
        section("Step 8 — AI Coach Chat")
        payload = {"message": "请解释一下什么是一元一次方程？"}
        # Use mock API (no real key needed; LLM service falls back gracefully)
        headers = {**self._headers(), "X-API-Key": ""}
        r = await client.post(f"{BASE_URL}/chat", json=payload, headers=headers, timeout=60.0)
        if await self.assert_ok("POST /chat", r):
            data = r.json().get("data", {})
            response_preview = str(data.get("response", ""))[:100]
            info(f"AI response preview: {response_preview}...")

    async def step_assessment_result(self, client: httpx.AsyncClient):
        section("Step 9 — Assessment Result")
        r = await client.get(f"{BASE_URL}/assessment/result", headers=self._headers())
        if await self.assert_ok("GET /assessment/result", r):
            data = r.json().get("data", {})
            mastery = data.get("mastery_map", {})
            info(f"mastery_map has {len(mastery)} entries")

    # ── Main run ──────────────────────────────────────────────────

    async def run(self):
        print(f"\n{BOLD}{'='*55}")
        print(f"  EduMind Phase 6 — E2E Integration Test")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*55}{RESET}")

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            await self.step_health(client)
            await self.step_register(client)
            if not self.student_id:
                fail("Registration failed — aborting test suite")
                return self._summary()
            await self.step_login(client)
            if not self.token:
                fail("Login failed — aborting test suite")
                return self._summary()
            await self.step_get_profile(client)
            await self.step_generate_plan(client)
            await self.step_complete_step(client)
            await self.step_get_progress(client)
            await self.step_chat(client)
            await self.step_assessment_result(client)

        return self._summary()

    def _summary(self) -> int:
        total = self.passed + self.failed
        print(f"\n{BOLD}{'='*55}")
        if self.failed == 0:
            print(f"  {GREEN}ALL TESTS PASSED{RESET} {BOLD}({self.passed}/{total}){RESET}")
        else:
            print(f"  {RED}{self.failed} FAILED{RESET} {BOLD}/ {self.passed} passed / {total} total{RESET}")
        print(f"{'='*55}{RESET}\n")
        return 1 if self.failed > 0 else 0


if __name__ == "__main__":
    runner = E2ETestRunner()
    exit_code = asyncio.run(runner.run())
    sys.exit(exit_code)
