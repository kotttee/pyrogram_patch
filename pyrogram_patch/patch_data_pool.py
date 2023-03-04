from dataclasses import dataclass
from typing import Union
from pyrogram_patch.fsm import BaseStorage
from contextlib import suppress


@dataclass()
class PatchDataPool:
    update_pool: dict
    pyrogram_patch_middlewares: list
    pyrogram_patch_outer_middlewares: list
    pyrogram_patch_fsm_storage: Union[BaseStorage, None]

    @staticmethod
    def include_helper_to_pool(update, patch_helper) -> None:
        PatchDataPool.update_pool[id(update)] = patch_helper

    @staticmethod
    def exclude_helper_from_pool(update) -> None:
        with suppress(KeyError):
            PatchDataPool.update_pool.pop(id(update))

    @staticmethod
    def get_helper_from_pool(update) -> Union[object, None]:
        return PatchDataPool.update_pool[id(update)]


PatchDataPool.update_pool = {}
PatchDataPool.pyrogram_patch_middlewares = []
PatchDataPool.pyrogram_patch_outer_middlewares = []
PatchDataPool.pyrogram_patch_fsm_storage = None

