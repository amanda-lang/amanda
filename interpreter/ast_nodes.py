from interpreter.tokens import Token
#Base class for all ASTNodes
class ASTNode:


    def __init__(self,token=None):
        self.token = token

    def visit(self):
        pass

class Program(ASTNode):
    def __init__(self):
        self.children = []

    def add_child(self,node):
        self.children.append(node)

    def visit(self):
        print("In block:")
        for child in self.children:
            child.visit()

class Block(Program):
    pass




class ExpNode(ASTNode):
    def __init__(self,token=None):
        super().__init__(token)
        self.eval_type = None
        self.prom_type = None

    def visit(self):
        print(self)

    def __str__(self):
        return f"{self.token.lexeme}"


# Class for all binary operations
class BinOpNode(ExpNode):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.right = right
        self.left = left

    def visit(self):
        print("Binary op:")
        printself.left.visit()
        print(self.token.lexeme,end="")
        self.right.visit()


class UnaryOpNode(ExpNode):
    def __init__(self,token,operand=None):
        super().__init__(token)
        self.operand = operand

    def visit(self):
        print("Unary op: ")
        print(self.token)
        self.operand.visit()



class VarDeclNode(ASTNode):
    def __init__(self,token,id=None,type=None,assign=None):
        super().__init__(token)
        self.type = type
        self.assign = assign
        self.id = id

    def visit(self):
        print(f"Variable decl: {self.id}")
        if self.assign is not None:
            self.assign.visit()

class ArrayDeclNode(ASTNode):
    def __init__(self,token,id=None,type=None,size=0):
        super().__init__(token)
        self.type = type
        self.id = id
        self.size = size

    def visit(self):
        print(f"Array declaration: {self.id} [{self.size}]")

class AssignNode(ExpNode):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.left = left
        self.right = right

    def visit(self):
        print(f"Assignment: {self.left} = {self.right}")


class Statement(ASTNode):
    def __init__(self,token,exp=None):
        super().__init__(token)
        self.exp = exp

    def visit(self):
        print(f"Statement: {self.token.lexeme} {self.token.line}")

    def __str__(self):
        return f"Statement: {self.token.lexeme} {self.token.line}"


class SeStatement(ASTNode):
    def __init__(self,token,condition,then_branch,else_branch=None):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

class WhileStatement(ASTNode):
    def __init__(self,token,condition,statement):
        super().__init__(token)
        self.condition = condition
        self.statement =  statement

class ForStatement(ASTNode):
    def __init__(self,token,expression = None,statement = None):
        super().__init__(token)
        self.expression = expression
        self.statement =  statement

class ForExpr(ASTNode):
    def __init__(self,id=None,range=None):
        super().__init__(Token("FOR_EXPR",None))
        self.id = id
        self.range = range

class RangeExpr(ASTNode):
    def __init__(self,start=None,end=None,inc=None):
        super().__init__(Token("RANGE",None))
        self.start = start
        self.end = end
        self.inc = inc

class FunctionCall(ExpNode):
    def __init__(self,id=None,fargs=[]):
        super().__init__(Token("FUNCTION_CALL",None))
        self.id = id
        self.fargs = fargs

    def visit(self):
        print(f"Function call: {self.id}")
        for args in self.fargs:
            args.visit()

class FunctionDecl(ASTNode):
    def __init__(self,id=None,block=None,type=None,params=[]):
        super().__init__(Token("FUNCTION_DECL",None))
        self.id = id
        self.params = params
        self.type = type
        self.block = block

    def visit(self):
        print(f"Function declaration: {self.id}")
        print("Parameters:")
        for param in self.params:
            print(param)
        self.block.visit()


class ParamNode(ASTNode):
    def __init__(self,type=None,id=None,is_array=False):
        super().__init__(Token("FUNCTION_PARAM",None))
        self.type = type
        self.id = id
        self.is_array = is_array

    def __str__(self):
        return f"{self.type} {self.id}"

class ArrayRef(ExpNode):
    def __init__(self,id=None,index=None):
        super().__init__(Token("ARRAY_REF",None))
        self.id = id
        self.index = index
    def visit(self):
        print(f"Array reference: {self.id}[{self.index}]")




#Base class for visitor objects
class Visitor:

    ''' Dispatcher method that chooses the correct
        visiting method'''

    def visit(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self,method_name,self.general_visit)
        if node_class == "block":
            return visitor_method(node,args)
        return visitor_method(node)

    def general_visit(self,node):
        pass
