# TODO: Need to setup DType.TransformInfos during transforming.

import ast
import typing as typ
import DevAuto.Core as core
import DevAuto.lang_imp as dal
import DevAuto.transFlags as flags
from .trans_utilities import TransformInfos


class Snippet:

    def __init__(self, insts: typ.List[typ.Any] = None, value: typ.Any = None) -> None:

        if insts is None:
            self._insts = []
        else:
            self._insts = insts
        self.value = value

    def insts(self) -> typ.List[typ.Union[dal.Inst, str]]:
        return self._insts

    def addInst(self, inst: typ.Union[dal.Var, str]) -> None:
        self._insts.append(inst)

    def addInsts(self, insts: typ.List[dal.Inst]) -> None:
        for inst in insts:
            self._insts.append(inst)



###############################################################################
#                                  Modifiers                                  #
###############################################################################
def da_define(insts: dal.InstGrp, identifier: str, snippet: Snippet) -> Snippet:
    """
    Note: This modifier should be only used while Variable's value is
    unpredictable.

    For example:

    def f():
        if expr:
            v = da_unwrap(da_define("v", da_call_transform(DInt(1))))
        else:
            v = da_unwrap(da_define("v", da_call_transform(DInt(2))))

        f(v)

    v is unknowk until expr is evaluated, so need to bind DInt(1) and DInt(2)'s
    Def Inst to the same variable.
    """
    # To check that is variable is already defined
    da_var_ident = insts.get_da_var(identifier)
    if da_var_ident is None:
        da_var_ident = insts.new_da_var_ident()
        insts.add_var_map(identifier, da_var_ident)


    if len(snippet.insts()) != 0:
        # Make sure it's not a python value
        insts.addInst(dal.Def(
            da_var_ident,
            typ.cast(core.DType, snippet.value).value()))

    return snippet

def da_as_arg(insts: dal.InstGrp, snippet: Snippet, recur_count: int) -> Snippet:

    args_dict = insts.getFlag(insts.ARG_HOLDER)
    assert args_dict is not None

    if not recur_count in args_dict:
        args_dict[recur_count] = args = []
    else:
        args = args_dict[recur_count]

    for inst in snippet.insts():
        args.append(inst)

    return snippet


def da_test(insts: dal.InstGrp, snippet: Snippet) -> Snippet:

    vars = snippet.insts()

    if len(vars) == 1:
        insts.setFlagWith(insts.TEST_EXPR, vars[0])

    return snippet



def da_as_assign_value(insts: dal.InstGrp, snippet: Snippet) -> Snippet:

    v = snippet.insts()

    # Multiple assignment is not supported
    assert len(v) == 1

    insts.setFlagWith(insts.ASSIGN_VALUE, v[0])

    return snippet


def da_comparator(insts: dal.InstGrp, snippet: Snippet) -> Snippet:

    v = snippet.insts()

    # There should be only one comparator
    assert len(v) == 1

    if insts.getFlag(insts.COMPARETOR_LEFT) is None:
        insts.setFlagWith(insts.COMPARETOR_LEFT, v[0])
    else:
        insts.setFlagWith(insts.COMPARETOR_RIGHT, v[0])

    return snippet

def da_unwrap(o: typ.Any) -> typ.Any:

    if isinstance(o, Snippet):
        return o.value
    else:
        return o


###############################################################################
#                             Transform Functions                             #
###############################################################################
def da_constant_transform(insts: dal.InstGrp, const: core.DType) -> Snippet:
    snippet = Snippet(value=const)

    # To check that whether bind to a variable.
    if not const.transInfo is None:
        var_ident = const.transInfo.var_identifier()
        if not var_ident is None:
            snippet.addInst(dal.Var(var_ident, const.value()))
            return snippet

    snippet.addInst(const.value())

    return snippet


def da_transform_check(o: object) -> bool:

    # If the operation was already transformed
    if isinstance(o, core.DType):
        infos = o.transInfo

        if infos is None:
            # A DA Constant
            return True
        elif infos.is_transformed():
            return False

    return True


def da_name_transform(insts: dal.InstGrp, n: typ.Any) -> Snippet:
    s = Snippet(value=n)

    if not isinstance(n, core.DType):
        return s
    else:

        if n.compileInfo is None:
            return da_constant_transform(insts, n)

        ret = n.transInfo.op_ret()
        if ret is None:
            raise Exception("da_name_transform: ret not found")

        s.addInst(ret)

    return s


def da_machine_transform(insts: dal.InstGrp, m: core.Machine) -> core.Machine:
    """
    Generate requirements
    """
    if isinstance(m, core.Executors):
        insts.addExecutor(m.ident())
    elif isinstance(m, core.Dut):
        insts.addDut(m.ident())
    else:
        """
        A machine without extra identity
        """
        ...

    return m


###############################################################################
#                          Call Expression Transform                          #
###############################################################################
class DA_CALL_TRANSFORM_NO_ARGS_FOUND(Exception):

    def __str__(self) -> str:
        return "No argument found"


