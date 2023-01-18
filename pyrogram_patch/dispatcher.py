import inspect
from contextlib import suppress
from typing import Union

import pyrogram
from pyrogram.dispatcher import Dispatcher, log
from pyrogram.handlers import RawUpdateHandler

from pyrogram_patch.fsm import BaseStorage
from pyrogram_patch.middlewares import PatchHelper


class PatchedDispatcher(Dispatcher):
    def __init__(self, client: pyrogram.Client):
        super().__init__(client)
        self.pyrogram_patch_middlewares = []
        self.pyrogram_patch_outer_middlewares = []
        self.pyrogram_patch_fsm_storage: Union[BaseStorage, None] = None
        self.pyrogram_patch_allowed_update_types = [
            pyrogram.types.messages_and_media.message.Message,
            pyrogram.types.CallbackQuery,
        ]

    def pyrogram_patch_include_middleware(self, middleware: object) -> None:
        self.pyrogram_patch_middlewares.append(middleware)

    def pyrogram_patch_include_outer_middleware(self, middleware: object) -> None:
        self.pyrogram_patch_outer_middlewares.append(middleware)

    def manage_allowed_update_types(self, pyrogram_types, include: bool = True) -> None:
        if include:
            self.pyrogram_patch_allowed_update_types.append(pyrogram_types)
        else:
            with suppress(ValueError):
                self.pyrogram_patch_allowed_update_types.remove(pyrogram_types)

    async def handler_worker(self, lock):
        while True:
            packet = await self.updates_queue.get()

            if packet is None:
                break

            try:
                update, users, chats = packet
                parser = self.update_parsers.get(type(update), None)

                parsed_update, handler_type = (
                    await parser(update, users, chats)
                    if parser is not None
                    else (None, type(None))
                )

                # include state

                patch_helper = PatchHelper()
                if parsed_update is not None:
                    parsed_update.patch_helper = patch_helper
                if self.pyrogram_patch_fsm_storage:
                    if type(parsed_update) in self.pyrogram_patch_allowed_update_types:
                        await patch_helper._include_state(
                            parsed_update, self.pyrogram_patch_fsm_storage, self.client
                        )

                # process outer middlewares
                if len(self.pyrogram_patch_outer_middlewares) > 0:
                    for middleware in self.pyrogram_patch_outer_middlewares:
                        if middleware == handler_type:
                            await patch_helper._process_middleware(
                                parsed_update, middleware, self.client
                            )

                async with lock:
                    for group in self.groups.values():
                        for handler in group:
                            args = None

                            if isinstance(handler, handler_type):
                                try:
                                    # filtering event
                                    if await handler.check(self.client, parsed_update):
                                        # process middlewares
                                        if len(self.pyrogram_patch_middlewares) > 0:
                                            for (
                                                middleware
                                            ) in self.pyrogram_patch_middlewares:
                                                if middleware == type(handler):
                                                    await patch_helper._process_middleware(
                                                        parsed_update,
                                                        middleware,
                                                        self.client,
                                                    )
                                        args = (parsed_update,)
                                except Exception as e:
                                    log.exception(e)
                                    continue

                            elif isinstance(handler, RawUpdateHandler):
                                try:
                                    # process middlewares
                                    if len(self.pyrogram_patch_middlewares) > 0:
                                        for (
                                            middleware
                                        ) in self.pyrogram_patch_middlewares:
                                            if middleware == type(handler):
                                                await patch_helper._process_middleware(
                                                    parsed_update,
                                                    middleware,
                                                    self.client,
                                                )
                                    args = (update, users, chats)
                                except pyrogram.StopPropagation:
                                    pass
                            if args is None:
                                continue

                            try:
                                # formation kwargs
                                kwargs = await patch_helper._get_data_for_handler(
                                    handler.callback.__code__.co_varnames
                                )
                                if inspect.iscoroutinefunction(handler.callback):
                                    await handler.callback(self.client, *args, **kwargs)
                                else:
                                    await self.loop.run_in_executor(
                                        self.client.executor,
                                        handler.callback,
                                        self.client,
                                        *args,
                                        **kwargs
                                    )
                            except pyrogram.StopPropagation:
                                raise
                            except pyrogram.ContinuePropagation:
                                continue
                            except Exception as e:
                                log.exception(e)

                            break
            except pyrogram.StopPropagation:
                pass
            except Exception as e:
                log.exception(e)
