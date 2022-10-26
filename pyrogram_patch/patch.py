from .dispatcher import PatchedDispatcher
from pyrogram import Client
from pyrogram_patch.fsm import BaseStorage
from typing import Any

class PatchManager:
    def __init__(self, dispatcher: PatchedDispatcher, storage: BaseStorage | None = None):
        self.dispatcher = dispatcher

    def include_middleware(self, middleware: 'PatchMiddleware') -> None:
        self.dispatcher.pyrogram_patch_include_middleware(middleware)

    def include_outer_middleware(self, middleware: 'PatchMiddleware') -> None:
        self.dispatcher.pyrogram_patch_include_outer_middleware(middleware)

    def set_storage(self, storage: BaseStorage) -> None:
        self.dispatcher.pyrogram_patch_fsm_storage = storage


def patch(app: Client) -> PatchManager:
    """app - instance of your pyrogram client
       returns
       MiddlewarePatchManager instance with methods:
       include_middleware and include_outer_middleware
    """
    app.__delattr__("dispatcher")
    app.dispatcher = PatchedDispatcher(app)
    return PatchManager(app.dispatcher)


