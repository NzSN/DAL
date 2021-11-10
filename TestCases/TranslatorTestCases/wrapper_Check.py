import pytest
import ast
import astpretty
import DevAuto.Translator.ast_wrappers as wrapper


class Wrapper_TC:

    @pytest.mark.skip
    def test_Wrap_Expr_In_Func(self) -> None:
        node = ast.Constant(value=123, kind=None)
        ast.fix_missing_locations(node)

        node = wrapper.wrap_expr_in_func("TEST", ["A1", "*", "A2"], node)

        assert type(node) == ast.Call
        assert node.func.id == "TEST"
        assert node.args[0].id == "A1"
        assert node.args[1].value == 123
        assert node.args[2].id == "A2"
