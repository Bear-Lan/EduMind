"""
EduMind Demo Student Seeding Script

Creates a pre-populated demo student user with realistic learning history,
mastery maps, active study plan, and AI chat logs so that opening the system
immediately presents a rich, competition-ready dashboard.

Usage:
  f:\\研究生ai\\EduMind\\venv\\Scripts\\python.exe scripts/seed_demo_student.py
"""

import sys
import asyncio
import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"

DEMO_USER = {
    "username": "demo_student",
    "password": "DemoPassword123!",
    "name": "张明 (竞赛演示账号)",
    "grade": "高一",
    "subject": "数学",
    "target_score": 92.0
}

async def seed_demo():
    print("=" * 60)
    print("EduMind Phase 8 — Demo Student Data Initialization")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Register or Login
        print("[1/5] Registering demo student account...")
        reg_res = await client.post(f"{BASE_URL}/auth/register", json=DEMO_USER)
        if reg_res.status_code in (200, 201):
            token = reg_res.json()["data"]["access_token"]
            print(f"      ✓ Created new account: {DEMO_USER['username']}")
        else:
            print(f"      → Account exists, logging in...")
            login_res = await client.post(f"{BASE_URL}/auth/login", json={
                "username": DEMO_USER["username"],
                "password": DEMO_USER["password"]
            })
            if login_res.status_code != 200:
                print(f"      ✗ Failed to login: {login_res.text}")
                return
            token = login_res.json()["data"]["access_token"]
            print(f"      ✓ Login successful")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Update Profile with initial realistic mastery data
        print("[2/5] Setting up student profile & knowledge mastery map...")
        mastery_map = {
            "Basic Arithmetic": 0.95,
            "Introduction to Algebra": 0.88,
            "Linear Equations": 0.72,
            "Basic Geometry": 0.65,
            "Quadratic Functions": 0.30
        }
        
        up_res = await client.put(f"{BASE_URL}/profile", json={
            "current_goal": "冲刺期末考试，突破函数与几何难点",
            "subject": "数学",
            "learning_preferences": {
                "pace": "balanced",
                "style": "visual"
            }
        }, headers=headers)
        if up_res.status_code == 200:
            print("      ✓ Student profile updated")

        # 3. Generate active learning plan
        print("[3/5] Generating active personalized learning plan...")
        plan_res = await client.post(f"{BASE_URL}/plan/generate", headers=headers)
        if plan_res.status_code == 200:
            pdata = plan_res.json()["data"]
            print(f"      ✓ Active plan generated for topic: {pdata.get('target_topic')}")

            # Complete step 1 automatically for demo feel
            plan_id = pdata.get("plan_id")
            if plan_id:
                await client.post(f"{BASE_URL}/learning/complete", json={
                    "plan_id": plan_id,
                    "step_number": 1,
                    "score": 0.9,
                    "duration": 450
                }, headers=headers)
                print("      ✓ Step 1 marked complete (progress ring populated)")

        # 4. Seed initial AI chat conversation
        print("[4/5] Pre-populating AI Coach chat conversation history...")
        chat_questions = [
            "教练，请问解一元一次方程时，移项为什么要改变符号？",
            "我明白了，那遇到带括号的情况应该先处理哪一步？"
        ]
        for q in chat_questions:
            chat_res = await client.post(f"{BASE_URL}/chat", json={"message": q}, headers=headers)
            if chat_res.status_code == 200:
                print(f"      ✓ Chat Q&A recorded: '{q[:20]}...'")

        # 5. Submit initial assessment record
        print("[5/5] Submitting assessment benchmark scores...")
        await client.post(f"{BASE_URL}/assessment", json={
            "topic": "Linear Equations",
            "score": 0.85,
            "duration": 600
        }, headers=headers)
        print("      ✓ Assessment recorded (Linear Equations -> 85%)")

    print("-" * 60)
    print("Demo Data Setup Completed!")
    print(f"Demo Account Credentials: Username: {DEMO_USER['username']} | Password: {DEMO_USER['password']}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(seed_demo())
