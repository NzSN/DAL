import pytest
import DevAuto.Core as core
import typing as typ


###############################################################################
#                        Operation parameter TestCases                        #
###############################################################################
@pytest.fixture
def parameter_pair_diff() -> typ.Tuple[core.opParameter, core.opParameter]:
    return (
        [("P1", core.DInt), ("P2", core.DStr), ("P3", core.DList)],
        [("P1", core.DStr), ("P2", core.DInt), ("P3", core.DDict)]
    )


@pytest.fixture
def parameter_pair_diff_length() -> \
        typ.Tuple[core.opParameter, core.opParameter]:
    return (
        [("P1", core.DInt), ("P2", core.DStr), ("P3", core.DList)],
        [("P1", core.DInt), ("P2", core.DStr)]
    )


@pytest.fixture
def parameter_pair_equal() -> typ.Tuple[core.opParameter, core.opParameter]:
    return (
        [("P1", core.DInt), ("P2", core.DStr), ("P3", core.DList)],
        [("P1", core.DInt), ("P2", core.DStr), ("P3", core.DList)]
    )


@pytest.fixture
def parameter_pair_equal_name_diff() -> \
        typ.Tuple[core.opParameter, core.opParameter]:
    return (
        [("P0", core.DInt), ("P3", core.DStr), ("P4", core.DList)],
        [("P1", core.DInt), ("P2", core.DStr), ("P3", core.DList)]
    )


class OperationParameter_TC:

    def test_ParameterMatchDiff(self, parameter_pair_diff) -> None:
        p1, p2 = parameter_pair_diff
        assert core.paraMatch(p1, p2) is False

    def test_ParameterMatchEqual(self, parameter_pair_equal) -> None:
        p1, p2 = parameter_pair_equal
        assert core.paraMatch(p1, p2) is True

    def test_ParameterMatchDiffLength(
            self, parameter_pair_diff_length) -> None:
        p1, p2 = parameter_pair_diff_length
        assert core.paraMatch(p1, p2) is False

    def test_ParameterMatchEqualNameDiff(
            self, parameter_pair_equal_name_diff) -> None:
        p1, p2 = parameter_pair_equal_name_diff
        assert core.paraMatch(p1, p2) is True


@pytest.fixture
def arg_para_match() -> typ.Tuple[typ.List[core.DType], core.opParameter]:
    return (
        [core.DInt(0), core.DStr("Hello")],
        [("", core.DInt), ("", core.DStr)]
    )


@pytest.fixture
def arg_para_diff() -> typ.Tuple[typ.List[core.DType], core.opParameter]:
    return (
        [core.DStr("Hey"), core.DStr("Hello")],
        [("", core.DInt), ("", core.DStr)]
    )


@pytest.fixture
def arg_para_difflength() -> \
        typ.Tuple[typ.List[core.DType], core.opParameter]:
    return (
        [core.DInt(0)],
        [("", core.DInt), ("", core.DStr)]
    )


class OperationArgs_TC:

    def test_ArguMatchEqual(self, arg_para_match) -> None:
        args, paras = arg_para_match
        assert core.argsCheck(args, paras) is True

    def test_ArguMatchDiff(self, arg_para_diff) -> None:
        args, paras = arg_para_diff
        assert core.argsCheck(args, paras) is False

    def test_ArguMatchDiffLen(self, arg_para_difflength) -> None:
        args, paras = arg_para_difflength
        assert core.argsCheck(args, paras) is False


###############################################################################
#                             Core Types TestCases                            #
###############################################################################
@pytest.fixture
def DZero() -> core.DInt:
    return core.DInt(0)


class DInt_TC:

    def test_Plus(self, DZero) -> None:
        i1 = DZero
        i2 = i1 + 1
        assert type(i2).__name__ == "DInt"
        assert i2.value() == 1
        i3 = 1 + i1
        assert type(i3).__name__ == "DInt"
        assert i3.value() == 1

    def test_Mul(self, DZero) -> None:
        i1 = DZero
        assert i1 * 2 == 0
        assert 2 * i1 == 0

        i2 = i1 + 1
        assert i2 * 2 == 2
        assert 2 * i2 == 2

    def test_Eq(self, DZero) -> None:
        i1 = DZero
        assert i1 == i1
        assert i1 == 0
        assert i1 != 2
        assert 0 == i1


@pytest.fixture
def DListInstance() -> core.DList:
    return core.DList()


class DList_TC:

    def test_(self, DListInstance) -> None:
        l = DListInstance
