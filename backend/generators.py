''' Classes for code objects used to generate python code'''
    
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

    def __init__(self,name,assign=None):
        self.name = name
        self.assign = assign

    def __str__(self):
        return f"{self.name} = None"

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

        then_branch = f"if {str(self.condition)}:\n{str(self.then_branch)}\n"
        if self.else_branch:
            return f"{then_branch}else:\n{str(self.else_branch)}"
        return then_branch
        

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
