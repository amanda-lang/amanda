''' Classes for code objects used to generate python code'''
    
from amanda.symbols import Tag
from amanda.tokens import TokenType as tt
from amanda.types import Bool


INDENT = "    "
#Name of buffer used in test
TEST_BUFFER = "_buffer_"



class CodeObj:


    def __init__(self,py_lineno=0,ama_lineno=0):
        self.py_lineno = py_lineno #Line number in python output src
        self.ama_lineno = ama_lineno #Line number in amanda src


    def get_ama_lineno(self,py_lineno):
        #Check if this CodeObj generates the line py_lineno
        #and returns the ama_lineno
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        return None

    def __str__(self):
        raise NotImplementedError("Subclasses must override this method")


class Pass(CodeObj):
    def __init(self):
        super().__init__(py_lineno,ama_lineno)


    def __str__(self):
        return f"pass"

class Del(CodeObj):

    def __init__(self,py_lineno,ama_lineno,names):
        super().__init__(py_lineno,ama_lineno)
        self.names = names

    def __str__(self):
        names = ",".join(self.names)
        return f"del {names}"
        


class BinOp(CodeObj):

    def __init__(self,py_lineno,ama_lineno,operator,lhs,rhs):
        super().__init__(py_lineno,ama_lineno)

        self.operator = operator
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):

        operator = self.operator
        if operator == tt.E.value.lower():
            operator = "and"
        elif operator == tt.OU.value.lower():
            operator = "or"

        return f"({str(self.lhs)} {operator} {str(self.rhs)})"


class UnaryOp(CodeObj):

    def __init__(self,py_lineno,ama_lineno,operator,operand):

        super().__init__(py_lineno,ama_lineno)
        self.operator = operator
        self.operand = operand


    def __str__(self):
        operator = self.operator
        if self.operator == tt.NAO.value.lower():
            operator = "not"
        return f"({operator} {self.operand})"



class VarDecl(CodeObj):

    def __init__(self,py_lineno,ama_lineno,name,var_type):
        super().__init__(py_lineno,ama_lineno)
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

    def __init__(self,py_lineno,ama_lineno,instructions,level,del_stmt=None):
        super().__init__(py_lineno,ama_lineno)
        self.instructions = instructions
        self.level = level
        self.del_stmt = del_stmt


    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        ama_lineno = None
        for instr in self.instructions:
            ama_lineno = instr.get_ama_lineno(py_lineno)
            if ama_lineno: return ama_lineno
        return ama_lineno
        
            

    def __str__(self):
        #Add indentation to every instruction in the block
        #and separate instructions with Newline
        block = "\n".join([
            f"{INDENT*self.level}{str(instr)}" for instr in self.instructions
        ])
        if self.del_stmt:
            block += f"\n{INDENT*(self.level-1)}{str(self.del_stmt)}"

        return block



class FunctionDecl(CodeObj):

    def __init__(self,py_lineno,ama_lineno,name,body,params):
        super().__init__(py_lineno,ama_lineno)
        self.name = name
        self.body = body 
        self.params = params


    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        return self.body.get_ama_lineno(py_lineno)


    def __str__(self):
        params = ",".join(self.params)
        return f"def {self.name}({params}):\n{str(self.body)}"





class Call(CodeObj):

    def __init__(self,py_lineno,ama_lineno,callee,args):
        super().__init__(py_lineno,ama_lineno)
        self.callee = callee
        self.args = args

    def __str__(self):
        args = ",".join([str(arg) for arg in self.args])
        return f"{self.callee}({args})"
        

class Assign(CodeObj):

    def __init__(self,py_lineno,ama_lineno,lhs,rhs):
        super().__init__(py_lineno,ama_lineno)
        self.lhs = lhs
        self.rhs = rhs

    def __str__(self):
        return f"{self.lhs} = {self.rhs}"

class Se(CodeObj):

    def __init__(self,py_lineno,ama_lineno,condition,then_branch,else_branch=None):
        super().__init__(py_lineno,ama_lineno)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch


    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        ama_lineno = self.then_branch.get_ama_lineno(py_lineno)
        if self.else_branch and not ama_lineno:
            ama_lineno = self.else_branch.get_ama_lineno(py_lineno)
        return ama_lineno

    def __str__(self):
        then_branch = self.then_branch
        if_stmt = f"if {str(self.condition)}:\n{str(then_branch)}\n"
        if self.else_branch:
            #Hack to get current indent level and use in the else block
            if_stmt = f"{if_stmt}{str(self.else_branch)}"
        return if_stmt
        

class Senao(CodeObj):

    def __init__(self,py_lineno,ama_lineno,then_branch,level):
        super().__init__(py_lineno,ama_lineno)
        self.then_branch = then_branch
        self.level = level

    def get_lines(self):
        return str(self).count("\n")

    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        return self.then_branch.get_ama_lineno(py_lineno)

    def __str__(self):
        then_branch = self.then_branch
        return f"{INDENT*self.level}else:\n{str(then_branch)}\n"


class Enquanto(CodeObj):

    def __init__(self,py_lineno,ama_lineno,condition,body):

        super().__init__(py_lineno,ama_lineno)
        self.condition = condition
        self.body = body


    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        return self.body.get_ama_lineno(py_lineno)

    def __str__(self):
        return f"while {str(self.condition)}:\n{str(self.body)}"

class Para(CodeObj):


    def __init__(self,py_lineno,ama_lineno,expression,body):

        super().__init__(py_lineno,ama_lineno)
        self.expression = expression
        self.body = body


    def get_ama_lineno(self,py_lineno):
        if self.py_lineno == py_lineno:
            return self.ama_lineno
        return self.body.get_ama_lineno(py_lineno)


    def __str__(self):
        return f"for {str(self.expression)}:\n{str(self.body)}"

class ParaExpr(CodeObj):

    def __init__(self,py_lineno,ama_lineno,name,start,stop,inc=None):
        super().__init__(py_lineno,ama_lineno)
        if not inc:
            # step defaults to -1 if start > stop else 1 
            inc = f"-1 if {str(start)} > {str(stop)} else 1"
        self.name = name
        self.start = start
        self.stop = stop
        self.inc = inc

    def __str__(self):
        return f"{str(self.name)} in range({self.start},{self.stop},{self.inc})"


class Global(CodeObj):

    def __init__(self,py_lineno,ama_lineno,names):
        super().__init__(py_lineno,ama_lineno)
        self.names = names

    def __str__(self):
        names = ",".join(self.names)
        return f"global {names}"


class NonLocal(CodeObj):

    def __init__(self,py_lineno,ama_lineno,names):
        super().__init__(py_lineno,ama_lineno)
        self.names = names

    def __str__(self):
        names = ",".join(self.names)
        return f"nonlocal {names}"


class Retorna(CodeObj):

    def __init__(self,py_lineno,ama_lineno,expression):
        super().__init__(py_lineno,ama_lineno)
        self.expression = expression

    def __str__(self):
        return f"return {str(self.expression)}"


class Mostra(CodeObj):

    def __init__(self,py_lineno,ama_lineno,expression,debug):
        super().__init__(py_lineno,ama_lineno)
        self.expression = expression
        self.debug = debug

    def __str__(self):
        output=""
        #Redirect output to buffer of compiler
        if self.debug:
            output=f",end=' ',file={TEST_BUFFER}"
        return f"printc({str(self.expression)}{output})"



