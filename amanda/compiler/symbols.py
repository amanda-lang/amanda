from amanda.compiler.ast import Program
from amanda.compiler.tokens import TokenType as TT
from dataclasses import dataclass


@dataclass
class Module:
    fpath: str
    ast: Program = None
    loaded: bool = False


class Symbol:
    def __init__(self, name, sym_type):
        self.name = name
        self.out_id = name  # symbol id in compiled source program
        self.type = sym_type
        self.is_property = False  # Avoid this repitition
        self.is_global = False

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.out_id},{self.type})>"

    def can_evaluate(self):
        return False

    def is_type(self):
        return False

    def is_callable(self):
        return False


class VariableSymbol(Symbol):
    def __init__(self, name, var_type):
        super().__init__(name, var_type)

    def can_evaluate(self):
        return True


class FunctionSymbol(Symbol):
    def __init__(self, name, func_type, params={}):
        super().__init__(name, func_type)
        self.params = params  # dict of symbols
        self.scope = None

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
    def __init__(self, enclosing_scope=None):
        self.symbols = {}
        self.enclosing_scope = enclosing_scope
        # Field is set only on the first scope of a scope
        # Nesting
        self.locals = {}

    def resolve(self, name):
        symbol = self.get(name)
        if not symbol:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol

    def resolve_scope(self, name, depth):
        symbol = self.get(name)
        if not symbol:
            scope = self.enclosing_scope
            while scope is not None:
                symbol = self.enclosing_scope.get(name)
                if symbol:
                    break
                depth -= 1
                scope = scope.enclosing_scope
            return -1
        return depth

    def add_local(self, name):
        if name in self.locals:
            return
        idx = len(self.locals)
        self.locals[name] = idx

    def get(self, name):
        return self.symbols.get(name)

    def define(self, name, symbol):
        self.symbols[name] = symbol

    def count(self):
        return len(self.symbols)

    def __str__(self):
        symbols = [
            f"{symbol}:{sym_obj}" for symbol, sym_obj in self.symbols.items()
        ]
        table = "\n".join(symbols)
        return f"SCOPE:\n______\n{table}\n<EXITING>\n\n"
