from amanda.tokens import TokenType as TT
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
        if not symbol:
            if self.enclosing_scope is not None:
                return self.enclosing_scope.resolve(name)
            else:
                return None
        return symbol

    def get_enclosing_func(self):
        if self.name == Scope.GLOBAL:
            return None
        elif self.name != Scope.LOCAL:
            sym = self.resolve(self.name)
            if isinstance(sym,FunctionSymbol):
                return sym
        return self.enclosing_scope.get_enclosing_func()



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

    def can_evaluate(self):
        return False

    def is_type(self):
        return False

    def is_callable(self):
        return False



#Tags used during index lookup of operations
class Tag(Enum):

    INT = 0
    REAL = 1
    BOOL = 2
    REF = 3

    def __str__(self):
        return self.name.lower()


class Type(Symbol):
    ''' Class that represents a type 
    in amanda. Types will be used during
    semantic analysis to enforce type
    rules
    '''
    # Type indexes used for table lookups to validate
    # operations and type promotions
    # Two operands must be of the same type before
    # an operation can be perfomed on them

    arithmetic = [
    #       int       real       bool
        [Tag.INT,Tag.REAL,None],
        [Tag.REAL,Tag.REAL,None],
        [None,None,None],
    ]

    #Table for  type for >,<,>=,<=
    comparison = [
    #       int       real       bool
        [Tag.BOOL,Tag.BOOL,None],
        [Tag.BOOL,Tag.BOOL,None],
        [None,None,None],
    ]

    #table for type results for == !=
    equality = [
    #       int       real       bool
        [Tag.BOOL,Tag.BOOL,Tag.BOOL],
        [Tag.BOOL,Tag.BOOL,Tag.BOOL],
        [None,None,Tag.BOOL],
    ]

    #table for type results for e ou !
    logic = [
    #    int  real  bool
        [None,None,None],
        [None,None,None],
        [None,None,Tag.BOOL],
    ]

    promotion = [
    #    int  real  bool
        [None,Tag.REAL,None],
        [None,None,None],
        [None,None,None],
    ]


    def __init__(self,name,tag):
        super().__init__(name,None)
        self.tag = tag

    def __str__(self):
        return str(self.name)

    def is_type(self):
        return True

    def validate_op(self,op,other,scope):

        #Reference types don't participate in ops 
        if self.tag == Tag.REF or other.tag == Tag.REF:
            return None

        result = None
        if op in (TT.PLUS,TT.MINUS,TT.STAR,TT.SLASH,TT.MODULO):
            result = self.arithmetic[self.tag.value][other.tag.value]
        elif op in (TT.GREATER,TT.LESS,TT.GREATEREQ,TT.LESSEQ):
            result = self.comparison[self.tag.value][other.tag.value]
        elif op in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            result = self.equality[self.tag.value][other.tag.value]
        elif op in (TT.E,TT.OU):
            result = self.logic[self.tag.value][other.tag.value]

        if not result:
            return None
        return scope.resolve(str(result))

    def promote_to(self,other,scope):
        #Reference types don't participate in ops 
        if self.tag == Tag.REF or other.tag == Tag.REF:
            return None

        result = self.promotion[self.tag.value][other.tag.value]
        if not result:
            return None
        return scope.resolve(str(result))

class BuiltInType(Type):
    pass


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


