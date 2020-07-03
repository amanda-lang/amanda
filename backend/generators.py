''' Classes for code objects used to generate python code'''
    
from amanda.symbols import Tag


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
        return f"({str(self.lhs)} {self.operator} {str(self.rhs)}) "


class UnaryOp(CodeObj):

    def __init__(self,operator,operand):

        self.operator = operator
        self.operand = operand


    def __str__(self):
        return f"({self.operator}{self.operand})"



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
        




class Retorna(CodeObj):

    def __init__(self,expression):
        self.expression = expression

    def __str__(self):
        return f"return {str(self.expression)}"


class Mostra(CodeObj):

    def __init__(self,expression):
        self.expression = expression

    def __str__(self):
        return f"print({str(self.expression)})"
