from pyrogram import Client
from .patched_decorators import PatchedDecorators


class Router(PatchedDecorators):

    def __init__(self) -> None:
        self._app = None

    def set_client(self, client: Client) -> None:
        self._app = client
