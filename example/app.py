from pyrogram import Client, filters
from pyrogram_patch import patch
from pyrogram_patch.fsm.storages import MemoryStorage
from pyrogram_patch.fsm import State, StateFilter
from excample.middlewares import CheckDigitMiddleware, CheckIgnoreMiddleware
from excample.states import Parameters

api_id = 11111
api_hash = 'hash'
app = Client("my_account", api_id=api_id, api_hash=api_hash)


patched = patch(app)
patched.set_storage(MemoryStorage())
patched.include_middleware(CheckDigitMiddleware())
patched.include_middleware(CheckIgnoreMiddleware(False))


@app.on_message(filters.private & StateFilter())
async def process_1(client: Client, message, state: State, is_digit: bool):
    print(is_digit)
    if message.text == 'register':
        await client.send_message(message.chat.id, 'enter your weight')
        await state.set_state(Parameters.weight)


@app.on_message(filters.private & StateFilter(Parameters.weight))
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