import typing as typ
from DevAuto.lang_imp import Var


class TransformInfos:

    def __init__(self) -> None:
        # Indicate that was a Machine Operation
        # already Transformed
        self._transformed = False  # type: bool

        # Place to hold Variable that hold an
        # Machine Operation's result.
        self._op_ret = None  # type: typ.Optional[Var]

        # Identifier of the DA Variable that
        # this value binded with.
        self._bind_to = None  # type: typ.Optional[str]

    def transformed(self) -> None:
        self._transformed = True

    def is_transformed(self) -> bool:
        return self._transformed is True

    def op_ret(self) -> typ.Union[None, Var]:
        return self._op_ret

    def set_op_ret(self, ret: Var) -> None:
        self._op_ret = ret

    def bind_to(self, ident: str) -> None:
        self._bind_to = ident

    def var_identifier(self) -> typ.Optional[str]:
        return self._bind_to
