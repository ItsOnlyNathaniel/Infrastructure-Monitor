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

redis_client = RedisClient()