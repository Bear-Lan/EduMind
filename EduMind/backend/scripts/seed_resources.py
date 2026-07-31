"""
EduMind Cold-Start Resource Ingestion Script

Seeds the database and vector indexes with initial mathematics textbook segments
to enable RAG and question answering.
"""

import sys
import asyncio
from pathlib import Path
from sqlalchemy import select

# Fix sys.path to allow running from any subdirectory
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from database.connection import get_db_session, init_db, close_db
from models.resource import LearningResource
from rag import rag_module



MATH_TEXTBOOK_DATA = [
    {
        "title": "什么是基础四则运算 (Basic Arithmetic)",
        "subject": "数学",
        "topic": "Basic Arithmetic",
        "content": "基础算术（Basic Arithmetic）是一切数学学习的基石，主要包含加法、减法、乘法与除法。运算时必须严格遵守运算法则：先乘除后加减，如果有括号则先计算括号内的内容。熟练掌握四则运算对于后续理解代数方程至关重要。",
        "source": "EduMind基础数学教辅 Vol. 1",
    },
    {
        "title": "代数初步与未知数 (Introduction to Algebra)",
        "subject": "数学",
        "topic": "Introduction to Algebra",
        "content": "代数（Algebra）引入了字母（如 x 和 y）来代替未知数。我们可以使用等式来表示数量之间的平衡关系。例如，在等式 x + 5 = 12 中，x 代表一个未知的数，通过在等式两边同时减去 5，我们可以解得 x = 7。引入未知数能够帮助我们解决日常生活中无法直接心算出来的复杂数量平衡问题。",
        "source": "EduMind代数学基础 Vol. 1",
    },
    {
        "title": "一元一次方程求解 (Linear Equations)",
        "subject": "数学",
        "topic": "Linear Equations",
        "content": "一元一次方程（Linear Equations in One Variable）是形如 ax + b = c (其中 a != 0) 的标准代数方程。求解一元一次方程的基本步骤是：1. 移项，将所有含有未知数的项移到等号一侧，常数项移到另一侧；2. 合并同类项，简化方程两边；3. 系数化为1，方程两边同时除以未知数的系数，从而得出未知数的值。例如解 2x + 6 = 14 时，移项得 2x = 8，除以 2 得 x = 4。",
        "source": "EduMind代数学基础 Vol. 1",
    },
    {
        "title": "几何基础与图形属性 (Basic Geometry)",
        "subject": "数学",
        "topic": "Basic Geometry",
        "content": "几何（Geometry）主要研究点、线、面以及各种几何图形（如三角形、长方形、圆）的属性和空间关系。三角形的内角和恒为 180 度；长方形的面积公式为长乘以宽；圆的周长公式为 2 * π * 半径，面积公式为 π * 半径的平方。掌握这些基本几何图形公式，是后续将几何问题代数化、并在直角坐标系中建立图形方程的前提。",
        "source": "EduMind几何学基础 Vol. 1",
    },
    {
        "title": "平面直角坐标系与解析几何 (Coordinate Geometry)",
        "subject": "数学",
        "topic": "Coordinate Geometry",
        "content": "解析几何/平面直角坐标系（Coordinate Geometry）通过建立平面直角坐标系，将几何图形在代数上用坐标和方程表示出来。平面上的任何点都可以用对实数表示。我们可以在坐标系中描绘出一条直线的方程 y = mx + b（其中 m 为斜率，b 为 y 轴截距），或者计算两点之间的距离。直角坐标系将几何直观与代数计算完美结合，是现代数学和工程的核心基础。",
        "source": "EduMind解析几何初步 Vol. 1",
    },
]


async def seed() -> None:
    print("=" * 60)
    print("EduMind Cold-Start Resource Seeder Ingestion")
    print("=" * 60)

    # Initialize database engine
    await init_db()

    count = 0
    try:
        # Create DB session context
        async for db in get_db_session():
            # Check if resources already seeded
            existing_res = await db.scalar(select(LearningResource.id).limit(1))
            if existing_res:
                print("Database already contains resource entries. Seeding skipped.")
                break

            for item in MATH_TEXTBOOK_DATA:
                print(f"Indexing textbook segment: '{item['title']}'...")
                await rag_module.upsert_resource(
                    db=db,
                    title=item["title"],
                    subject=item["subject"],
                    topic=item["topic"],
                    content=item["content"],
                    source=item["source"],
                )
                count += 1

            # Commit and write all changes to database
            await db.commit()
            break
    finally:
        # Close Qdrant client connection
        if rag_module._client:
            await rag_module._client.close()
            rag_module._client = None
            
        # Close database engine connection
        await close_db()

    print("-" * 60)
    print(f"Ingestion finished successfully. Seeded {count} items.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(seed())
