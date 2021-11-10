import ast
import typing as typ


def function_define_posonly(func: str, args: typ.List[str],
                    body: typ.List[ast.stmt]) -> ast.FunctionDef:
    f = typ.cast(ast.FunctionDef, parse_stmt(
        """
        def f():
            return
        """
    ))
    f.name = func
    f.args.args += [ast.arg(arg=arg, annotation=None, type_comment=None) for arg in args]
    f.body = body
    ast.fix_missing_locations(f)

    return f


def call(f: ast.expr, args: typ.List[ast.expr]) -> ast.Call:
    call_expr = typ.cast(ast.Call, parse_expr("f()"))
    call_expr.func = f
    call_expr.args = args

    ast.fix_missing_locations(call_expr)
    return call_expr


def parse_expr(expr: str) -> ast.expr:
    return ast.parse(expr).body[0].value  # type: ignore


def parse_stmt(stmt: str) -> ast.stmt:
    return ast.parse(stmt).body[0]
