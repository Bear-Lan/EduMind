"""
EduMind Database & Vector Store Rebuild Script

Clears all LearningResource rows and the Qdrant collection, then re-seeds
with the structured textbook data (chapter/section headings → multi-chunk).

Usage:
    cd EduMind/backend
    python -m scripts.rebuild_db
    # or: python scripts/rebuild_db.py

    Then start the backend and run:
    set ADMIN_PASSWORD=<password>
    python scripts/seed_via_api.py
"""
import asyncio
import sys
import shutil
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config.settings import settings
from models import Base
from models.resource import LearningResource
from models.quiz import QuizQuestion
from rag import rag_module


async def rebuild():
    print("=" * 60)
    print("EduMind Database & Vector Store Rebuild")
    print("=" * 60)

    # 1. Connect to SQLite database (settings.database_url is resolved by validator)
    db_url = settings.database_url
    print(f"[1/4] Connecting to database: {db_url}")
    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    db = session_factory()

    # 2. Clear LearningResource and QuizQuestion tables
    print("[2/4] Clearing LearningResource and QuizQuestion tables...")
    result1 = await db.execute(delete(LearningResource))
    result2 = await db.execute(delete(QuizQuestion))
    await db.commit()
    print(f"       Deleted {result1.rowcount} resources, {result2.rowcount} quiz questions")

    # 3. Clear Qdrant collection
    print("[3/4] Clearing Qdrant vector store...")
    if settings.qdrant_path and settings.qdrant_path != ":memory:":
        qdrant_path = Path(settings.qdrant_path)
        if qdrant_path.exists():
            print(f"       Removing Qdrant storage at {qdrant_path}")
            # Close any existing client
            if rag_module._client:
                await rag_module._client.close()
                rag_module._client = None
            shutil.rmtree(qdrant_path, ignore_errors=True)
            print("       Qdrant storage removed")
        else:
            print(f"       Qdrant path not found: {qdrant_path} (already clean)")
    else:
        # Server mode: delete collection via client
        try:
            client = rag_module.get_client()
            await client.delete_collection(settings.qdrant_collection_name)
            print(f"       Deleted Qdrant collection '{settings.qdrant_collection_name}'")
            await client.close()
            rag_module._client = None
        except Exception as e:
            print(f"       [WARN] Could not delete Qdrant collection: {e}")

    # 4. Done
    await db.close()
    await engine.dispose()
    print("[4/4] Rebuild complete!")
    print()
    print("Next steps:")
    print("  1. Start the backend:  cd backend && python main.py")
    print("  2. Run the seed script:")
    print("     set ADMIN_PASSWORD=<your_password>")
    print("     python scripts/seed_via_api.py")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(rebuild())
