''' Classes for code objects used to generate python code'''
    
from amanda.symbols import Tag
from amanda.tokens import TokenType as tt
from backend.types import Bool


INDENT = "    "



class CodeObj:

    def __str__(self):
        raise NotImplementedError("Subclasses must override this method")

class BinOp(CodeObj):

    def __init__(self,operator,lhs,rhs):

        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):

        operator = self.operator
        if operator == tt.E.value.lower():
            operator = "and"
        elif operator == tt.OU.value.lower():
            operator = "or"

        return f"({str(self.lhs)} {operator} {str(self.rhs)}) "


class UnaryOp(CodeObj):

    def __init__(self,operator,operand):

        self.operator = operator
        self.operand = operand


    def __str__(self):
        operator = self.operator
        if self.operator == tt.NAO.value.lower():
            operator = "not"
        return f"({operator} {self.operand})"



class VarDecl(CodeObj):

    def __init__(self,name,var_type):
        self.name = name
        self.var_type = var_type

    def __str__(self):
        value = None
        if self.var_type == Tag.INT:
            value = 0
        if self.var_type == Tag.REAL:
            value = 0.0
        if self.var_type == Tag.BOOL:
            value = Bool.FALSO
        return f"{self.name} = {value}"

class Block(CodeObj):

    def __init__(self,instructions,level):
        self.instructions = instructions
        self.level = level

    def __str__(self):
        #Add indentation to every instruction in the block
        #and separate instructions with Newline
        return "\n".join([
            f"{INDENT*self.level}{str(instr)}" for instr in self.instructions
        ])


class FunctionDecl(CodeObj):

    def __init__(self,name,body,params):
        self.name = name
        self.body = body 
        self.params = params

    def __str__(self):
        params = ",".join(self.params)
        return f"def {self.name}({params}):\n{str(self.body)}"


class Global(CodeObj):

    def __init__(self,names):
        self.names = names


    def __str__(self):
        names = ",".join(self.names)
        return f"global {names}"


class NonLocal(CodeObj):

    def __init__(self,names):
        self.names = names


    def __str__(self):
        names = ",".join(self.names)
        return f"nonlocal {names}"



class Call(CodeObj):

    def __init__(self,callee,args):
        self.callee = callee
        self.args = args

    def __str__(self):
        args = ",".join([str(arg) for arg in self.args])
        return f"{self.callee}({args})"
        

class Assign(CodeObj):

    def __init__(self,lhs,rhs):
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"

class Se(CodeObj):

    def __init__(self,condition,then_branch,else_branch=None):
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def __str__(self):
        if_stmt = f"if {str(self.condition)}:\n{str(self.then_branch)}\n"
        if self.else_branch:
            #Hack to get current indent level and use in the else block
            if_stmt = f"{if_stmt}{str(self.else_branch)}"
        return if_stmt
        

class Senao(CodeObj):

    def __init__(self,then_branch,level):
        self.then_branch = then_branch
        self.level = level

    def __str__(self):
        return f"{INDENT*self.level}else:\n{str(self.then_branch)}\n"


class Enquanto(CodeObj):

    def __init__(self,condition,body):

        self.condition = condition
        self.body = body

    def __str__(self):
        return f"while {str(self.condition)}:\n{str(self.body)}"

class Para(CodeObj):


    def __init__(self,expression,body):

        self.expression = expression
        self.body = body

    def __str__(self):
        return f"for {str(self.expression)}:\n{str(self.body)}"

class ParaExpr(CodeObj):

    def __init__(self,name,start,stop,inc=None):
        if not inc:
            #TODO: Fix this at some point
            #Hack in case of empty inc value
            # step defaults to -1 if start > stop else 1 
            inc = f"-1 if {str(start)} > {str(stop)} else 1"
        self.name = name
        self.start = start
        self.stop = stop
        self.inc = inc

    def __str__(self):
        return f"{str(self.name)} in range({self.start},{self.stop},{self.inc})"

class Retorna(CodeObj):

    def __init__(self,expression):
        self.expression = expression

    def __str__(self):
        return f"return {str(self.expression)}"


class Mostra(CodeObj):

    def __init__(self,expression,debug):
        self.expression = expression
        self.debug = debug

    def __str__(self):
        output=""
        #Redirect output to buffer of compiler
        if self.debug:
            output=",end=' ',file=__buffer__"
        return f"printc({str(self.expression)}{output})"
