from amanda.tokens import Token,TokenType

#TODO: Rename fields of some classes


#Base class for all ASTNodes
class ASTNode:
    def __init__(self,token=None):
        self.token = token

    def is_assignable(self):
        return False
    
    def accept(self,visitor):
        raise NotImplementedError("Subclasses must implement this method")


class Program(ASTNode):
    def __init__(self):
        self.children = []

    def add_child(self,node):
        self.children.append(node)

    def accept(self,visitor):
        return visitor.exec_program(self)


class Block(Program):

    def accept(self,visitor):
        return visitor.exec_block(self)


class Expr(ASTNode):

    def __init__(self,token=None):
        super().__init__(token)
        self.eval_type = None
        self.prom_type = None

    def __str__(self):
        return f"{self.token.lexeme}"


class Constant(Expr):

    def __init__(self,token):
        super().__init__(token)

    def accept(self,visitor):
        return visitor.exec_constant(self)

class Variable(Expr):

    def __init__(self,token):
        super().__init__(token)

    def is_assignable(self):
        return True

    def accept(self,visitor):
        return visitor.exec_variable(self)

class BinOp(Expr):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.right = right
        self.left = left
    
    def accept(self,visitor):
        return visitor.exec_binop(self)


class UnaryOp(Expr):
    def __init__(self,token,operand=None):
        super().__init__(token)
        self.operand = operand

    def accept(self,visitor):
        return visitor.exec_unaryop(self)

class VarDecl(ASTNode):
    def __init__(self,token,name=None,var_type=None,assign=None):
        super().__init__(token)
        self.var_type = var_type
        self.assign = assign
        self.name = name

    def accept(self,visitor):
        return visitor.exec_vardecl(self)

class Assign(Expr):
    def __init__(self,token,left=None,right=None):
        super().__init__(token)
        self.left = left
        self.right = right


    def accept(self,visitor):
        return visitor.exec_assign(self)

class Statement(ASTNode):
    def __init__(self,token,exp=None):
        super().__init__(token)
        self.exp = exp


class Retorna(Statement):
    def accept(self,visitor):
        return visitor.exec_retorna(self)



class Mostra(Statement):
    def accept(self,visitor):
        return visitor.exec_mostra(self)


class Se(ASTNode):
    def __init__(self,token,condition,then_branch,else_branch=None):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch

    def accept(self,visitor):
        return visitor.exec_se(self)

class Enquanto(ASTNode):
    def __init__(self,token,condition,statement):
        super().__init__(token)
        self.condition = condition
        self.statement =  statement

    def accept(self,visitor):
        return visitor.exec_enquanto(self)



class Para(ASTNode):
    def __init__(self,token,expression = None,statement = None):
        super().__init__(token)
        self.expression = expression
        self.statement =  statement

    def accept(self,visitor):
        return visitor.exec_para(self)



class ParaExpr(ASTNode):
    def __init__(self,name=None,range_expr=None):
        super().__init__(name)
        self.name = name
        self.range_expr = range_expr


    def accept(self,visitor):
        return visitor.exec_paraexpr(self)

class RangeExpr(ASTNode):
    def __init__(self,start=None,end=None,inc=None):
        super().__init__(start)
        self.start = start
        self.end = end
        self.inc = inc

    def accept(self,visitor):
        return visitor.exec_rangeexpr(self)

class Call(Expr):
    def __init__(self,callee=None,paren=None,fargs=[]):
        super().__init__(paren)
        self.callee = callee
        self.fargs = fargs

    def accept(self,visitor):
        return visitor.exec_call(self)


class Get(Expr):

    def __init__(self,target=None,member=None):
        super().__init__(member)
        self.target = target
        self.member = member

    def is_assignable(self):
        return True

class Set(Expr):

    def __init__(self,target=None,expr=None):
        super().__init__(expr.token)
        self.target = target
        self.expr = expr


class FunctionDecl(ASTNode):
    def __init__(self,name=None,block=None,func_type=None,params=[]):
        super().__init__(name)
        self.name = name
        self.params = params
        self.func_type = func_type
        self.block = block

    def accept(self,visitor):
        return visitor.exec_functiondecl(self)

class ClassDecl(ASTNode):

    def __init__(self,name=None,superclass=None,body=None):
        super().__init__(name)
        self.name = name
        self.superclass = superclass
        self.body = body

    def accept(self,visitor):
        pass


class ClassBody(Block):
    ''' Specialized block class for Amanda class declarations.
        It allows for names to be used before their declarations.'''

    def __init__(self):
        # Indicates if name resolution pass has occurred
        super().__init__()
        self.resolved = False

class Param(ASTNode):
    def __init__(self,param_type=None,name=None):
        super().__init__(name)
        self.param_type = param_type
        self.name = name

    def accept(self,visitor):
        return visitor.exec_param(self)


#Base class for visitor objects
class Visitor:

    ''' Dispatcher method that chooses the correct
        return visiting method'''

    def visit(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self,method_name,self.general_visit)
        if node_class == "block":
            return visitor_method(node,args)
        return visitor_method(node)

    def general_visit(self,node):
        pass