class DA_CALL_TRANSFORM_ARGS_MISMATCH(Exception):

    def __str__(self) -> str:
        return "argument mismatch"


def da_call_not_operation(insts: dal.InstGrp, o: typ.Any) \
    -> typ.Optional[Snippet]:

    snippet = Snippet(value=o)

    if isinstance(o, core.Machine):
        # Need to generate Dut, Executor description.
        # For example:
        #   box = BoxMachine()
        # It's a call but not an operation.
        da_machine_transform(insts, o)
        return snippet

    elif not isinstance(o, core.DType):
        # Value that is computable in python layer
        return snippet

    assert(isinstance(o, core.DType))

    op = o.compileInfo

    if op is None:
        # A DA Constant
        return da_constant_transform(insts, o)

    return None


def da_call_transform(insts: dal.InstGrp, o: typ.Any, recur_count: int) -> Snippet:


    snippet = da_call_not_operation(insts, o)
    if not snippet is None:
        return snippet

    transInfos = o.transInfo = TransformInfos()
    snippet = Snippet(value=o)

    assert(isinstance(o, core.DType))

    op = o.compileInfo

    assert(isinstance(transInfos, TransformInfos))
    assert(isinstance(op, core.Operation))

    opInfo = op.op()
    args = []
    argv = len(opInfo.opargs)

    # Get Arguments if need
    if argv > 0:
        args_dict = insts.getFlag(insts.ARG_HOLDER)
        assert args_dict is not None

        args = args_dict[recur_count]

        if args is None:
            raise DA_CALL_TRANSFORM_NO_ARGS_FOUND()
        if len(args) != argv:
            raise DA_CALL_TRANSFORM_ARGS_MISMATCH()

        del args_dict[recur_count]

    retVar = insts.compileDict[insts.VAR_ID_GEN].gen()
    var = dal.Var(retVar)

    op_inst = dal.Op(
        opInfo.opcode,
        core.DList(args),
        var
    )
    insts.addInst(op_inst)
    snippet.addInst(var)

    transInfos.set_op_ret(var)
    transInfos.transformed()

    return snippet


def da_oper_convert(insts: dal.InstGrp, val: core.DType) -> core.DType:
    op = val.compileInfo
    assert isinstance(op, core.Operation)

    opInfos = op.op()
    op_inst = dal.Op(
        opInfos.opcode,
        core.DList(opInfos.opargs),
        dal.Var(""))
    insts.addInst(op_inst)
    return val

# TODO: implement da_if_transform
def da_if_transform(insts: dal.InstGrp,
                    body: dal.InstGrp,
                    elseBody: dal.InstGrp) -> None:

    test_result = insts.getFlag(insts.TEST_EXPR)
    assert(isinstance(test_result, core.DBool) or
           isinstance(test_result, dal.Var))

    # Create Jmp instruction
    else_exists = len(elseBody) > 0
    body_exists = len(body) > 0

    if else_exists:
        next_inst_idx =  len(elseBody) + 1 + len(insts)

        jmp_inst = dal.JmpTrue(
            test_result, core.DInt(next_inst_idx))
    else:
        if body_exists:
            next_inst_idx = len(body) + 1 + len(insts)
            jmp_inst = dal.JmpFalse(
                test_result, core.DInt(next_inst_idx))
        else:
            return

    insts.addInst(jmp_inst)
    insts.addInsts(elseBody.insts())
    insts.addInsts(body.insts())


###############################################################################
#                            da_binOp_xxx_transform                           #
###############################################################################
type_map = {
    "str": core.DStr,
    "int": core.DInt
}  # type: typ.Dict[str, type]


def da_binOp_need_transformed(loperand: object,
                              roperand: object) -> bool:

    for operand in [loperand, roperand]:
        if isinstance(operand, core.DType) and \
           operand.compileInfo is not None:
            return True

    return False


def da_to_python_type(o: object) -> typ.Any:
    if isinstance(o, core.DType):
        return o.value()
    else:
        return o


def da_binOp_Eq_transform(
        insts: dal.InstGrp,
        loperand: object,
        roperand: object) -> Snippet:

    s = Snippet()

    if not da_binOp_need_transformed(loperand, roperand):
        s.value = loperand == roperand
        return s
    else:
        l = insts.getFlag(insts.COMPARETOR_LEFT)
        if l is None:
            l = da_to_python_type(loperand)
        r = insts.getFlag(insts.COMPARETOR_RIGHT)
        if r is None:
            r = da_to_python_type(roperand)

        insts.setFlagWith(insts.COMPARETOR_LEFT, None)
        insts.setFlagWith(insts.COMPARETOR_RIGHT, None)

        ident = insts.new_da_var_ident()
        var = dal.Var(ident)

        eq_inst = dal.Equal(l, r, var)
        insts.addInst(eq_inst)
        s.addInst(var)

        ret = core.DBool()
        ret.compileInfo = 1
        ret.transInfo = TransformInfos()
        ret.transInfo.set_op_ret = var

        s.value = ret

    return s
