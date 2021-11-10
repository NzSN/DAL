import pytest
import astpretty
import typing as typ
import DevAuto as DA
import DevAuto.Core as core
from DevAuto.Core import DStr
import DevAuto.Translator.translator as trans
from DevAuto import DFunc
from DevAuto.lang_imp import InstGrp
from TestCases.CoreTestCases.devCore_Check import BoxMachine


boxOpSpec = [
    # is_open
    core.OpSpec("is_open", [], ("successed", core.DBool)),
    # op
    core.OpSpec("op", [("arg", core.DStr)], ("ret", core.DNone)),
    # query
    core.OpSpec("query", [("arg", core.DStr)], ("ret", core.DStr))
]


class BoxMachinePlus(BoxMachine, core.Dut):

    def __init__(self) -> None:
        BoxMachine.__init__(self)
        self._operations = self._operations + boxOpSpec
        self.value = 0

    @core.Machine.operation("is_open", boxOpSpec)
    def is_open(self) -> core.DBool:
        return self.operate(
            core.Operation(
                "core",
                "Box",
                core.opTuple("is_open", [])
            )
        )

    @core.Machine.operation("op", boxOpSpec)
    def op(self, arg: core.DStr) -> None:
        return self.operate(
            core.Operation(
                "core",
                "Box",
                core.opTuple("op", [arg])
            )
        )

    @core.Machine.operation("query", boxOpSpec)
    def query(self, arg: core.DStr) -> core.DStr:
        return self.operate(
            core.Operation(
                "core",
                "Box",
                core.opTuple("query", [arg])
            )
        )


###############################################################################
#                           Call Expressoin Fixtures                          #
###############################################################################
@DA.function(globals())
def CallExpression_Case_1() -> bool:
    box = BoxMachinePlus()
    box.op(box.query(DStr("things")))

    return True


@DA.function(globals())
def CallExpression_Case_2() -> bool:
    box = BoxMachinePlus()
    box.op(DStr("thing"))
    return True


@pytest.fixture
def CallExpression_Cases() -> typ.List[DFunc]:
    tests = [CallExpression_Case_1]
    return tests


###############################################################################
#                          Assign Statement Fixtures                          #
###############################################################################
@DA.function(globals())
def AssignStmts_Case_1() -> bool:
    box = BoxMachinePlus()
    info = box.query(DStr("things"))
    box.op(info)
    return True


@DA.function(globals())
def AssignStmts_Case_2() -> bool:
    box = BoxMachinePlus()
    info = 1
    return True


@DA.function(globals())
def AssignStmts_Case_3() -> bool:
    box = BoxMachinePlus()
    box.value = 1
    return True


@pytest.fixture
def AssignStmts_Cases() -> typ.List[DFunc]:
    return [AssignStmts_Case_1, AssignStmts_Case_2, AssignStmts_Case_3]


###############################################################################
#                          Binary Operation Fixtures                          #
###############################################################################
@DA.function(globals())
def BinEqual_Case_1() -> bool:
    box = BoxMachinePlus()
    box.query(DStr("A")) == box.query(DStr("B"))
    return True

@DA.function(globals())
def BinEqual_Case_2() -> bool:
    a = 1 == 2
    return True

@DA.function(globals())
def BinEqual_Case_3() -> bool:
    box = BoxMachinePlus()
    box.query(DStr("A")) == "A"

    return True


@pytest.fixture
def BinEqual_Cases() -> typ.List[DFunc]:
    return [BinEqual_Case_1, BinEqual_Case_2, BinEqual_Case_3]


###############################################################################
#                            If Statement Fixtures                            #
###############################################################################
@DA.function(globals())
def IfStmt_Case_1() -> bool:
    box = BoxMachinePlus()

    if box.query(DStr("ident")) == "Box":
        v = core.DInt(1)
    else:
        v = core.DInt(2)

    return True


@DA.function(globals())
def IfStmt_Case_2() -> bool:
    box = BoxMachinePlus()
    v = 1

    if box.query(DStr("ident")) == "Box":
        v = 2
    else:
        v = 3

    return True


@DA.function(globals())
def IfStmt_Case_3() -> bool:
    box = BoxMachinePlus()

    if box.query(DStr("ident")) == "Box":
        v = core.DInt(1)

    return True


@pytest.fixture
def IfStmts_Cases() -> typ.List[DFunc]:
    return [IfStmt_Case_1, IfStmt_Case_2, IfStmt_Case_3]



###############################################################################
#                                     Misc                                    #
###############################################################################
@pytest.fixture
def transFlags() -> trans.TransFlags:
    return trans.TransFlags()


@pytest.fixture
def Tr() -> trans.Translator:
    return trans.Translator()



