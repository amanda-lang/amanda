from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, TYPE_CHECKING
from .symbols import Symbol


class VariableSymbol(Symbol):
    def __init__(self, name: str, var_type: Type):
        super().__init__(name)
        self.type = var_type

    def can_evaluate(self):
        return True


class FunctionSymbol(Symbol):
    def __init__(
        self,
        name: str,
        func_type: Type,
        params: dict[str, VariableSymbol] = {},
        entrypoint=False,
    ):
        super().__init__(name)
        self.params = params  # dict of symbols
        self.scope = None
        self.entrypoint = entrypoint

    def __str__(self):
        params = ",".join(self.params)
        return (
            f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"
        )

    def is_callable(self):
        return True

    def arity(self):
        return len(self.params)


class MethodSym(FunctionSymbol):
    def __init__(
        self,
        name: str,
        target_ty: Type,
        return_ty: Type,
        params: dict[str, VariableSymbol] = {},
    ):
        super().__init__(name, return_ty, params=params)
        self.target_ty = target_ty
        self.return_ty = return_ty
        self.is_property = True

    def __str__(self):
        params = ",".join(self.params)
        return (
            f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"
        )

    def is_callable(self):
        return True

    def arity(self):
        return len(self.params)


class Scope:
    def __init__(self, enclosing_scope: Optional[Scope] = None):
        self.symbols: Dict[str, Symbol] = {}
        self.enclosing_scope = enclosing_scope
        # Field is set only on the first scope of a scope
        # Nesting
        self.locals = {}

    def resolve(self, name: str) -> Optional[Symbol]:
        symbol = self.get(name)
        if not symbol:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol

    def resolve_scope(self, name: str, depth: int) -> int:
        symbol = self.get(name)
        if not symbol:
            scope = self.enclosing_scope
            while scope is not None:
                symbol = scope.get(name)
                if symbol:
                    break
                depth -= 1
                scope = scope.enclosing_scope
            return -1
        return depth

    def add_local(self, name: str):
        if name in self.locals:
            return
        idx = len(self.locals)
        self.locals[name] = idx

    def get(self, name: str) -> Optional[Symbol]:
        return self.symbols.get(name)

    def define(self, name: str, symbol: Symbol):
        self.symbols[name] = symbol

    def count(self) -> int:
        return len(self.symbols)

    def __str__(self) -> str:
        symbols = [
            f"{symbol}:{sym_obj}" for symbol, sym_obj in self.symbols.items()
        ]
        table = "\n".join(symbols)
        return f"SCOPE:\n______\n{table}\n<EXITING>\n\n"
