import inspect
from typing import Any, Union

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

    async def insert_data(self, argument_name: str, value: Any) -> None:
        """use this method to pass data to handler or next middleware"""
        self.__data[argument_name] = value

    async def get_data(self, argument_name: str) -> Any:
        """use this method to get the data you saved earlier"""
        try:
            return self.__data[argument_name]
        except KeyError:
            raise RuntimeError(
                f"you are trying to get an argument {argument_name} by calling the get_data method but you haven't given it a value yet"
            )

    async def skip_handler(self) -> None:
        """use this method to skip the handler"""
        raise StopPropagation("Please ignore this error")

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
        parsed_update.middleware_patch_state = self.state

    @staticmethod
    def generate_state_key(client, user_id: Union[int, str] = "unknown", chat_id: Union[int, str] = "unknown") -> str:
        return str(client.me.id) + "-" + str(user_id) + "-" + str(chat_id)

