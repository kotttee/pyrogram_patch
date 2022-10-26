from typing import Any
from pyrogram import StopPropagation


# you can modify it
async def create_key(parsed_update) -> str:
    chat_id, user_id = 'unknown', 'unknown'
    if hasattr(parsed_update, 'from_user'):
        if parsed_update.from_user is not None:
            user_id = str(parsed_update.from_user.id)
    if hasattr(parsed_update, 'chat'):
        if parsed_update.chat is not None:
            chat_id = str(parsed_update.chat.id)
    return user_id + chat_id


class MiddlewareHelper:

    def __init__(self) -> None:
        self.__data = {}
        self.state = '*'

    async def insert_data(self, argument_name: str, value: Any) -> None:
        """use this method to pass data to handler or next middleware"""
        self.__data[argument_name] = value

    async def get_data(self, argument_name: str) -> Any:
        """use this method to get the data you saved earlier"""
        try:
            return self.__data[argument_name]
        except KeyError:
            raise RuntimeError(f"you are trying to get an argument {argument_name} by calling the get_data method but you haven't given it a value yet")

    async def skip_handler(self) -> None:
        """use this method to skip the handler"""
        raise StopPropagation('Please ignore this error')

    async def _get_data_for_handler(self, arguments) -> dict:
        """PLEASE DON'T USE THIS"""
        kwargs = {}
        if 'state' in arguments:
            kwargs['state'] = self.state

        if len(self.__data) > 0:
            for k, v in self.__data.items():
                if k in arguments:
                    kwargs[k] = v
        return kwargs

    async def _process_middleware(self, parsed_update, middleware):
        """PLEASE DON'T USE THIS"""
        return await middleware(parsed_update, self)

    async def _include_state(self, parsed_update, storage):
        """PLEASE DON'T USE THIS"""

        self.state = await storage.checkup(await create_key(parsed_update))
        parsed_update.middleware_patch_state = self.state
