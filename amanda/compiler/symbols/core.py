from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, cast, Any
from amanda.compiler.module import Module
from amanda.compiler.symbols.base import Symbol, TypeVar, Typed, Type


class VariableSymbol(Typed):
    def __init__(self, name: str, var_type: Type, module: Module):
        super().__init__(name, var_type, module)

    def can_evaluate(self):
        return True

    def is_callable(self):
        return False

    def bind(self, **ty_args: Type) -> Typed:
        if not self.type.is_type_var():
            return self
        return VariableSymbol(self.name, ty_args[self.type.name], self.module)


class FunctionSymbol(Typed):
    def __init__(
        self,
        name: str,
        func_type: Type,
        *,
        module: Module,
        params: dict[str, VariableSymbol] = {},
        entrypoint=False,
    ):
        super().__init__(name, func_type, module)
        self.params = params  # dict of symbols
        self.scope = None
        self.entrypoint = entrypoint
        self._has_generic_params_cached: bool | None = None

    def __str__(self):
        params = ",".join(self.params)
        return (
            f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"
        )

    def can_evaluate(self):
        return False

    def is_callable(self):
        return True

    def arity(self):
        return len(self.params)

    def has_generic_params(self):
        if self._has_generic_params_cached is not None:
            return self._has_generic_params_cached
        self._has_generic_params_cached = any(
            map(lambda p: p.type.is_type_var(), self.params.values())
        )
        return self._has_generic_params_cached

    def bind(self, **ty_args: Type) -> Typed:
        if not self.has_generic_params() and not self.type.is_type_var():
            return self

        params = self.params
        if self.has_generic_params:
            params = {
                param: cast(VariableSymbol, value.bind(**ty_args))
                for param, value in self.params.items()
            }
        return_ty = self.type
        if self.type.is_type_var():
            return_ty = ty_args[self.type.name]

        return FunctionSymbol(
            self.name, return_ty, module=self.module, params=params
        )


class MethodSym(FunctionSymbol):
    def __init__(
        self,
        name: str,
        *,
        target_ty: Type,
        return_ty: Type,
        module: Module,
        params: dict[str, VariableSymbol] = {},
    ):
        super().__init__(name, return_ty, module=module, params=params)
        self.target_ty = target_ty
        self.return_ty = return_ty
        self.is_property = True

    def __str__(self):
        params = ",".join(self.params)
        return (
            f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"
        )

    def bind(self, **ty_args: Type) -> Typed:
        new_fn = cast(FunctionSymbol, super().bind(**ty_args))
        return MethodSym(
            self.name,
            target_ty=self.target_ty,
            return_ty=new_fn.type,
            module=self.module,
            params=new_fn.params,
        )


class Scope:
    def __init__(self, enclosing_scope: Optional[Scope] = None):
        self.symbols: dict[str, Symbol] = {}
        self.enclosing_scope = enclosing_scope
        self.methods: dict[str, dict[str, MethodSym]] = {}
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

    def resolve_typed(self, name: str) -> Optional[Typed]:
        sym = self.resolve(name)
        return cast(Typed, sym)

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

    def get_typed(self, name: str) -> Optional[Typed]:
        return cast(Typed, self.symbols.get(name))

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
