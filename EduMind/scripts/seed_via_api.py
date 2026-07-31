"""
EduMind RAG Multi-Subject Seed via HTTP API
Seeds the running backend with textbook resources for Mathematics, English, Physics, Chemistry, and Computer Science.
"""
import asyncio
import httpx
import sys

BASE = "http://127.0.0.1:8000/api/v1"

MULTI_SUBJECT_DATA = [
    # Mathematics
    {
        "title": "什么是基础四则运算 (Basic Arithmetic)",
        "subject": "数学",
        "topic": "Basic Arithmetic",
        "content": "基础算术包含加法、减法、乘法与除法。运算时须遵守运算法则：先乘除后加减，括号优先。熟练掌握四则运算对于后续理解代数方程至关重要。",
        "source": "EduMind基础数学教辅 Vol.1",
    },
    {
        "title": "代数初步与未知数 (Introduction to Algebra)",
        "subject": "数学",
        "topic": "Introduction to Algebra",
        "content": "代数引入字母（如 x、y）代替未知数，用等式表示数量平衡关系。如 x+5=12，两边减5得 x=7。引入未知数帮助解决复杂数量问题。",
        "source": "EduMind代数学基础 Vol.1",
    },
    {
        "title": "一元一次方程求解 (Linear Equations)",
        "subject": "数学",
        "topic": "Linear Equations",
        "content": "一元一次方程形如 ax+b=c（a≠0）。求解步骤：1.移项，含未知数项移一边，常数移另一边；2.合并同类项；3.系数化1。例：2x+6=14→2x=8→x=4。",
        "source": "EduMind代数学基础 Vol.1",
    },

    # English
    {
        "title": "英语基础语法与词汇结构 (English Grammar Basics)",
        "subject": "英语",
        "topic": "英语基础",
        "content": "英语基础语法包含八大词性（名词、动词、形容词、副词、代词、介词、连词、感叹词）和五种简单句型结构 (S+V, S+V+O, S+V+P, S+V+IO+DO, S+V+O+C)。熟练掌握动词时态（一般现在时、一般过去时、现在进行时）是语言沟通与阅读理解的基石。",
        "source": "EduMind初中英语语法精解 Vol.1",
    },
    {
        "title": "英语进阶阅读与从句分析 (Advanced English Reading)",
        "subject": "英语",
        "topic": "英语进阶",
        "content": "英语进阶学习侧重从简单句向复合句过渡，涵盖定语从句 (Attributive Clauses)、状语从句 (Adverbial Clauses) 及宾语从句。通过分析文章主旨、推断上下文语境及积累高级词汇，能显著提升阅读理解与写作表达能力。",
        "source": "EduMind初中英语进阶阅读 Vol.1",
    },

    # Physics
    {
        "title": "物理力学与运动学基础 (Physics Mechanics)",
        "subject": "物理",
        "topic": "物理基础",
        "content": "物理力学研究物体的受力与运动状态。牛顿第一定律（惯性定律）指出，一切物体在没有受到外力作用时，总保持静止状态或匀速直线运动状态。重力公式 G = mg，压强公式 P = F/S 是解决力学问题的核心基石。",
        "source": "EduMind初中物理力学教辅 Vol.1",
    },
    {
        "title": "物理电学与欧姆定律 (Physics Electricity)",
        "subject": "物理",
        "topic": "物理进阶",
        "content": "电学研究电荷、电流、电压与电阻的关系。欧姆定律 (Ohm's Law) 表达式为 I = U / R。串联电路中总电阻等于各电阻之和，并联电路中总电阻倒数等于各电阻倒数之和。电功率公式 P = UI 用于计算用电器消耗电能的快慢。",
        "source": "EduMind初中物理电学教辅 Vol.1",
    },

    # Computer Science
    {
        "title": "计算机科学与编程算法基础 (CS & Algorithms)",
        "subject": "计算机科学",
        "topic": "计算机基础",
        "content": "计算机科学基础涵盖数据结构（数组、链表、栈、队列）与基本算法逻辑（顺序、分支、循环）。程序等于数据结构加算法。掌握变量命名、条件判断与循环迭代是运用代码解决实际问题的核心逻辑起点。",
        "source": "EduMind计算机科学入门 Vol.1",
    },
]

async def main():
    async with httpx.AsyncClient(timeout=30) as client:
        username = "seed_admin"
        password = "SeedPass999!"
        await client.post(f"{BASE}/auth/register", json={
            "username": username, "password": password, "name": "Seed Admin", "subject": "数学"
        })

        login = await client.post(f"{BASE}/auth/login", json={
            "username": username, "password": password
        })
        if login.status_code != 200:
            print(f"[FAIL] Login failed: {login.text}")
            sys.exit(1)

        token = login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[OK] Logged in as {username}")

        resp = await client.post(
            f"{BASE}/resources/seed",
            json=MULTI_SUBJECT_DATA,
            headers=headers,
        )
        if resp.status_code == 200:
            d = resp.json()["data"]
            print(f"[OK] Seeded {d['seeded']} resources, skipped {d['skipped']} duplicates")
        else:
            print(f"[FAIL] Seed failed ({resp.status_code}): {resp.text[:300]}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
