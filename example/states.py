from pyrogram_patch.fsm import StatesGroup, StateItem


class Parameters(StatesGroup):
    weight = StateItem()
    height = StateItem()
