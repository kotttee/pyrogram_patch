from pyrogram import Client, filters
from pyrogram_patch import patch
from pyrogram_patch.middlewares.middleware_types import OnMessageMiddleware
from pyrogram_patch.middlewares import MiddlewareHelper
from pyrogram.types import Message
from pyrogram_patch.fsm import State, StateItem, StatesGroup, StateFilter
from pyrogram_patch.fsm.storages import MemoryStorage
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


class CheckDigitMiddleware(OnMessageMiddleware):

    def __init__(self) -> None:
        pass

    # you cannot change the call arguments
    async def __call__(self, message: Message, middleware_helper: MiddlewareHelper):
        return await middleware_helper.insert_data('is_digit', message.text.isdigit())


class CheckIgnoreMiddleware(OnMessageMiddleware):
    def __init__(self, ignore: bool) -> None:
        self.ignore = ignore  # it can be any value you want

    # you cannot change the call arguments
    async def __call__(self, message: Message, middleware_helper: MiddlewareHelper):
        if self.ignore:
            pass
        else:
            if middleware_helper.state.state == Parameters.weight or middleware_helper.state.state == Parameters.height:
                if not await middleware_helper.get_data('is_digit'):
                    return await middleware_helper.skip_handler()


"""APP"""

app = Client(...)
router = Router()
router2 = Router()

patched = patch(app)
patched.set_storage(MemoryStorage())
patched.include_outer_middleware(CheckDigitMiddleware())
patched.include_middleware(CheckIgnoreMiddleware(False))
patched.include_router(router)
patched.include_router(router2)


async def my_filter_function(_, __, query) -> bool:
    some_data = await query.middleware_helper.get_data('is_digit')
    await query.middleware_helper.insert_data('some_data_is_digit', some_data)
    return True  # False


my_filter = filters.create(my_filter_function)


@router.on_message(filters.private & StateFilter() & my_filter)
async def process_1(client: Client, message, state: State, some_data_is_digit: bool):
    print(some_data_is_digit)
    if message.text == 'register':
        await client.send_message(message.chat.id, 'enter your weight')
        await state.set_state(Parameters.weight)


@router2.on_message(filters.private & StateFilter(Parameters.weight))
async def process_2(client: Client, message, state: State):
    await state.set_data({'weight': message.text})
    await client.send_message(message.chat.id, 'enter your height')
    await state.set_state(Parameters.height)


@app.on_message(filters.private & StateFilter(Parameters.height))
async def process_3(client: Client, message, state: State):
    state_data = await state.get_data()
    weight = state_data['weight']
    await client.send_message(message.chat.id, f'your height - {message.text} your weight - {weight}')
    await state.finish()


app.run()
