
class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self,name,symbol):
        self.symbols[name] = symbol

    def resolve(self,name):
        return self.symbols.get(name)

    def __str__(self):
        str = "\n"
        str.join([f"{symbol}:{self.symbol[symbol]}" for symbol in self.symbol])
        for symbol in self.symbols:
            sym_obj = self.symbols[symbol]
            str += f"{symbol}:{sym_obj}\n"
        return str


class Scope(SymbolTable):
    GLOBAL = "GLOBAL_SCOPE"
    LOCAL = "LOCAL_SCOPE"

    def __init__(self,name,enclosing_scope=None):
        super().__init__()
        self.name = name
        self.enclosing_scope = enclosing_scope

    def resolve(self,name):
        symbol = super().resolve(name)
        if symbol == None:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol

    #TODO: refactor this later because of classes
    def get_enclosing_func(self):
        if self.name == Scope.GLOBAL:
            return None
        if self.name != Scope.LOCAL:
            return self

        scope = self.enclosing_scope
        while scope:
            if scope.name not in (Scope.LOCAL,Scope.GLOBAL):
                return scope
            scope = scope.enclosing_scope
        return None


    def define(self,name,symbol,token=None):
        super().define(name,symbol)

    def __str__(self):
        return f"SCOPE: {self.name}\n\n______\n{super().__str__()}\n\n<Exiting {self.name}>\n"





#Abstract base class for all symbols
class Symbol:
    def __init__(self,name,type):
        self.name = name
        self.type = type

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.type})>"



class BuiltInType(Symbol):
    def __init__(self,name,type=None):
        super().__init__(name,type)

    def __str__(self):
        return str(self.name)

class VariableSymbol(Symbol):
    def __init__(self,name,type):
        super().__init__(name,type)


class FunctionSymbol(Symbol):
    def __init__(self,name,type,params):
        super().__init__(name,type)
        self.params = params #dict of symbols

    def __str__(self):
        params = ",".join(self.params)
        return f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"

class ArraySymbol(Symbol):
    def __init__(self,name,type,size = 0):
        super().__init__(name,type)
        self.size = size
