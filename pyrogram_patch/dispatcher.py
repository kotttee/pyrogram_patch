import inspect
from contextlib import suppress
from typing import Union

import pyrogram
from pyrogram.dispatcher import Dispatcher, log
from pyrogram.handlers import RawUpdateHandler
from .patch_data_pool import PatchDataPool
from pyrogram_patch.fsm import BaseStorage
from pyrogram_patch.middlewares import PatchHelper


class PatchedDispatcher(Dispatcher):
    def __init__(self, client: pyrogram.Client):
        super().__init__(client)
        self.patch_data_pool = PatchDataPool

    async def handler_worker(self, lock):
        while True:
            packet = await self.updates_queue.get()

            if packet is None:
                break

            try:
                update, users, chats = packet
                parser = self.update_parsers.get(type(update), None)

                parsed_updates, handler_type = (
                    await parser(update, users, chats)
                    if parser is not None
                    else (None, type(None))
                )

                if parsed_updates is None:
                    continue

                patch_helper = PatchHelper()
                PatchDataPool.include_helper_to_pool(parsed_updates, patch_helper)

                if PatchDataPool.pyrogram_patch_fsm_storage:
                    await patch_helper._include_state(
                        parsed_updates, PatchDataPool.pyrogram_patch_fsm_storage, self.client
                    )

                # process outer middlewares
                for middleware in PatchDataPool.pyrogram_patch_outer_middlewares:
                    if middleware == handler_type:
                        await patch_helper._process_middleware(
                            parsed_updates, middleware, self.client
                        )

                async with lock:
                    for group in self.groups.values():
                        for handler in group:
                            args = None

                            if isinstance(handler, handler_type):
                                try:
                                    # filtering event
                                    if await handler.check(self.client, parsed_updates):
                                        # process middlewares
                                        for middleware in PatchDataPool.pyrogram_patch_middlewares:
                                            if middleware == type(handler):
                                                await patch_helper._process_middleware(
                                                    parsed_updates,
                                                    middleware,
                                                    self.client,
                                                )
                                        args = (parsed_updates,)
                                except Exception as e:
                                    log.exception(e)
                                    PatchDataPool.exclude_helper_from_pool(parsed_updates)
                                    continue

                            elif isinstance(handler, RawUpdateHandler):
                                try:
                                    # process middlewares
                                    for middleware in PatchDataPool.pyrogram_patch_middlewares:
                                        if middleware == type(handler):
                                            await patch_helper._process_middleware(
                                                    parsed_updates,
                                                    middleware,
                                                    self.client,
                                                )
                                    args = (update, users, chats)
                                except pyrogram.StopPropagation:
                                    PatchDataPool.exclude_helper_from_pool(parsed_updates)
                                    continue
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
                                    args = list(args)
                                    for v in kwargs.values():
                                        args.append(v)
                                    args = tuple(args)
                                    await self.loop.run_in_executor(
                                        self.client.executor,
                                        handler.callback,
                                        self.client,
                                        *args
                                    )
                            except pyrogram.StopPropagation:
                                raise
                            except pyrogram.ContinuePropagation:
                                continue
                            except Exception as e:
                                log.exception(e)
                            finally:
                                PatchDataPool.exclude_helper_from_pool(parsed_updates)
                            break
                    PatchDataPool.exclude_helper_from_pool(parsed_updates)
            except pyrogram.StopPropagation:
                pass
            except Exception as e:
                log.exception(e)
