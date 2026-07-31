import asyncio
from qdrant_client import AsyncQdrantClient

async def test():
    try:
        client = AsyncQdrantClient(location=":memory:")
        print("Client initialized")
        res = await client.get_collections()
        print("Collections:", res)
    except Exception as e:
        print("Error:", e)

asyncio.run(test())
