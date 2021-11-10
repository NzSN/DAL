from types import MethodType
import typing as typ
import DevAuto.Core as core
from DevAuto.utility import *

T = typ.TypeVar("T")


class Var:

    def __init__(self, ident: str = "", value: typ.Any = None) -> None:
        """
        None means
        """
        self.ident = ident
        self.value = value

    def __str__(self) -> str:
        return "<" + self.ident + ">"

    def __eq__(self, o: 'Var') -> core.DBool:
        return core.DBool(self.ident == o.ident)


class Inst:

    def __init__(self, icode: str) -> None:
        self._inst_code = icode

    def code(self) -> str:
        return self._inst_code


class CInst(Inst):

    def __init__(self, icode: str) -> None:
        Inst.__init__(self, icode)


class OInst(Inst):

    def __init__(self, icode:str,
                 opcode: str,
                 args: core.DList[core.DStr],
                 ret: Var) -> None:

        Inst.__init__(self, icode)
        self._opcode = opcode
        self._args = args
        self._ret = ret

    def opcode(self) -> str:
        return self._opcode

    def args(self) -> core.DList:
        return self._args

    def ret(self) -> Var:
        return self._ret

    def __eq__(self, o: 'OInst') -> core.DBool:
        return core.DBool(self._opcode == o.opcode()) and \
            self._args == o.args() and \
            self._ret == o.ret()

    def __str__(self) -> str:
        return self._opcode + " [" +  \
            " ".join([str(arg) for arg in self._args]) + \
            "] " + str(self._ret)


class VInst(Inst):


    def __init__(self, icode:str, l: typ.Union[str, Var], r:typ.Union[str, Var]) -> None:
        Inst.__init__(self, icode)
        self._l = l
        self._r = r

    def loperand(self) -> typ.Union[str, Var] :
        return self._l

    def roperand(self) -> typ.Union[str, Var]:
        return self._r


class Term(Inst):

    def __init__(self, icode:str) -> None:
        Inst.__init__(self, icode)


class Success(Term):

    icode = "Success"

    def __init__(self) -> None:
        Term.__init__(self, self.icode)


class Fail(Term):

    icode = "fail"

    def __init__(self) -> None:
        Term.__init__(self, self.icode)


class Jmp(CInst):

    icode = "jmp"

    def __init__(self, to: core.DInt) -> None:
        CInst.__init__(self, self.icode)
        self._to = to

    def to(self) -> core.DInt:
        return self._to


class JmpTrue(CInst):

    icode = "jmptrue"

    def __init__(self,
                 test: typ.Union[core.DBool, Var],
                 idx: core.DInt) -> None:
        CInst.__init__(self, self.icode)
        self._test = test
        self._idx = idx

    def test(self) -> typ.Union[core.DBool, Var]:
        return self._test

    def goto_inst(self) -> core.DInt:
        return self._idx

    def __str__(self) -> str:
        return "jmptrue " + str(self._test) + " " + str(self._idx)


class JmpFalse(CInst):

    icode = "jmpfalse"

    def __init__(self, test: typ.Union[core.DBool, Var],
                 idx: core.DInt) -> None:
        CInst.__init__(self, self.icode)
        self._test = test
        self._idx = idx

    def test(self) -> typ.Union[core.DBool, Var]:
        return self._test

    def goto_inst(self) -> core.DInt:
        return self._idx

    def __str__(self) -> str:
        return "jmpfalse " + str(self._test) + " " + str(self._idx)


class Jmpeq(CInst):
    ...


class Op(OInst):

    icode = "op"

    def __init__(self, opcode: str, args: core.DList[core.DStr], ret: Var) -> None:
        OInst.__init__(self, self.icode, opcode, args, ret)
        self._src = ""
        self._dst = ""

    def src(self) -> str:
        return self._src

    def dst(self) -> str:
        return self._src

class Equal(VInst):

    icode = "equal"

    def __init__(self, l: typ.Union[str, Var], r: typ.Union[str, Var], ret: Var) -> None:
        VInst.__init__(self, self.icode, l, r)
        self._ret = ret

    def __str__(self) -> str:
        return "equal [" + str(self.loperand()) + \
            " " + str(self.roperand()) + "] " + str(self._ret)


class Def(VInst):

    icode = "def"

    def __init__(self, ident: str, value: core.DType) -> None:
        VInst.__init__(self, self.icode, "", "")
        self._ident = ident
        self._value = value

    def ident(self) -> str:
        return self._ident

    def value(self) -> core.DType:
        return self._value

    def __str__(self) -> str:
        return "def " + str(self._ident) + " " + str(self._value)


class Assign(VInst):

    icode = "assign"

    def __init__(self, ident: str, value: str) -> None:
        VInst.__init__(self, self.icode, "", "")
        self._ident = ident
        self._value = value

    def ident(self) -> str:
        return self._ident

    def value(self) -> str:
        return self._value

    def __str__(self) -> str:
        return "assign " + str(self._ident) + " " + str(self._value)

