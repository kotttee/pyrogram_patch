import inspect
from pyrogram_patch.middlewares import MiddlewareHelper
import pyrogram
from pyrogram.dispatcher import Dispatcher
from pyrogram.dispatcher import log
from pyrogram.handlers import RawUpdateHandler

from pyrogram_patch.fsm import BaseStorage


class PatchedDispatcher(Dispatcher):

    def __init__(self, client: pyrogram.Client):
        super().__init__(client)
        self.pyrogram_patch_middlewares = []
        self.pyrogram_patch_outer_middlewares = []
        self.pyrogram_patch_fsm_storage: BaseStorage | None = None
        self.pyrogram_patch_allowed_update_types = [pyrogram.types.messages_and_media.message.Message]

    def pyrogram_patch_include_middleware(self, middleware: object) -> None:
        self.pyrogram_patch_middlewares.append(middleware)

    def pyrogram_patch_include_outer_middleware(self, middleware: object) -> None:
        self.pyrogram_patch_outer_middlewares.append(middleware)

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
                middleware_helper = MiddlewareHelper()
                if self.pyrogram_patch_fsm_storage:
                    if type(parsed_update) in self.pyrogram_patch_allowed_update_types:
                        await middleware_helper._include_state(parsed_update,
                                                               self.pyrogram_patch_fsm_storage)

                if len(self.pyrogram_patch_outer_middlewares) > 0:
                    for middleware in self.pyrogram_patch_outer_middlewares:
                        if middleware == handler_type:
                            await middleware_helper._process_middleware(parsed_update, middleware)
                async with lock:
                    for group in self.groups.values():
                        for handler in group:
                            args = None
                            if type(parsed_update) in self.pyrogram_patch_allowed_update_types:
                                parsed_update.middleware_helper = middleware_helper
                            if isinstance(handler, handler_type):
                                try:
                                    if await handler.check(self.client, parsed_update):
                                        if len(self.pyrogram_patch_middlewares) > 0:
                                            for middleware in self.pyrogram_patch_middlewares:
                                                if middleware == type(handler):
                                                    await middleware_helper._process_middleware(parsed_update,
                                                                                             middleware)
                                        args = (parsed_update, )
                                except pyrogram.StopPropagation:
                                    pass
                                except Exception as e:
                                    log.error(e, exc_info=True)
                                    continue

                            elif isinstance(handler, RawUpdateHandler):
                                try:
                                    if len(self.pyrogram_patch_middlewares) > 0:
                                        for middleware in self.pyrogram_patch_middlewares:
                                            if middleware == type(handler):
                                                await middleware_helper._process_middleware(parsed_update,
                                                                                            middleware)
                                    args = (update, users, chats)
                                except pyrogram.StopPropagation:
                                    pass
                            if args is None:
                                continue
                            try:
                                kwargs = await middleware_helper._get_data_for_handler(handler.callback.__code__.co_varnames)
                                if inspect.iscoroutinefunction(handler.callback):
                                    await handler.callback(self.client, *args, **kwargs)
                                else:
                                    await self.loop.run_in_executor(
                                        self.client.executor,
                                        handler.callback,
                                        self.client,
                                        *args, **kwargs
                                    )
                            except pyrogram.StopPropagation:
                                raise
                            except pyrogram.ContinuePropagation:
                                continue
                            except Exception as e:
                                log.error(e, exc_info=True)

                            break

            except pyrogram.StopPropagation:
                pass

            except Exception as e:
                log.error(e, exc_info=True)
