from typing import NoReturn, Protocol
from amanda.compiler.ast import ASTNode
import amanda.compiler.ast as ast
from amanda.compiler.module import Module
from amanda.compiler.symbols.base import TypeVar
import amanda.compiler.symbols.core as symbols
from amanda.compiler.tokens import Token
from amanda.compiler.types.core import Registo


class Checker(Protocol):
    ctx_scope: symbols.Scope
    ctx_node: ASTNode
    global_scope: symbols.Scope
    ctx_reg: Registo
    ctx_module: Module
    scope_depth: int

    def get_generic_params(self, node: ASTNode) -> set[TypeVar]: ...
    def error(self, code, **kwargs) -> NoReturn: ...
    def error_with_loc(self, loc_tok: Token, code, **kwargs) -> NoReturn: ...
    def enter_ty_ctx(self, scope: symbols.Scope): ...
    def get_generic_ty_ctx(self, params: set[TypeVar]) -> symbols.Scope: ...
    def define_symbol(
        self, symbol: symbols.Symbol, depth: int, scope: symbols.Scope
    ): ...

    def enter_scope(self, scope: symbols.Scope | None = None): ...
    def leave_scope(self): ...

    def leave_ty_ctx(self): ...
    def get_type(self, type_node: ast.Type) -> symbols.Type: ...
    def types_match(
        self, expected: symbols.Type, received: symbols.Type
    ) -> bool: ...
    def visit(self, node: ast.ASTNode): ...