class InstGrp:
    """
    InstGrp is a list of Insts with extra informations that
    explain which executor and duts is need.
    """

    # Place to hold arguments of a call expression
    ARG_HOLDER = "AH"

    # Place to hold if stmt's test value
    TEST_EXPR  = "TE"

    # Variable identifier generator
    VAR_ID_GEN = "VIG"

    # Variable Map
    VAR_MAP = "VE"

    ASSIGN_VALUE = "AV"

    COMPARETOR_LEFT = "CL"

    COMPARETOR_RIGHT = "CR"

    def __init__(self, insts: typ.List[Inst],
                 duts: typ.List[str],
                 executors: typ.List[str]) -> None:

        self._insts = insts
        self._duts = duts
        self._executors = executors
        self.compileDict = {
            self.ARG_HOLDER: {},  # type: typ.Dict[int, typ.Any]
            self.TEST_EXPR: None,
            self.VAR_ID_GEN: IdentGenerator("VarGen", "__VAR_", 10000),
            self.VAR_MAP: {},  # type: typ.Dict[str, str]
            self.ASSIGN_VALUE: None,
            self.COMPARETOR_LEFT: None,
            self.COMPARETOR_RIGHT: None
        }

    def setFlagT(self, flag: str) -> None:
        self.compileDict[flag] = True

    def setFlagF(self, flag: str) -> None:
        self.compileDict[flag] = False

    def unsetFlag(self, flag: str) -> None:
        self.compileDict[flag] = None

    def getFlag(self, flag: str) -> typ.Optional[typ.Any]:
        if flag in self.compileDict:
            return self.compileDict[flag]
        else:
            return None

    def isFlagSetuped(self, flag: str) -> bool:
        return flag in self.compileDict and \
            self.compileDict[flag] != None

    def setFlagWith(self, flag: str, v: typ.Any) -> None:
        self.compileDict[flag] = v

    def insts(self) -> typ.List[Inst]:
        return self._insts

    def __len__(self) -> int:
        return len(self._insts)

    def __getitem__(self, index: int) -> typ.Optional[Inst]:
        return self._insts[index]

    def addInst(self, inst: Inst) -> None:
        self._insts.append(inst)

    def addInsts(self, insts: typ.List[Inst]) -> None:
        self._insts = self._insts + insts

    def duts(self) -> typ.List[str]:
        return self._duts

    def addDut(self, dut: str) -> None:
        self._duts.append(dut)

    def executors(self) -> typ.List[str]:
        return self._executors

    def addExecutor(self, executor: str) -> None:
        self._executors.append(executor)

    def new_da_var_ident(self) -> str:
        return self.compileDict[self.VAR_ID_GEN].gen()

    def get_da_var(self, ident: str) -> typ.Optional[str]:
        var_map = self.compileDict[self.VAR_MAP]
        if ident in var_map:
            return var_map[ident]
        else:
            return None

    def add_var_map(self, pyVar: str, daVar: str) -> None:
        var_map = self.compileDict[self.VAR_MAP]

        if pyVar in var_map:
            return
        else:
            var_map[pyVar] = daVar


class DFunc:
    """
    DevAuto Function
    """

    def __init__(self, func: typ.Callable, env: typ.Dict) -> None:
        self.__name__ = func.__name__
        self._func = func
        self.__IS_DA_FUNC__ = True
        self._env = env

    def body(self) -> typ.Callable:
        return self._func

    def env(self) -> typ.Dict:
        return self._env

    def __call__(self) -> 'DFunc':
        return self


class DIf:
    """
    IF statement of DevAuto.
    """

    def __init__(self, insts: InstGrp,
                 cond: typ.Union[core.DBool, bool]  ,
                 body: typ.Callable,
                 elseBody: typ.Callable) -> None:
        self._insts = insts
        self._cond = cond
        self._body = body
        self._elseBody = elseBody

    def cond(self) -> typ.Union[core.DBool, bool]:
        return self._cond

    def body(self) -> typ.Callable:
        return self._body

    def elseBody(self) -> typ.Callable:
        return self._elseBody

    def __call__(self, transFunc: typ.Callable[[InstGrp, 'DIf'], None]) -> None:
        if type(self._cond) == core.DBool:
            """
            Which unable to be evaluated in python layer.
            """
            transFunc(self._insts, self)
        else:
            if self._cond:
                self._body()
            elif self._elseBody is not None:
                self._elseBody()

class DWhile:
    """
    While statement of DevAuto
    """


class DFor:
    """
    For statement of DevAuto
    """


def function(env):
    """
    Decorator that mark a python function as a DA function.
    """
    def deco(f: typ.Callable) -> DFunc:
        return DFunc(f, env)

    return deco
