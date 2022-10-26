
class StateFilter:
    def __init__(self, state:str = '*') -> None:
        self.state = state
        self.__name__ = state + '_state_filter'

    def __call__(_, __, query) -> bool:
        try:
            return _.state == query.middleware_patch_state.state
        except Exception:
            raise RuntimeError('you can use this filter only for message handler  - "on_message"')
