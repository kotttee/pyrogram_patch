from json import dumps, loads
from typing import Any, Dict, Optional
from redis.asyncio.client import Redis
from redis.asyncio.connection import ConnectionPool
from pyrogram_patch.fsm.base_storage import BaseStorage
from pyrogram_patch.fsm.states import State


class RedisStorage(BaseStorage):
    def __init__(self, __storage: Redis) -> None:
        self.__storage = __storage

    @classmethod
    def from_url(
            cls, url: str, connection_kwargs: Optional[Dict[str, Any]] = None
    ) -> "RedisStorage":
        if connection_kwargs is None:
            connection_kwargs = {}
        pool = ConnectionPool.from_url(url, **connection_kwargs)
        redis = Redis(connection_pool=pool)
        return cls(__storage=redis)

    async def checkup(self, key) -> "State":
        if await self.__storage.exists(key):
            return State(await self.__storage.get(key), self, key)
        return State("*", self, key)

    async def set_state(self, state: str, key: str) -> None:
        if state is None:
            await self.__storage.delete(key)
        else:
            await self.__storage.set(
                key,
                state
            )

    async def set_data(self, data: dict, key: str) -> None:
        if not data:
            await self.__storage.delete(key)
            return
        await self.__storage.set(
            key,
            dumps(data)
        )

    async def get_data(self, key: str) -> dict:
        if key is None:
            return {}
        if isinstance(key, bytes):
            key = key.decode("utf-8")
        return loads(await self.__storage.get(key))

    async def finish_state(self, key: str) -> None:
        await self.__storage.delete(key)