###############################################################################
#                                  Test Cases                                 #
###############################################################################
class Tr_TC:

    def test_TransFlags(self, transFlags: trans.TransFlags) -> None:
        assert transFlags.get(transFlags.ARGUMENT_AWAIT) is False

    def test_TransFlags_Recursive(self, transFlags: trans.TransFlags) -> None:

        with transFlags.recursive():
            assert transFlags.is_recursive_inner() is False
            assert transFlags.get(transFlags.ARGUMENT_AWAIT) is False
            transFlags.setTrue(transFlags.ARGUMENT_AWAIT)
            assert transFlags.get(transFlags.ARGUMENT_AWAIT) is True

        assert transFlags.get(transFlags.ARGUMENT_AWAIT) is False

    def test_Call_Expression_Transform(self, Tr, CallExpression_Cases) -> None:
        instgrp = Tr.trans(CallExpression_Cases[0])  # type: InstGrp

        assert instgrp is not None

        # Verify that insts is successful generated
        # box = BoxMachinePlus()
        assert instgrp.duts() == ["Box"]

        insts = instgrp.insts()
        assert str(insts[0]) == "query [things] <__VAR__0>"
        assert str(insts[1]) == "op [<__VAR__0>] <__VAR__1>"

    def test_Assign_Stmt_Transform(self, Tr, AssignStmts_Cases) -> None:
        Case_1, Case_2, Case_3 = AssignStmts_Cases

        instgrp_1 = Tr.trans(Case_1)
        instgrp_2 = Tr.trans(Case_2)
        instgrp_3 = Tr.trans(Case_3)

        # Verify
        assert instgrp_1.duts() == ["Box"]
        assert [str(inst) for inst in instgrp_1.insts()] == [
            "query [things] <__VAR__0>",
            "op [<__VAR__0>] <__VAR__1>"
        ]

        assert instgrp_2.duts() == ["Box"]
        assert instgrp_2.insts() == []

        assert instgrp_3.duts() == ["Box"]
        assert instgrp_3.insts() == []

    def test_BinEqual_Expr_Case_1_Transform(self, Tr, BinEqual_Cases) -> None:
        Case_1 = BinEqual_Cases[0]

        insts = Tr.trans(Case_1)

        for inst in insts.insts():
            print(inst)

        # Verify
        assert(insts.duts() == ["Box"])
        assert [str(inst) for inst in insts.insts()] == [
            "query [A] <__VAR__0>",
            "query [B] <__VAR__1>",
            "equal [<__VAR__0> <__VAR__1>] <__VAR__2>"
        ]

    def test_BinEqual_Expr_Case_2_Transform(self, Tr, BinEqual_Cases) -> None:
        Case_2 = BinEqual_Cases[1]

        insts = Tr.trans(Case_2)

        # Verify
        assert [str(inst) for inst in insts.insts()] == []

    def test_BinEqual_Expr_Case_3_Transform(self, Tr, BinEqual_Cases) -> None:
        Case_3 = BinEqual_Cases[2]

        insts = Tr.trans(Case_3)

        # Verify
        assert(insts.duts() == ["Box"])
        assert [str(inst) for inst in insts.insts()] == [
            "query [A] <__VAR__0>",
            "equal [<__VAR__0> A] <__VAR__1>"
        ]

    def test_If_Stmt_Transform_Case_1(self, Tr, IfStmts_Cases) -> None:
        Case_1 = IfStmts_Cases[0]

        insts_1 = Tr.trans(Case_1)

        # Verify Case 1
        assert insts_1.duts() == ["Box"]
        assert [str(inst) for inst in insts_1.insts()] == [
            "query [ident] <__VAR__0>",
            "equal [<__VAR__0> Box] <__VAR__1>",
            "jmptrue <__VAR__1> 4",
            "def __VAR__2 2",
            "def __VAR__2 1"
        ]

    def test_If_Stmt_Transform_Case_2(self, Tr, IfStmts_Cases) -> None:
        Case_2 = IfStmts_Cases[1]

        insts_2 = Tr.trans(Case_2)

        for insts in insts_2.insts():
            print(insts)

        # Verify Case 2
        assert insts_2.duts() == ["Box"]
        assert [str(inst) for inst in insts_2.insts()] == [
            "query [ident] <__VAR__0>",
            "equal [<__VAR__0> Box] <__VAR__1>",
            # Cause v is not DA Object so there
            # is nothing need to be transformed into
            # Instructions.
        ]

    def test_If_Stmt_Transform_Case_3(self, Tr, IfStmts_Cases) -> None:
        Case_3 = IfStmts_Cases[2]

        insts_3 = Tr.trans(Case_3)

        for insts in insts_3.insts():
            print(insts)

        # Verify Case 3
        assert insts_3.duts() == ["Box"]
        assert [str(inst) for inst in insts_3.insts()] == [
            "query [ident] <__VAR__0>",
            "equal [<__VAR__0> Box] <__VAR__1>",
            "jmpfalse <__VAR__1> 4",
            "def __VAR__2 1"
        ]
