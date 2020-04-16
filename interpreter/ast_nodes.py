from interpreter.tokens import Token
#Base class for all ASTNodes
class ASTNode:

    EVAL_TYPE = {
        "int":1,
        "real":2,
        "string":3
    }


    def __init__(self,token=None):
        self.token = token


class ExpNode(ASTNode):
    def __init__(self,token=None):
        super().__init(token)
        self.eval_type = None


# Class for all binary operations
class BinOpNode(ExpNode):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.right = right
        self.left = left

class UnaryOpNode(ExpNode):
    def __init__(self,token,operand=None):
        super().__init__(token)
        self.operand = operand


class VarDeclNode(ASTNode):
    def __init__(self,token,id=None,type=None,assign=None):
        super().__init__(token)
        self.type = type
        self.assign = assign
        self.id = id

class ArrayDeclNode(ASTNode):
    def __init__(self,token,id=None,type=None,size=0):
        super().__init__(token)
        self.type = type
        self.id = id
        self.size = 0

class AssignNode(ASTNode):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.left = left
        self.right = right

class Statement(ASTNode):
    def __init__(self,token,exp=None):
        super().__init__(token)
        self.exp = exp

class FunctionCall(ExpNode):
    def __init__(self,id=None,fargs=[]):
        super().__init__(Token("FUNCTION_CALL",None))
        self.id = id
        self.fargs = fargs

class FunctionDecl(ASTNode):
    def __init__(self,id=None,block=None,type=None,params=[]):
        super().__init__(Token("FUNCTION_DECL",None))
        self.id = id
        self.params = params
        self.type = type
        self.block = block

class ParamNode(ASTNode):
    def __init__(self,type=None,id=None):
        super().__init__(Token("FUNCTION_PARAM",None))
        self.type = type
        self.id = id

class ArrayRef(ExpNode):
    def __init__(self,id=None,index=None):
        super().__init__(Token("ARRAY_REF",None))
        self.id = self.id
        self.index = index


class Block(ASTNode):
    def __init__(self):
        self.children = []

    def add_child(self,node):
        self.children.append(node)



#Base class for visitor objects
class Visitor:

    ''' Dispatcher method that chooses the correct
        visiting method'''

    def visit(self,node):
        node_class = type(node).__name__.lower
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self,method_name,self.bad_visit)
        return visitor_method(node)

    def bad_visit(self,node):
        raise Exception("Unkwown node type")
