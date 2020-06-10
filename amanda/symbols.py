
class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self,name,symbol):
        self.symbols[name] = symbol

    def resolve(self,name):
        return self.symbols.get(name)

    def __str__(self):
        str = "\n"
        #str.join([f"{symbol}:{self.symbols[symbol]}" for symbol in self.symbol])
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
        elif self.name != Scope.LOCAL:
            sym = self.resolve(self.name)
            if isinstance(sym,FunctionSymbol):
                return self
        return self.enclosing_scope().get_enclosing_func()



    def define(self,name,symbol):
        super().define(name,symbol)

    def __str__(self):
        return f"SCOPE: {self.name}\n\n______\n{super().__str__()}\n\n<Exiting {self.name}>\n"



#Abstract base class for all symbols
#Change this type cheese
class Symbol:
    def __init__(self,name,type):
        self.name = name
        self.type = type

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.type})>"

    def is_valid_var(self):
        return False

    def is_type(self):
        return False

    def is_callable(self):
        return False


class Type(Symbol):
    ''' Class that represents a type 
    in amanda. Types will be used during
    semantic analysis to enforce type
    rules
    '''
    def __init__(self,name,super_type=None):
        super().__init__(name,None)
        self.super_type = super_type

    def __str__(self):
        return str(self.name)

    def is_type(self):
        return True



class BuiltInType(Type):
    pass



class VariableSymbol(Symbol):
    def __init__(self,name,type):
        super().__init__(name,type)
    def is_valid_var(self):
        return True



class FunctionSymbol(Symbol):
    def __init__(self,name,type,params={}):
        super().__init__(name,type)
        self.params = params #dict of symbols

    def __str__(self):
        params = ",".join(self.params)
        return f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"

    def is_callable(self):
        return True


class ClassSymbol(Type):
    ''' Represents a class in amanda.
        Both user defined and builtins.'''

    def __init__(self,name,members={},super_type=None):
        super().__init__(name,super_type)
        self.members = members

    def __str__(self):
        return f"{self.name}\n--------\n{self.members}\n"


