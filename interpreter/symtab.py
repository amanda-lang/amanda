class SymbolTable:
    def __init__(self):
        self.symbols = {}

    def define(self,name,symbol):
        self.symbols[name] = symbol

    def resolve(self,name):
        return self.symbols.get(name)



#Abstract base class for all symbols
class Symbol:
    def __init__(name,type):
        self.name = name
        self.type = type

    def __str__(self):
        return f"<{self.__class__.__name} {self.name} {self.type}>"



class BuiltInType(Symbol):
    def __init__(self,name,type=None):
        super().__init__(name,type)

    def __str__(self):
        return name

class VariableSymbol(Symbol):

    def __init__(self,name,type):
        super().__init__(name,type)


class FunctionSymbol(Symbol):
    def __init__(self,name,type,params):
        super().__init__(name,type)
        self.params = params #list of symbols
