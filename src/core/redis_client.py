#Imports
import redis.asyncio as redis
from src.core.config import settings
import json

class RedisClient:
    def __init__(self):
        self.client = None

    async def connect(self):
        self.client = await redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
        )

    async def disconnect(self):
        if self.client:
            await self.client.close()

    async def get(self, key: str):
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        else:
            return None

    async def set(self, key: str, value: dict, ttl: int = 300):
        pass

redis_client = RedisClient()