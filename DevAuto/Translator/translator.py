import re
import ast
from types import MethodType
import astor
import copy
import inspect
import astpretty
import typing as typ
import DevAuto.transFlags as flags
import DevAuto.Core as core
import DevAuto.lang_imp as dal
import DevAuto.Translator.ast_wrappers as ast_wrapper
import DevAuto.Translator.transform as trFuncs
from DevAuto.utility import *


class Translator:

    def preprocessing_before_transform(self, tree: ast.Module, info: typ.List) -> ast.AST:
        funcdef = tree.body[0]
        assert(isinstance(funcdef, ast.FunctionDef))

        # Remove decorator
        funcdef.decorator_list = []

        return tree

    def preprocessing_after_transform(self, tree: ast.Module, info: typ.List) -> ast.AST:

        funName = info[0]

        # Add Insts :: List[Inst] as an arg
        # Insts is used to hold all Insts that equal
        # to the dal.DFunc.
        funcdef = tree.body[0]
        assert(isinstance(funcdef, ast.FunctionDef))
        funcdef.args.args.append(ast.arg(arg="insts", annotation=None, type_comment=None))

        # Append a call expr
        # without this expr the pyfunc will not be executed
        # in exec()
        expr = ast.Expr(
            ast.Call(
                func = ast.Name(id=funName, ctx=ast.Load()),
                args = [ ast.Name(id='insts', ctx = ast.Load()) ],
                keywords = []))
        tree.body.append(expr)

        ast.fix_missing_locations(tree)

        return tree

    def environmentInit(self, func: dal.DFunc) -> typ.Dict:
        env = func.env()
        env["insts"] = dal.InstGrp([], [], [])
        env["DType"] = core.DType

        # Import Transform Functions into environment.
        funcs = [x for x in dir(trFuncs) if not re.match("da_", x) is None]
        for f in funcs:
            env[f] = getattr(trFuncs, f)

        return env

    def trans(self, func: dal.DFunc) -> dal.InstGrp:
        """
        Transform a dal.DFunc into list of Insts.
        """
        pyfunc = func.body()
        global_env = self.environmentInit(func)

        # Transform AST nodes
        ast_nodes = ast.parse(inspect.getsource(pyfunc))
        self.preprocessing_before_transform(ast_nodes, [pyfunc.__name__])

        DA_NodeTransformer(global_env).visit(ast_nodes)

        self.preprocessing_after_transform(ast_nodes, [pyfunc.__name__])

        # TODO: Remove ast tree print
        print("Transformed Source:\n\n")
        print(astor.to_source(ast_nodes))

        # Transform from ast to List[Inst]
        exec(compile(ast_nodes, "", 'exec'), global_env, {})

        return global_env["insts"]


class DA_NodeTransformer(ast.NodeTransformer):
    """
    Transform a dal.DFunc into intermidiate form which able
    to be execute by python interpreter to generate a list
    of DA instructions.
    """

    def __init__(self, env: typ.Dict) -> None:
        self._env = env
        self._precheck_transformer = DA_NodeTransPreCheck(env)
        self._trans_transformer = DA_NodeTransTransform(env)

    def visit(self, node: ast.AST) -> None:
        """
        Make transformations to dal.DFunc's ast nodes
        """

        # Make sure the ast is able to be transformed
        self._precheck_transformer.visit(node)

        # Do Transformation
        self._trans_transformer.visit(node)


class DA_NodeTransPreCheck(ast.NodeTransformer):
    """
    Do prechecking to ast nodes of dal.DFunc
    """

    def __init__(self, env: typ.Dict) -> None:
        ast.NodeTransformer.__init__(self)
        self._env = env


