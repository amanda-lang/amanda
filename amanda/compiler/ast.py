from __future__ import annotations
import enum
from amanda.compiler.tokens import Token, TokenType as TT
import amanda.compiler.types.core as types
from amanda.compiler.types.builtins import Builtins
from dataclasses import dataclass
from typing import (
    Any,
    List,
    Optional,
    Sequence,
    Type as PyTy,
    TypeVar,
    Callable,
    Tuple,
    TYPE_CHECKING,
)
from typing_extensions import TypeGuard
from abc import abstractmethod
import amanda.compiler.symbols.core as symbols

# TODO: Rename fields of some classes
T = TypeVar("T")
ChildAttr = str | Tuple[str, int]


def node_of_type(node: ASTNode, ty: PyTy[T]) -> TypeGuard[T]:
    return isinstance(node, ty)


@dataclass
class Annotation:
    name: str
    attrs: dict[str, str]
    location_tok: Token


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
        super().__init__(Token(TT.PROGRAM, "", 1, 1))
        self.children: List[ASTNode] = children if children else []
        self.symbols = None

    def add_child(self, node):
        self.children.append(node)


@dataclass
class Module(Block):
    annotations: list[Annotation]

    def __init__(self, children: list[ASTNode] | None = None, annotations=None):
        super().__init__(children)
        self.annotations = annotations if annotations else []


class UsaMode(enum.Enum):
    Scoped = enum.auto()
    Item = enum.auto()
    Global = enum.auto()


class Usa(ASTNode):
    def __init__(
        self,
        token: Token,
        *,
        usa_mode: UsaMode,
        module: Token,
        alias: Token | None = None,
        items: list[str] | None = None,
    ):
        super().__init__(token)
        self.usa_mode = usa_mode
        self.module = module
        self.alias = alias
        self.items = items if items else []


class Expr(ASTNode):
    def __init__(self, token: Token):
        super().__init__(token)
        self.eval_type: types.Type = Builtins.Unknown
        self.prom_type: types.Type | None = Builtins.Unknown

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
        self, token, *, left: Expr, right: Expr, ty: types.Type | None = None
    ):
        super().__init__(token)
        self.right = right
        self.left = left
        self.eval_type = Builtins.Unknown
        if ty:
            self.eval_type = ty


class UnaryOp(Expr):
    def __init__(self, token: Token, *, operand: Expr):
        super().__init__(token)
        self.operand = operand


class VarDecl(ASTNode):
    def __init__(
        self, token: Token, *, name: Token, var_type=None, assign=None
    ):
        super().__init__(token)
        self.var_type: Type = var_type  # type: ignore
        self.assign: Assign | None = assign
        self.name: Token = name


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
    def __init__(self, token, expression: ParaExpr, statement: Block):
        super().__init__(token)
        self.expression = expression
        self.statement = statement


class ParaExpr(ASTNode):
    def __init__(self, name: Token, range_expr: RangeExpr):
        super().__init__(name)
        self.name = name
        self.range_expr = range_expr


class RangeExpr(ASTNode):
    def __init__(self, token: Token, start: Expr, end: Expr, inc: Expr):
        super().__init__(token)
        self.start = start
        self.end = end
        self.inc = inc


class Call(Expr):
    def __init__(
        self, *, callee: Expr, paren: Token | None = None, fargs: List[Expr]
    ):
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


class Unwrap(Expr):
    def __init__(self, *, option: Expr, default_val: Expr | None):
        super().__init__(option.token)
        self.option = option
        self.default_val = default_val


@dataclass
class Path(Expr):
    components: Sequence[Variable]

    def __init__(self, components: Sequence[Variable]):
        super().__init__(components[0].token)
        self.components = components


class FunctionDecl(ASTNode):
    def __init__(
        self,
        *,
        name: Token,
        params: list[Param],
        block: Block | None = None,
        annotations: list[Annotation],
        func_type: Type | None,
    ):
        super().__init__(name)
        self.name: Token = name
        self.params = params
        self.func_type = func_type
        self.block = block
        self.is_native = False
        self.annotations = annotations
        self.symbol: symbols.FunctionSymbol = None  # type: ignore

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
        annotations: list[Annotation],
        generic_params: list[GenericParam] | None,
    ):
        super().__init__(
            name=name,
            block=block,
            func_type=return_ty,
            params=params,
            annotations=list(),
        )
        self.annotations = annotations
        self.generic_params = generic_params
        self.target_ty = target_ty
        self.return_ty = return_ty

    def is_method(self) -> bool:
        return True


class Registo(ASTNode):
    def __init__(
        self,
        *,
        name: Token,
        fields: List[VarDecl],
        annotations: list[Annotation] | None = None,
        generic_params: list[GenericParam] | None,
    ):
        super().__init__(name)
        self.name = name
        self.fields = fields
        self.annotations = annotations
        self.generic_params = generic_params


@dataclass
class UniaoVariant(ASTNode):
    def __init__(self, name: Token, params: list[Type]):
        super().__init__(name)
        self.name = name
        self.params = params


@dataclass
class Uniao(ASTNode):
    def __init__(
        self,
        *,
        name: Token,
        variants: list[UniaoVariant],
        annotations: list[Annotation],
        generic_params: list[GenericParam],
    ):
        super().__init__(name)
        self.name = name
        self.variants = variants
        self.generic_params = generic_params
        self.annotations = annotations


class GenericParam(ASTNode):
    def __init__(
        self,
        name: Token,
    ):
        super().__init__(name)
        self.name = name


class GenericArg(ASTNode):
    def __init__(
        self,
        arg: Type,
    ):
        super().__init__(arg.token)
        self.arg = arg


class Param(ASTNode):
    def __init__(self, param_type: Type = None, name: Token = None):  # type: ignore
        super().__init__(name)
        self.param_type = param_type
        self.name = name


@dataclass
class Type(ASTNode):
    name: Token
    generic_args: list[GenericArg] | None
    maybe_ty: bool

    def __init__(self, name: Token, maybe_ty: bool, generic_args):
        super().__init__(name)
        self.name = name
        self.maybe_ty = maybe_ty
        self.generic_args = generic_args


@dataclass
class TypePath(Type):
    components: list[str]
    maybe_ty: bool
    generic_args: list[GenericArg] | None

    def __init__(
        self,
        tok: Token,
        components: list[str],
        maybe_ty: bool,
        generic_args: list[GenericArg] | None,
    ):
        super().__init__(tok, maybe_ty, generic_args)
        self.components = components
        self.maybe_ty = maybe_ty
        self.generic_args = generic_args


@dataclass
class ArrayType(Type):
    element_type: Type

    def __init__(self, element_type: Type, maybe_ty: bool):
        super().__init__(element_type.name, maybe_ty, None)
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
