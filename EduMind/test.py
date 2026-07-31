import asyncio, sys, traceback
sys.path.insert(0, 'f:/研究生ai/EduMind/backend')
from database.connection import init_db, get_db_session
from application.orchestrator import orchestrator

async def test():
    await init_db()
    async for db in get_db_session():
        try:
            plan = await orchestrator.handle_learning_plan(db, student_id=2) # 1 is missing? Let's try 1
            print('Success:', plan)
        except Exception as e:
            traceback.print_exc()
        break

asyncio.run(test())
