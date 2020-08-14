from amanda.frontend.tokens import TokenType as TT
from enum import Enum



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
        for symbol,sym_obj in self.symbols.items():
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
        if not symbol:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol
    
    def get(self,name):
        return super().resolve(name)

    def define(self,name,symbol):
        super().define(name,symbol)

    def count(self):
        return len(self.symbols)

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

    def can_evaluate(self):
        return False

    def is_type(self):
        return False

    def is_callable(self):
        return False

class VariableSymbol(Symbol):
    def __init__(self,name,type):
        super().__init__(name,type)
    def can_evaluate(self):
        return True

class FunctionSymbol(Symbol):
    def __init__(self,name,func_type,params={}):
        super().__init__(name,func_type)
        self.params = params #dict of symbols
        self.is_constructor = False #indicates if param is a constructor

    def __str__(self):
        params = ",".join(self.params)
        return f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"

    def is_callable(self):
        return True

    def arity(self):
        return len(self.params)

class Type(Symbol):
    ''' Class that represents a type 
    in amanda. Types will be used during
    semantic analysis to enforce type
    rules
    '''
    def __init__(self,name,prom_types=[]):
        super().__init__(name,None)
        self.prom_types = prom_types

    def __str__(self):
        return str(self.name)

    def is_type(self):
        return True

    def is_numeric(self):
        return self == Type.INT or self == Type.REAL

    def is_operable(self):
        return self != Type.VAZIO and self != Type.INDEF

    def promote_to(self,other):
        return other if other in self.prom_types else None

#Add Builtin types 
#All types except vazio can be promoted to indef
Type.INDEF = Type("indef")
Type.VAZIO = Type("vazio")
Type.REAL = Type("real",(Type.INDEF,))
Type.INT = Type("int",(Type.REAL,Type.INDEF))
Type.BOOL = Type("bool",(Type.INDEF,))
Type.TEXTO = Type("texto",(Type.INDEF,))


class Lista(Type):

    def __init__(self,subtype):
        super().__init__("lista",(Type.INDEF,))
        self.subtype = subtype

    def __str__(self):
        return f"[]{self.subtype}"

    def __eq__(self,other):
        if type(other) != Lista:
            return False
        return self.subtype == other.subtype

class ClassSymbol(Type):
    ''' Represents a class in amanda.
        Both user defined and builtins.'''

    def __init__(self,name,members={},superclass=None):
        super().__init__(name,Tag.REF)
        self.members = members
        self.resolved = False
        self.superclass = superclass

    def is_callable(self):
        return True

    def __str__(self):
        return self.name

    def get_member(self,member):
        return self.members.get(member)

    def resolve_member(self,member):
        #Also does lookup in super class
        prop = self.members.get(member)
        if not prop and self.superclass:
            return self.superclass.resolve_member(member)
        return prop