class TransFlags:

    ARGUMENT_AWAIT = "arg"
    IF_TEST_EXPR = "ITE"
    ASSIGNMENT_STMT = "AS"
    ASSIGN_RIGHT = "AR"
    DA_VAR_IDENTIFIER = "DVI"
    FORCE_DEFINE_VAR = "DV"
    COMPARE_SUB_EXPR = "CSE"

    def __init__(self) -> None:
        self._recursive_count = 0
        self._flagsDefault = {
            # Indicate that current expr is
            # argument of another expr
            self.ARGUMENT_AWAIT: False,
            self.IF_TEST_EXPR: None,
            self.ASSIGNMENT_STMT: False,
            self.ASSIGN_RIGHT: None,
            self.FORCE_DEFINE_VAR: False,
            self.DA_VAR_IDENTIFIER: None,
            self.COMPARE_SUB_EXPR: False,
        }  # type: typ.Dict[str, typ.Any]

        self._stack = [copy.deepcopy(self._flagsDefault)]

    def __enter__(self) -> None:
        self._recursive_in()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self._recursive_exit()

    def current(self) -> typ.Dict[str, typ.Any]:
        return self._stack[-1]

    def get(self, key: str) -> typ.Any:
        current = self.current()

        if key in current:
            return current[key]
        else:
            # TODO: Provide a more concrete exception
            raise Exception("Key not found")

    def set(self, key: str, value: typ.Any) -> None:
        self.current()[key] = value

    def unset(self, key: str) -> None:
        self.current()[key] = None

    def setTrue(self, key: str) -> None:
        self.current()[key] = True

    def setFalse(self, key: str) -> None:
        self.current()[key] = False

    def compare_sub_expr(self) -> None:
        self.setTrue(self.COMPARE_SUB_EXPR)

    def is_compare_sub_expr(self) -> bool:
        return self.get(self.COMPARE_SUB_EXPR) is True

    def recursive_count(self) -> int:
        return self._recursive_count

    def arg_await(self) -> None:
        """
        Set arg_await flag to let Transformer to
        provide subexpr's value to parent.
        """
        self.setTrue(self.ARGUMENT_AWAIT)

    def in_assign_proc(self) -> None:
        self.setTrue(self.ASSIGNMENT_STMT)

    def set_assign_value(self, v: typ.Any) -> None:
        self.set(self.ASSIGN_RIGHT, v)

    def assign_value(self) -> typ.Any:
        return self.get(self.ASSIGN_RIGHT)

    def if_test_proc(self) -> None:
        self.setTrue(self.IF_TEST_EXPR)

    def is_in_assign_proc(self) -> bool:
        return self.get(self.ASSIGNMENT_STMT) == True

    def is_arg_await(self) -> bool:
        return self.current()[self.ARGUMENT_AWAIT] == True

    def is_if_test(self) -> bool:
        return self.current()[self.IF_TEST_EXPR] == True

    def recursive(self) -> 'TransFlags':
        return self

    def _recursive_in(self) -> None:
        self._recursive_count += 1
        self._stack.append(copy.deepcopy(self._flagsDefault))

    def _recursive_exit(self) -> None:
        if len(self._stack) > 1:
            self._recursive_count -= 1
            self._stack.pop()
        else:
            return

    def is_recursive_inner(self) -> bool:
        return len(self._stack) == 0

    def force_define_var(self) -> None:
        self.setTrue(self.FORCE_DEFINE_VAR)

    def is_force_define_var(self) -> bool:
        return self.get(self.FORCE_DEFINE_VAR) is True

    def set_var_ident(self, ident: str) -> None:
        self.set(self.DA_VAR_IDENTIFIER, ident)

    def get_var_ident(self) -> str:
        identifier = self.get(self.DA_VAR_IDENTIFIER)
        if identifier is None:
            return "None"
        else:
            return identifier

