from pyrogram_patch.fsm.base_storage import BaseStorage
from pyrogram_patch.fsm.states import State


class MemoryStorage(BaseStorage):
    def __init__(self) -> None:
        self.__storage = {}
        self.__data_storage = {}

    async def checkup(self, key) -> "State":
        if key not in self.__storage.keys():
            return State("*", self, key)
        return State(self.__storage[key], self, key)

    async def set_state(self, state: str, key: str) -> None:
        self.__storage[key] = state

    async def set_data(self, data: dict, key: str) -> None:
        if key in self.__data_storage:
            self.__data_storage[key].update(data)
        else:
            self.__data_storage[key] = data

    async def get_data(self, key: str) -> dict:
        if key in self.__data_storage:
            return self.__data_storage[key]
        return {}

    async def finish_state(self, key: str) -> None:
        if key in self.__storage.keys():
            self.__storage.pop(key)
        if key in self.__data_storage.keys():
            self.__data_storage.pop(key)
