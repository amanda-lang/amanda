from __future__ import annotations
from amanda.compiler.tokens import Token, TokenType as TT
import amanda.compiler.type as types
from dataclasses import dataclass
from typing import (
    Any,
    List,
    Optional,
    Type as PyTy,
    TypeVar,
    Callable,
    Tuple,
    TYPE_CHECKING,
)
from typing_extensions import TypeGuard
from abc import abstractmethod

if TYPE_CHECKING:
    import amanda.compiler.symbols as symbols

# TODO: Rename fields of some classes
T = TypeVar("T")
ChildAttr = str | Tuple[str, int]


def node_of_type(node: ASTNode, ty: PyTy[T]) -> TypeGuard[T]:
    return isinstance(node, ty)


class ASTNode:
    def __init__(self, token: Token):
        self.token = token
        self.parent: Optional[ASTNode] = None
        self.lineno: int = token.line

    def for_each_child(self, f: Callable[[ASTNode, ChildAttr], None]):
        for attr in self.__dict__:
            if attr == "parent":
                continue
            maybe_node = getattr(self, attr, None)
            if isinstance(maybe_node, ASTNode):
                f(maybe_node, attr)
            elif isinstance(maybe_node, list):
                nodes = maybe_node
                for i, node in enumerate(nodes):
                    if not node_of_type(node, ASTNode):
                        continue
                    f(node, (attr, i))

    def _tag(self, node: ASTNode, _: str | Tuple[str, int]):
        node.parent = self
        node.tag_children()

    def tag_children(self):
        self.for_each_child(self._tag)

    def is_assignable(self):
        return False

    def child_of(self, ty: type) -> bool:
        assert self.parent, "parent should not be none"
        return isinstance(self.parent, ty)

    def of_type(self, ty: PyTy[T]) -> TypeGuard[T]:
        return isinstance(self, ty)


class Block(ASTNode):
    def __init__(self, children: list[ASTNode] | None = None):
        super().__init__(Token(TT.PROGRAM, "", 0, 0))
        self.children: List[ASTNode] = children if children else []
        self.symbols = None

    def add_child(self, node):
        self.children.append(node)


class Usa(ASTNode):
    def __init__(self, token, *, module="", alias=None):
        super().__init__(token)
        self.module = module
        self.alias = alias


class Program(Block):

    pass


