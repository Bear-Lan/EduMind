import asyncio
import httpx
import json

async def run_test():
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("Logging in...")
        login_res = await client.post(
            "http://127.0.0.1:8000/api/v1/auth/login",
            json={"username": "小明", "password": "password"} # Try a dummy password if we don't know it. Wait, login might fail if password is wrong. Let's just bypass auth in a different way if needed.
        )
        print("Login response:", login_res.status_code, login_res.text)

if __name__ == "__main__":
    asyncio.run(run_test())
