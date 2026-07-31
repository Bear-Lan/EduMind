import asyncio
from qdrant_client import AsyncQdrantClient

async def test():
    try:
        client = AsyncQdrantClient(path="D:/guo/研究生ai/EduMind/data/qdrant_db")
        print("Client initialized")
        res = await client.get_collections()
        print("Collections:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
