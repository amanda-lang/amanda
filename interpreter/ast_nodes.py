
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


class IntNode(ExpNode):
    def __init__(self,token):
        super().__init__(token)
        self.eval_type =ASTNode.EVAL_TYPE["int"]


class RealNode(ExpNode):
    def __init__(self,token):
        super().__init__(token)
        self.eval_type =ASTNode.EVAL_TYPE["real"]

class StringNode(ExpNode):
    def __init__(self,token):
        super().__init__(token)
        self.eval_type =ASTNode.EVAL_TYPE["string"]

class VarRefNode(ExpNode):
    def __init__(self,token):
        super().__init__(token)

class VarDeclNode(ExpNode):
    def __init__(self,token,type=None,identifier=None):
        super().__init__(token)
        self.type = type
        self.id = identifier

class ArrayDeclNode(ASTNode):
    def __init__(self,token,type=None,identifier=None,size=0):
        super().__init__(token)
        self.type = type
        self.id = identifier
        self.size = 0

class AssignNode(ASTNode):
    def __init__(self,token,t):
        super().__init__(token)





class Block(ASTNode):
    def __init__(self):
        self.children = []

    def add_child(self,node):
        self.children.append(node)
