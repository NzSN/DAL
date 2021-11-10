import typing as typ


class MACHINE_OPERATION_NOT_DEFINED(Exception):
    """
    The operation is not defined on target machine.
    """

    def __init__(self, machine: str, opName: str) -> None:
        self._machine = machine
        self._opName = opName

    def __str__(self) -> str:
        return "Operation " + self._opName + " is not define in machine " + \
            self._machine


class PROP_VAL_TYPE_ERROR(Exception):
    """
    Operation on property is not supported by the value type of
    property.
    """

    def __init__(self, propName: str, op: typ.Callable) -> None:
        self._propName = propName
        self._op = op

    def __str__(self) -> str:
        return self._propName + " does not support operation " \
            + self._op.__name__ + " ."


class OP_WITH_INVALID_ARGS(Exception):
    """
    ...
    """

    pass


class OP_SPEC_NOT_FOUND(Exception):
    """
    Operation's specification can not be found within
    a machine
    """

    def __init__(self, machine: str, op: str) -> None:
        self._machine = machine
        self._op = op

    def __str__(self) -> str:
        return self._op + " is not supported by machine " + self._machine


class DBOOL_IS_NOT_IN_VALID_FORM(Exception):
    """
    An DBool in invalid form is not comparable if do it
    then need to throw exception
    """

    def __str__(self) -> str:
        return "DBool in invalid form is not comparable"
