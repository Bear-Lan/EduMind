import asyncio, sys, traceback
sys.path.insert(0, 'f:/ÑÐ¾¿Éúai/EduMind/backend')
from database.session import async_session_maker
from application.orchestrator import orchestrator

async def test():
    async with async_session_maker() as db:
        try:
            plan = await orchestrator.handle_learning_plan(db, student_id=1)
            print('Success:', plan)
        except Exception as e:
            traceback.print_exc()

asyncio.run(test())