class Expr(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.eval_type: types.Type = types.Type(types.Kind.TUNKNOWN)
        self.prom_type: types.Type | None = types.Type(types.Kind.TUNKNOWN)

    def __str__(self):
        return f"{self.token.lexeme}"


class Constant(Expr):
    def __init__(self, token):
        super().__init__(token)


class FmtStr(Expr):
    def __init__(self, token: Token, parts: list[Expr]):
        super().__init__(token)
        self.parts = parts


class Variable(Expr):
    def __init__(self, token):
        super().__init__(token)
        self.var_symbol: types.VariableSymbol = None  # type: ignore Symbol will contain extra info for python code gen phase

    def is_assignable(self):
        return True


class Converta(Expr):
    def __init__(self, token: Token, target: Expr, new_type: Type):
        super().__init__(token)
        self.target = target
        self.new_type = new_type


class Lista(Expr):
    def __init__(self, token, array_type, expression):
        super().__init__(token)
        self.array_type = array_type
        self.expression = expression


class Alvo(Expr):
    def __init__(self, token):
        super().__init__(token)
        self.var_symbol = None


class BinOp(Expr):
    def __init__(
        self, token, left=None, right=None, ty: types.Type | None = None
    ):
        super().__init__(token)
        self.right = right
        self.left = left
        if ty:
            self.eval_type = ty


class UnaryOp(Expr):
    def __init__(self, token, operand=None):
        super().__init__(token)
        self.operand = operand


class VarDecl(ASTNode):
    def __init__(
        self, token: Token, *, name: Token, var_type=None, assign=None
    ):
        super().__init__(token)
        self.var_type = var_type
        self.assign = assign
        self.name = name


class Assign(Expr):
    def __init__(self, token, left=None, right=None):
        super().__init__(token)
        self.left: Variable = left  # type: ignore
        self.right: Expr = right  # type: ignore


class Statement(ASTNode):
    def __init__(self, token: Token, exp: Expr | None = None):
        super().__init__(token)
        self.exp = exp


class LoopCtlStmt(Statement):
    pass


class Retorna(Statement):
    pass


class Mostra(Statement):
    pass


class Se(ASTNode):
    def __init__(
        self,
        token,
        condition,
        then_branch,
        *,
        elsif_branches=None,
        else_branch=None,
    ):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch
        self.elsif_branches = elsif_branches
        self.else_branch = else_branch


class SenaoSe(ASTNode):
    def __init__(self, token, condition, then_branch):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch


class Enquanto(ASTNode):
    def __init__(self, token, condition, statement):
        super().__init__(token)
        self.condition = condition
        # TODO: Rename this field to 'block'
        self.statement = statement


class CaseBlock(ASTNode):
    def __init__(self, token, expression, block):
        super().__init__(token)
        self.expression = expression
        self.block = block


class Escolha(ASTNode):
    def __init__(self, token, expression, cases, default_case):
        super().__init__(token)
        self.expression = expression
        self.cases = cases
        self.default_case = default_case


class Para(ASTNode):
    def __init__(self, token, expression=None, statement=None):
        super().__init__(token)
        self.expression = expression
        self.statement = statement


class ParaExpr(ASTNode):
    def __init__(self, name=None, range_expr=None):
        super().__init__(name)
        self.name = name
        self.range_expr = range_expr


class RangeExpr(ASTNode):
    def __init__(self, token, start=None, end=None, inc=None):
        super().__init__(token)
        self.start = start
        self.end = end
        self.inc = inc


class Call(Expr):
    def __init__(self, callee=None, paren=None, fargs: List[Expr] = []):
        super().__init__(callee.token)
        self.callee = callee
        self.fargs = fargs
        self.symbol: Any = None


class ListLiteral(Expr):
    def __init__(self, token, *, list_type=None, elements=None):
        super().__init__(token)
        self.list_type = list_type
        self.elements = elements


class NamedArg(Expr):
    def __init__(self, *, name: Token, arg: Expr):
        super().__init__(name)
        self.name = name
        self.arg = arg


class Get(Expr):
    def __init__(self, *, target: Expr, member: Token):
        super().__init__(member)
        self.target = target
        self.member = member

    def is_assignable(self):
        return True


class IndexGet(Expr):
    def __init__(self, token, target, index):
        super().__init__(token)
        self.target = target
        self.index = index

    def is_assignable(self):
        return True


class IndexSet(Expr):
    def __init__(self, token, index, value):
        super().__init__(token)
        self.index = index
        self.value = value

    def is_assignable(self):
        return True


class Set(Expr):
    def __init__(self, *, target: Get, expr: Expr):
        super().__init__(expr.token)
        self.target = target
        self.expr = expr


class FunctionDecl(ASTNode):
    def __init__(
        self,
        *,
        name: Token,
        params: list[Param],
        block: Block | None = None,
        func_type: Type | None,
    ):
        super().__init__(name)
        self.name: Token = name
        self.params = params
        self.func_type = func_type
        self.block = block
        self.is_native = False
        self.symbol: symbols.FunctionSymbol = None  # type: ignore (going to be set later)

    def is_method(self) -> bool:
        return False


class MethodDecl(FunctionDecl):
    def __init__(
        self,
        *,
        target_ty: Type,
        name: Token,
        block: Block,
        return_ty: Type,
        params: List[Param],
    ):
        super().__init__(
            name=name, block=block, func_type=return_ty, params=params
        )
        self.target_ty = target_ty
        self.return_ty = return_ty

    def is_method(self) -> bool:
        return True


class Registo(ASTNode):
    def __init__(self, *, name: Token, fields: List[VarDecl]):
        super().__init__(name)
        self.name = name
        self.fields = fields


class Param(ASTNode):
    def __init__(self, param_type=None, name=None):
        super().__init__(name)
        self.param_type = param_type
        self.name = name


class Type(ASTNode):
    def __init__(self, name: Token):
        super().__init__(name)
        self.name = name


class ArrayType(Type):
    element_type: Type

    def __init__(self, element_type: Type):
        super().__init__(element_type.name)
        self.element_type = element_type


class NoOp(ASTNode):
    def __init__(self):
        super().__init__(Token(TT.EOF, "", 0, 0))


# Base class for visitor objects
class Visitor:

    """Dispatcher method that chooses the correct
    return visiting method"""

    def visit(self, node, args=None):
        pass

    def general_visit(self, node):
        pass
