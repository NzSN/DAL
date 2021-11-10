import typing as typ


class OUT_OF_IDENT(Exception):

    def __init__(self, ident: str) -> None:
        self._ident = ident

    def __str__(self) -> str:
        return "IdentGenerator '" + self._ident + \
            "' is out of identifiers"


class IdentGenerator:

    def __init__(self, ident: str, prefix: str, max: int) -> None:
        self._ident = ident
        self._prefix = prefix
        self._current_idx = 0
        self._max = max

    def ident(self) -> str:
        return self._ident

    def gen(self) -> str:
        if self._current_idx > self._max:
            raise OUT_OF_IDENT(self._ident)

        ident = self._prefix + "_" + str(self._current_idx)
        self._current_idx += 1

        return ident

    def set_max(self, max: int) -> None:
        self._max = max
