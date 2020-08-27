from amanda.frontend.tokens import TokenType as TT
from enum import Enum

class Symbol:
    def __init__(self,name,sym_type):
        self.name = name
        self.type = sym_type

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.type})>"

    def can_evaluate(self):
        return False

    def is_type(self):
        return False

    def is_callable(self):
        return False

class VariableSymbol(Symbol):
    def __init__(self,name,var_type):
        super().__init__(name,var_type)

    def can_evaluate(self):
        return True

class FunctionSymbol(Symbol):
    def __init__(self,name,func_type,params={}):
        super().__init__(name,func_type)
        self.params = params #dict of symbols

    def __str__(self):
        params = ",".join(self.params)
        return f"<{self.__class__.__name__}: ({self.name},{self.type}) ({params})>"

    def is_callable(self):
        return True

    def arity(self):
        return len(self.params)
#REMOVE name attribute from this class
class Scope:
    GLOBAL = "GLOBAL_SCOPE"
    LOCAL = "LOCAL_SCOPE"

    def __init__(self,name,enclosing_scope=None):
        self.symbols = {}
        self.name = name
        self.enclosing_scope = enclosing_scope

    def resolve(self,name):
        symbol = self.get(name)
        if not symbol:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol
    
    def get(self,name):
        return self.symbols.get(name)

    def define(self,name,symbol):
        self.symbols[name] = symbol

    def count(self):
        return len(self.symbols)

    def __str__(self):
        symbols = [
            f"{symbol}:{sym_obj}"\
            for symbol,sym_obj in self.symbols.items()
        ]
        table = "\n".join(symbols) 
        return f"SCOPE: {self.name}\n\n______\n{table}\n\n<Exiting {self.name}>\n"



class Type(Symbol):

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

class Klass(Type):

   def __init__(self,name,members):
       super().__init__(name,(Type.INDEF,))
       self.members = members
       self.constructor = None

   def __str__(self):
       return self.name

