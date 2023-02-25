from pyrogram import Client

from .patched_decorators import PatchedDecorators


class Router(PatchedDecorators):
    def __init__(self) -> None:
        self._app = None
        self._decorators_storage: list = []

    def set_client(self, client: Client) -> None:
        self._app = client
        for decorator in self._decorators_storage:
            self._app.add_handler(
                    *decorator
            )