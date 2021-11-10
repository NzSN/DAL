# DevCore is collection of fundamental objects in DevAuto.
import typing as typ
import DevAuto.Core.devCoreExcep as dcexcep
from .devCoreTypes import opTuple, PropVal, opParameter, opRet, argsCheck

class DaObj(object):

    def __init__(self) -> None: ...


class DelayObj(DaObj):
    """
    Objects that unable to be computed in Python layer need to delay to DA
    layer.
    """

    def __init__(self) -> None: ...


class Message(DelayObj):
    """
    Communication unit between DaCore and Executors, Duts. All
    things between DACore and Executors, Duts are Messages.
    """

    def __init__(self, source: str, dest: str, content: str) -> None:
        self._source = source
        self._dest = dest
        self._content = content

    def source(self) -> str:
        return self._source

    def dest(self) -> str:
        return self._dest

    def content(self) -> str:
        return self._content


class Operation(Message):
    """
    Operation is a kind of message that order executors to do a specific
    action.

    Operation string format:
    opcode :: opargs :: ... (... means not not specified)
    """

    def __init__(self, source: str, dest: str,
                 op: opTuple) -> None:

        self._op = op

        # Build up operation content
        # First convert DStr to str
        opArgStr = [str(arg) for arg in op[1]]
        content = op[0] + "::" + "::".join(opArgStr)

        Message.__init__(self, source, dest, content)

    def op(self) -> opTuple:
        return self._op

    def __eq__(self, op: 'Operation') -> bool:
        return self._op == op.op()


class Config(Operation):
    """
    Config is a kind of Operation that use to config Executors, Duts, no
    infomations is return that cause by config except an acknowledge which
    indicate wheter target is config properly.

    With config indicater to indicate that the operation will change
    some properties of target.

    Operation string format:
    opcode :: opargs :: <config indicater>
    """

    config_indicater = "cfg"

    def __init__(self, source: str, dest: str,
                 op: opTuple) -> None:
        Operation.__init__(self, source, dest, op)

        # Append config indicater to tail of operation
        self._content = self._content + "::" + self.config_indicater


class Query(Operation):
    """
    Query is a kind of Operation that retrive informations from target,
    without properties, status changed to target.

    Like Config it need a query indicater.

    Operation string format:
    opcode :: opargs :: <query indicater>
    """

    query_indicater = "query"

    def __init__(self, source: str, dest: str,
                 op: opTuple) -> None:
        Operation.__init__(self, source, dest, op)

        # Append query indicater to tail of operation
        self._content = self._content + "::" + self.query_indicater


class Property:
    """
    Property is part of machine, it show that what feature a machine has,
    on python layer, it just an unique string within a machine.
    """

    def __init__(self, p: str, propval: PropVal) -> None:
        self._property = p
        self._propVal = propval

    def name(self) -> str:
        return self._property

    def __getitem__(self, key: typ.Union[int, str]) -> str:
        if self._propIndexArgCheck(key) is False:
            dcexcep.PROP_VAL_TYPE_ERROR(self._property, self.__getitem__)
        return self._propVal[key]  # type: ignore

    def __setitem__(self, key: typ.Union[int, str], value: str) -> None:
        if self._propIndexArgCheck(key) is False:
            dcexcep.PROP_VAL_TYPE_ERROR(self._property, self.__setitem__)
        self._propVal[key] = value  # type: ignore

    def __eq__(self, property: 'Property') -> bool:
        return (self._property, self._propVal) == \
            (property._property, property._propVal)

    def __str__(self) -> str:
        return self._property

    def _propIndexArgCheck(self, idxArg: typ.Union[str, int]) -> bool:
        typeOfProp = type(self._propVal).__name__
        indexType = type(idxArg).__name__

        if (typeOfProp == "dict" and indexType == "str") or \
           (typeOfProp == "list" and indexType == "int"):
            return True
        else:
            return False

class OpSpec:
    """
    An specification of operations.
    """

    def __init__(self, opcode: str,
                 para: opParameter, ret: opRet) -> None:
        self._opcode = opcode
        self._para = para
        self._ret = ret

    def __eq__(self, spec: 'OpSpec') -> bool:
        return (self._opcode, self._para, self._ret) == \
            (spec._opcode, spec._para, spec._ret)

    def opcode(self) -> str:
        return self._opcode

    def parameter(self) -> opParameter:
        return self._para

    def retVal(self) -> opRet:
        return self._ret


def opExists(opSpecs: typ.List[OpSpec], opcode: str) -> bool:
    exists = [spec.opcode() == opcode for spec in opSpecs] != []
    return exists


class Machine(DaObj):
    """
    An entity that able to perform operations and have
    some properties. To specify a more concrete machine by
    extend this class.
    """

    def __init__(self, ident: str, properties: typ.List[Property],
                 operations: typ.List[OpSpec]) -> None:
        self._ident = ident
        self._properties = properties
        self._operations = operations

    def ident(self) -> str:
        return self._ident

    def hasProperty(self, pident: str) -> bool:
        theProperty = [
            p for p in self._properties if p.name() == pident
        ]
        return theProperty != []

    def hasOperation(self, opcode: str) -> bool:
        theOp = [op.opcode()[0] == opcode for op in self._operations]
        return theOp != []

    def getOpSpec(self, opcode: str) -> typ.Optional[OpSpec]:
        spec = [s for s in self._operations if s.opcode() == opcode]
        if spec == []:
            return None
        else:
            # There must only one element with the opcode
            assert(len(spec) == 1)
            return spec[0]

    def operate(self, op: Operation) -> typ.Any:
        opcode = op.op().opcode
        spec = self.getOpSpec(opcode)

        if spec is None:
            raise dcexcep.OP_SPEC_NOT_FOUND(
                self._ident, op.op().opcode)

        # Operation arguments checking
        if argsCheck(op.op().opargs, spec.parameter()) is False:
            raise dcexcep.OP_WITH_INVALID_ARGS()

        retVal = spec.retVal()[1]()
        retVal.compileInfo = op
        return retVal

    @staticmethod
    def operation(ident: str, specs: typ.List[OpSpec]) -> typ.Callable:

        def spec_check(op: typ.Callable) -> typ.Callable:
            if not opExists(specs, op.__name__):
                # fixme: need to raise exception
                raise dcexcep.MACHINE_OPERATION_NOT_DEFINED(
                    ident, op.__name__)
            else:
                return op

        return spec_check


class Executors(Machine): ...


class Dut(Machine): ...
