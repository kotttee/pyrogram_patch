from abc import ABC, abstractmethod
from pyrogram_patch.fsm import State


class BaseStorage(ABC):

    @abstractmethod
    async def checkup(self, key) -> State:
        ...

    @abstractmethod
    async def set_state(self, state: str, key: str) -> None:
        ...

    @abstractmethod
    async def set_data(self, data: dict, key: str) -> None:
        ...

    @abstractmethod
    async def get_data(self, key: str) -> dict:
        ...

    @abstractmethod
    async def finish_state(self, key: str) -> None:
        ...
