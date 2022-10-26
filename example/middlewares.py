from pyrogram_patch.middlewares.middleware_types import OnMessageMiddleware
from pyrogram_patch.middlewares import MiddlewareHelper
from pyrogram.types import Message
from states import Parameters


class CheckDigitMiddleware(OnMessageMiddleware):

    def __init__(self) -> None:
        pass

    # you cannot change the call arguments
    async def __call__(self, message: Message, middleware_helper: MiddlewareHelper):
        return await middleware_helper.insert_data('is_digit', message.text.isdigit())


class CheckIgnoreMiddleware(OnMessageMiddleware):
    def __init__(self, ignore: bool) -> None:
        self.ignore = ignore     # it can be any value you want


    # you cannot change the call arguments
    async def __call__(self, message: Message, middleware_helper: MiddlewareHelper):
        if self.ignore:
            pass
        else:
            if middleware_helper.state.state == Parameters.weight or middleware_helper.state.state == Parameters.height:
                if not await middleware_helper.get_data('is_digit'):
                    return await middleware_helper.skip_handler()
