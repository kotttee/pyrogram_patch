from pyrogram import Client, filters
from pyrogram.handlers import EditedMessageHandler, MessageHandler
from pyrogram.types import Message

from pyrogram_patch import patch
from pyrogram_patch.fsm import State, StateItem, StatesGroup
from pyrogram_patch.fsm.filter import StateFilter
from pyrogram_patch.fsm.storages import MemoryStorage
from pyrogram_patch.middlewares import PatchHelper
from pyrogram_patch.middlewares.middleware_types import (MixedMiddleware,
                                                         OnMessageMiddleware)
from pyrogram_patch.router import Router

SESSION_NAME = "bot"
API_ID = 8
API_HASH = "7245de8e747a0d6fbe11f7cc14fcc0bb"
BOT_TOKEN = ""

"""FSM"""


class Parameters(StatesGroup):
    weight = StateItem()
    height = StateItem()


"""MIDDLEWARES"""


class SkipDigitMiddleware(OnMessageMiddleware):
    def __init__(self) -> None:
        pass

    async def __call__(self, message: Message, client: Client, patch_helper: PatchHelper):
        is_digit = patch_helper.data["is_digit"]
        if not is_digit:
            if patch_helper.state.state == Parameters.height:
                return await patch_helper.skip_handler()


class CheckDigitMiddleware(MixedMiddleware):
    def __init__(self, handlers: tuple, some_var: bool) -> None:
        self.some_var = some_var  # it can be any value you want
        super().__init__(handlers)

    async def __call__(self, message: Message, client: Client, patch_helper: PatchHelper):
        if hasattr(message, "text"):
            patch_helper.data["is_digit"] = message.text.isdigit()


"""APP"""

app = Client(...)

router = Router()
router2 = Router()

patch_manager = patch(app)
patch_manager.set_storage(MemoryStorage())
patch_manager.include_outer_middleware(
    CheckDigitMiddleware((MessageHandler, ), False)
)
patch_manager.include_middleware(SkipDigitMiddleware())
patch_manager.include_router(router)
patch_manager.include_router(router2)


async def my_filter_function(_, __, update) -> bool:
    if hasattr(update, "text"):
        patch_helper = PatchHelper.get_from_pool(update)
        some_data = patch_helper.data["is_digit"]
        patch_helper.data["some_data_is_digit"] = some_data
        return True  # False
    return False


my_filter = filters.create(my_filter_function)


@router.on_message(filters.private & StateFilter() & my_filter)
async def process_1(client: Client, message, state: State, some_data_is_digit: bool):
    print(some_data_is_digit)
    if message.text == "register":
        await client.send_message(message.chat.id, "enter your weight")
        await state.set_state(Parameters.weight)


@router2.on_message(filters.private & StateFilter(Parameters.weight))
async def process_2(client: Client, message, state: State):
    await state.set_data({"weight": message.text})
    await client.send_message(message.chat.id, "enter your height")
    await state.set_state(Parameters.height)


@app.on_message(filters.private & StateFilter(Parameters.height))
async def process_3(client: Client, message, state: State):
    state_data = await state.get_data()
    weight = state_data["weight"]
    await client.send_message(
        message.chat.id, f"your height - {message.text} your weight - {weight}"
    )
    await state.finish()


app.run()
