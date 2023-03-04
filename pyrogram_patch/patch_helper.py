import inspect
from typing import Any, Union
from .patch_data_pool import PatchDataPool
from pyrogram import Client, StopPropagation
from pyrogram.handlers.handler import Handler


# you can modify it
async def create_key(parsed_update, client: Client) -> str:
    chat_id, user_id = "unknown", "unknown"
    if hasattr(parsed_update, "from_user"):
        if parsed_update.from_user is not None:
            user_id = str(parsed_update.from_user.id)
    if hasattr(parsed_update, "chat"):
        if parsed_update.chat is not None:
            chat_id = str(parsed_update.chat.id)
    elif hasattr(parsed_update, "message"):
        if hasattr(parsed_update.message, "chat"):
            if parsed_update.message.chat is not None:
                chat_id = str(parsed_update.message.chat.id)
    return str(client.me.id) + "-" + user_id + "-" + chat_id


class PatchHelper:
    def __init__(self) -> None:
        self.__data = {}
        self.state = "*"

    async def skip_handler(self) -> None:
        """use this method to skip the handler"""
        raise StopPropagation("please ignore this error, it is raised by the PatchHelper.skip_handler method in one of your middlewares")

    async def _get_data_for_handler(self, arguments) -> dict:
        """PLEASE DON'T USE THIS"""
        kwargs = {}
        if "state" in arguments:
            kwargs["state"] = self.state
        if "patch_helper" in arguments:
            kwargs["patch_helper"] = self

        if len(self.__data) > 0:
            for k, v in self.__data.items():
                if k in arguments:
                    kwargs[k] = v
        return kwargs

    async def _process_middleware(self, parsed_update, middleware, client):
        """PLEASE DON'T USE THIS"""
        return await middleware(parsed_update, client, self)

    async def _include_state(self, parsed_update, storage, client):
        """PLEASE DON'T USE THIS"""
        self.state = await storage.checkup(await create_key(parsed_update, client))

    @classmethod
    def get_from_pool(cls, update):
        helper = PatchDataPool.get_helper_from_pool(update)
        if helper is None:
            return cls()
        return helper

    @staticmethod
    def generate_state_key(client_id: int, user_id: Union[int, str] = "unknown", chat_id: Union[int, str] = "unknown") -> str:
        return str(client_id) + "-" + str(user_id) + "-" + str(chat_id)

    @property
    def data(self) -> dict:
        return self.__data

    def __repr__(self) -> str:
        return f"PatchHelper(state: {self.state} | data: {self.__data})"