class DA_NodeTransTransform(ast.NodeTransformer):
    """
    Do transfromations to ast nodes of dal.DFunc
    """

    def __init__(self, env: typ.Dict) -> None:
        ast.NodeTransformer.__init__(self)
        self._insts_ident = "insts"
        self._env = env
        self._func_ident_gen = IdentGenerator("funcGen", "_lambda", 10000)
        self._flags = TransFlags()

    def decorate(self, node: ast.AST) -> typ.Optional[ast.AST]:

        new = node

        if self._flags.is_arg_await():
            # New insts is as argument of another inst.
            new = ast_wrapper.call(
                ast.Name(id="da_as_arg", ctx=ast.Load()),
                [ast.Name(id=self._insts_ident, ctx=ast.Load()),
                 typ.cast(ast.expr, new),
                 ast.Constant(value=self._flags.recursive_count() - 1)])

        if self._flags.is_if_test():
            # New insts is as condition expression of
            # an Jmpxx inst.
            new = ast_wrapper.call(
                ast.Name(id="da_test", ctx=ast.Load()),
                [ast.Name(id=self._insts_ident, ctx=ast.Load()),
                 typ.cast(ast.expr, new)]
            )

        if self._flags.is_in_assign_proc():
            # Do nothing cause rvalue's info is
            # contained in TransformInfos. Just need
            # to unwrap value from Snippet.
            new = node

        if self._flags.is_force_define_var():
            new = ast_wrapper.call(
                ast.Name(id="da_define", ctx=ast.Load()),
                [ast.Name(id=self._insts_ident, ctx=ast.Load()),
                 ast.Constant(value=self._flags.get_var_ident(), ctx=ast.Load()),
                 typ.cast(ast.expr, new)]
            )

        if self._flags.is_compare_sub_expr():
            new = ast_wrapper.call(
                ast.Name(id="da_comparator", ctx=ast.Load()),
                [ast.Name(id=self._insts_ident, ctx=ast.Load()),
                 typ.cast(ast.expr, new)]
            )

        # Unwrap snippet to provide it's value to
        # another expression.
        new = ast_wrapper.call(
            ast.Name(id="da_unwrap", ctx=ast.Load()),
            [typ.cast(ast.expr, new)]
        )

        return new

    def visit_For(self, node):
        return node

    def visit_While(self, node):
        return node

    def visit_If(self, node: ast.If) -> typ.List[ast.stmt]:

        # Transform test expression
        with self._flags.recursive():
            self._flags.if_test_proc()
            test_expr = self.visit(node.test)

            # Python Variable may refer to different
            # DA Value in different condition so python
            # need to refer to DA Variable instead of DA Value.
            self._flags.force_define_var()

            self._insts_ident = "body_insts"
            bodyStmts = [self.visit(stmt) for stmt in node.body]

            self._insts_ident = "elseBody_insts"
            elseBodyStmts = [self.visit(stmt) for stmt in node.orelse]

        stmts = ast.parse("""
test_expr = 0
if isinstance(test_expr, DType):
    body_insts = InstGrp([], [], [])
    elseBody_insts = InstGrp([], [], [])

    body_insts.compileDict[insts.VAR_ID_GEN] = \
        insts.compileDict[insts.VAR_ID_GEN]
    elseBody_insts.compileDict[insts.VAR_ID_GEN] = \
        insts.compileDict[insts.VAR_ID_GEN]

    body_insts.compileDict[insts.VAR_MAP] = \
        insts.compileDict[insts.VAR_MAP]
    elseBody_insts.compileDict[insts.VAR_MAP] = \
        insts.compileDict[insts.VAR_MAP]

    # Transform Body Statements
    # Transform elseBody Statements

    da_if_transform(insts, body_insts, elseBody_insts)
else:
    if test_expr:
        ...
    else:
        ...
        """)

        stmts.body[0].value = test_expr  # type: ignore
        if_stmt = typ.cast(ast.If, stmts.body[1])
        # Setup test expression
        typ.cast(ast.Call ,if_stmt.test).args[0] = \
            ast.Name(id="test_expr", ctx=ast.Load())

        self._insts_ident = "insts"
        if_stmt.body = \
            if_stmt.body[0:6] + \
            bodyStmts + \
            elseBodyStmts + \
            [if_stmt.body[-1]]

        # TODO: Deal with Python If

        return stmts.body

    def visit_Name(self, node: ast.Name) -> ast.AST:
        call_expr = ast_wrapper.call(ast.Name(
            id="da_name_transform", ctx=ast.Load()),
                         [ast.Name(id=self._insts_ident, ctx=ast.Load()), node])
        decor_node = self.decorate(call_expr)
        if decor_node is None:
            # TODO: Should provide a more precise exception
            raise Exception("Failed to decorate a NamedExpr")
        self._env["da_name_transform"] = trFuncs.da_name_transform
        return decor_node

    def visit_Return(self, node):
        return node

    def visit_BinOp(self, node):
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        return node

    def visit_Compare(self, node: ast.Compare) -> typ.Any:

        ops = node.ops
        comparators = node.comparators

        # Only support one operator currently
        assert len(ops) == len(comparators) == 1

        op = ops[0]
        left = node.left
        comparator = comparators[0]

        # Get function to deal with the operation
        f_ident = "da_binOp_"+ type(op).__name__ + "_transform"

        if type(op).__name__ == "Is":
            return node

        # Transform left and comparator
        with self._flags.recursive():
            self._flags.compare_sub_expr()
            left_transed = self.visit(left)
            right_transed = self.visit(comparator)

        eq_expr = ast_wrapper.call(
            ast.Name(id=f_ident, ctx=ast.Load()),
            [ast.Name(id="insts", ctx=ast.Load()),
             left_transed, right_transed]
        )

        eq_expr = self.decorate(eq_expr)

        return eq_expr


    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        if self._flags.is_force_define_var():
            define_var = True
        else:
            define_var = False

        with self._flags.recursive():

            if define_var:
                # Need to associate right expr's value
                # to a DA-Variable if it's a DA-Value.
                self._flags.force_define_var()
                ident = astor.to_source(node.targets[0])
                ident = ident.replace('\n', '')
                self._flags.set_var_ident(ident)

            self._flags.in_assign_proc()
            node.value = self.visit(node.value)
        return node

    def visit_Call(self, node: ast.Call) -> ast.Call:

        args = []

        if len(node.args) > 0:

            # Transform every argument of this call
            # into intermidiate form
            with self._flags.recursive():
                self._flags.arg_await()
                args = [self.visit(arg) for arg in node.args]

            # Replace original arguments
            # with transformed arguments.
            node.args = args

        # To check that is any Operations is called
        # as arguments of this calling.
        transform_node = typ.cast(ast.Call, ast_wrapper.parse_expr(
            "da_call_transform(" + self._insts_ident + ")"))
        transform_node.args.append(node)
        transform_node.args.append(
            ast.Constant(value=self._flags.recursive_count()))

        decorated_node = self.decorate(transform_node)
        if decorated_node is None:
            # TODO: Should provide a more precise exception.
            raise Exception("Failed to decorate a call expression")

        self._env["da_call_transform"] = trFuncs.da_call_transform
        return typ.cast(ast.Call, decorated_node)
