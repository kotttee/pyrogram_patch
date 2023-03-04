from dataclasses import dataclass


class State:
    def __init__(self, name: str, storage: "BaseStorage", key: str) -> None:
        self.name = name
        self.__storage = storage
        self.__key = key

    async def set_state(self, state) -> None:
        await self.__storage.set_state(state, self.__key)
        self.name = state

    async def set_data(self, data: dict) -> None:
        await self.__storage.set_data(data, self.__key)

    async def get_data(self) -> dict:
        return await self.__storage.get_data(self.__key)

    async def finish(self) -> None:
        await self.__storage.finish_state(self.__key)

    async def create_state(self, key: str) -> "State":
        return await self.__storage.checkup(key)

    def __repr__(self) -> str:
        return f"State(name - {self.name} | key - {self.__key})"

    @property
    def state(self) -> str:
        return self.name


class StateItem:
    def __get__(self, obj, cls):
        for name, obj in vars(cls).items():
            if obj is self:
                return "StatesGroup_" + cls.__name__ + "_State_" + name


@dataclass(init=False, frozen=True)
class StatesGroup:
    pass
