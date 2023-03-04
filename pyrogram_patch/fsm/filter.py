from ..patch_helper import PatchHelper


class StateFilter:
    def __init__(self, state: str = "*") -> None:
        self.state = state
        self.__name__ = state + "_state_filter"

    def __call__(_, __, query) -> bool:
        try:
            return _.state == PatchHelper.get_from_pool(query).state.name
        except Exception:
            raise RuntimeError(
                'check storage'
            )