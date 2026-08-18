"""
EduMind RAG Multi-Subject Seed via HTTP API
Seeds the running backend with textbook resources for Mathematics, English, Physics, Chemistry, and Computer Science.

Content includes chapter/section headings so the structure-aware chunker
can split documents into chunks carrying parent_doc / chapter / section metadata,
enabling citations that point back to the exact textbook location.

Usage:
    set ADMIN_PASSWORD=<your admin password>
    python scripts/seed_via_api.py
"""
import asyncio
import httpx
import sys

BASE = "http://127.0.0.1:8000/api/v1"

MULTI_SUBJECT_DATA = [
    # ── Mathematics ──────────────────────────────────────────────────────
    {
        "title": "初中数学教辅 · 代数与方程",
        "subject": "初中 数学",
        "topic": "Introduction to Algebra",
        "source": "EduMind初中数学教辅 Vol.1",
        "content": """# 第一章 代数初步

## 1.1 字母表示数

代数引入字母（如 x、y）代替未知数，用等式表示数量平衡关系。例如 x+5=12，两边减5得 x=7。引入未知数帮助解决复杂数量问题。

## 1.2 一元一次方程

一元一次方程形如 ax+b=c（a≠0）。求解步骤：1.移项，含未知数项移一边，常数移另一边；2.合并同类项；3.系数化1。

例：2x+6=14→2x=8→x=4。

# 第二章 二次方程

## 2.1 二次方程的求根公式

一元二次方程的求根公式是 x = (-b ± √(b²-4ac)) / 2a。判别式 Δ = b² - 4ac 决定根的个数：Δ>0 有两个不等实根，Δ=0 有两个相等实根，Δ<0 无实根。

## 2.2 韦达定理

韦达定理指出：对于方程 ax²+bx+c=0，两根之和 x₁+x₂ = -b/a，两根之积 x₁·x₂ = c/a。
""",
    },
    {
        "title": "初中数学教辅 · 几何基础",
        "subject": "初中 数学",
        "topic": "Basic Geometry",
        "source": "EduMind初中数学教辅 Vol.2",
        "content": """# 第一章 平面几何

## 1.1 点线面

点线面是几何的基本元素。角由两条射线从同一点出发组成。常见的角有锐角（小于90°）、直角（等于90°）、钝角（大于90°小于180°）。

## 1.2 三角形

三角形内角和等于180°。勾股定理：在直角三角形中，两直角边的平方和等于斜边的平方，即 a² + b² = c²。

# 第二章 圆

## 2.1 圆的性质

圆是到定点距离等于定长的所有点的集合。圆周角等于同弧所对圆心角的一半。圆的面积公式 S = πr²，周长公式 C = 2πr。
""",
    },
    # ── English ──────────────────────────────────────────────────────────
    {
        "title": "初中英语语法精解",
        "subject": "初中 英语",
        "topic": "英语基础",
        "source": "EduMind初中英语语法精解 Vol.1",
        "content": """# Chapter 1 词性与句型

## 1.1 八大词性

英语基础语法包含八大词性：名词 (Noun)、动词 (Verb)、形容词 (Adjective)、副词 (Adverb)、代词 (Pronoun)、介词 (Preposition)、连词 (Conjunction)、感叹词 (Interjection)。

## 1.2 五种基本句型

五种简单句型结构：S+V（主谓）、S+V+O（主谓宾）、S+V+P（主系表）、S+V+IO+DO（主谓双宾）、S+V+O+C（主谓宾补）。

# Chapter 2 动词时态

## 2.1 一般时态

一般现在时表示经常性动作，如 I study English every day。一般过去时表示过去发生的动作，如 I studied English yesterday。

## 2.2 进行时态

现在进行时表示正在发生的动作，如 I am studying English now。结构为 be + doing。
""",
    },
    # ── Physics ──────────────────────────────────────────────────────────
    {
        "title": "初中物理教辅 · 力学与电学",
        "subject": "初中 物理",
        "topic": "物理基础",
        "source": "EduMind初中物理教辅 Vol.1",
        "content": """# 第一章 力学

## 1.1 牛顿运动定律

牛顿第一定律（惯性定律）指出，一切物体在没有受到外力作用时，总保持静止状态或匀速直线运动状态。

牛顿第二定律：F = ma，加速度与合外力成正比，与质量成反比。

牛顿第三定律：作用力与反作用力大小相等、方向相反。

## 1.2 重力与压强

重力公式 G = mg，其中 g ≈ 9.8 N/kg。压强公式 P = F/S，表示单位面积上受到的压力。

# 第二章 电学

## 2.1 欧姆定律

欧姆定律 (Ohm's Law) 表达式为 I = U / R。串联电路中总电阻等于各电阻之和，并联电路中总电阻倒数等于各电阻倒数之和。

## 2.2 电功率

电功率公式 P = UI，用于计算用电器消耗电能的快慢。1度电 = 1 kW·h = 3.6×10⁶ J。
""",
    },
    # ── Computer Science ─────────────────────────────────────────────────
    {
        "title": "计算机科学入门 · 数据结构与算法",
        "subject": "大学 计算机科学",
        "topic": "计算机基础",
        "source": "EduMind计算机科学入门 Vol.1",
        "content": """# Chapter 1 数据结构

## 1.1 线性结构

数据结构是组织和存储数据的方式。常见的线性结构包括数组 (Array)、链表 (Linked List)、栈 (Stack) 和队列 (Queue)。数组支持随机访问，时间复杂度 O(1)；链表支持动态扩容，插入删除效率高。

## 1.2 树与图

树 (Tree) 是层次结构，二叉搜索树的查找时间复杂度为 O(log n)。图 (Graph) 由顶点和边组成，可用邻接矩阵或邻接表表示。

# Chapter 2 算法基础

## 2.1 排序算法

常见排序算法包括冒泡排序 (O(n²))、快速排序 (O(n log n)) 和归并排序 (O(n log n))。快速排序采用分治策略，选取基准元素将数组分为两部分。

## 2.2 时间复杂度

大O表示法描述算法最坏情况时间复杂度。O(1) < O(log n) < O(n) < O(n log n) < O(n²) < O(2ⁿ)。
""",
    },
]

async def main():
    async with httpx.AsyncClient(timeout=60) as client:
        # /resources/seed now requires admin authentication
        import os
        username = os.environ.get("ADMIN_USERNAME", "edumind_admin")
        password = os.environ.get("ADMIN_PASSWORD", "")
        if not password:
            print("[FAIL] Set ADMIN_PASSWORD env var (admin login password)")
            sys.exit(1)

        login = await client.post(f"{BASE}/admin/login", json={
            "username": username, "password": password
        })
        if login.status_code != 200:
            print(f"[FAIL] Admin login failed: {login.text}")
            sys.exit(1)

        token = login.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        print(f"[OK] Logged in as admin {username}")

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
