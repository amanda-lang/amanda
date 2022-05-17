from dataclasses import dataclass

# TODO: Rename fields of some classes
class ASTNode:
    def __init__(self, token):
        self.token = token
        self.parent = None
        self.lineno = token.line

    def tag_children(self):
        for attr in self.__dict__:
            node = getattr(self, attr, None)
            if isinstance(node, ASTNode):
                node.parent = self

    def is_assignable(self):
        return False


class Program:
    def __init__(self):
        self.children = []
        self.symbols = None

    def add_child(self, node):
        self.children.append(node)


class Usa(ASTNode):
    def __init__(self, token, *, module="", alias=None):
        super().__init__(token)
        self.module = module
        self.alias = alias
        self.tag_children()


class Block(Program):
    pass


class Expr(ASTNode):
    def __init__(self, token=None):
        super().__init__(token)
        self.eval_type = None
        self.prom_type = None

    def __str__(self):
        return f"{self.token.lexeme}"


class Constant(Expr):
    def __init__(self, token):
        super().__init__(token)


class FmtStr(Expr):
    def __init__(self, token, parts):
        super().__init__(token)
        self.parts = parts


class Variable(Expr):
    def __init__(self, token):
        super().__init__(token)
        self.var_symbol = (
            None  # Symbol will contain extra info for python code gen phase
        )

    def is_assignable(self):
        return True


class Converta(Expr):
    def __init__(self, token, target, new_type):
        super().__init__(token)
        self.target = target
        self.new_type = new_type
        self.tag_children()


class Lista(Expr):
    def __init__(self, token, array_type, expression):
        super().__init__(token)
        self.array_type = array_type
        self.expression = expression
        self.tag_children()


class Eu(Expr):
    def __init__(self, token):
        super().__init__(token)


class Super(Expr):
    def __init__(self, token):
        super().__init__(token)


class BinOp(Expr):
    def __init__(self, token, left=None, right=None):
        super().__init__(token)
        self.right = right
        self.left = left
        self.tag_children()


class UnaryOp(Expr):
    def __init__(self, token, operand=None):
        super().__init__(token)
        self.operand = operand
        self.tag_children()


class VarDecl(ASTNode):
    def __init__(self, token, name=None, var_type=None, assign=None):
        super().__init__(token)
        self.var_type = var_type
        self.assign = assign
        self.name = name
        self.tag_children()


class Assign(Expr):
    def __init__(self, token, left=None, right=None):
        super().__init__(token)
        self.left = left
        self.right = right
        self.tag_children()


class Statement(ASTNode):
    def __init__(self, token, exp=None):
        super().__init__(token)
        self.exp = exp
        self.tag_children()


class LoopCtlStmt(Statement):
    pass


class Retorna(Statement):
    pass


class Mostra(Statement):
    pass


class Se(ASTNode):
    def __init__(
        self,
        token,
        condition,
        then_branch,
        *,
        elsif_branches=None,
        else_branch=None,
    ):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch
        self.elsif_branches = elsif_branches
        self.else_branch = else_branch
        self.tag_children()


class SenaoSe(ASTNode):
    def __init__(self, token, condition, then_branch):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch
        self.tag_children()


class Enquanto(ASTNode):
    def __init__(self, token, condition, statement):
        super().__init__(token)
        self.condition = condition
        # TODO: Rename this field to 'block'
        self.statement = statement
        self.tag_children()


class CaseBlock(ASTNode):
    def __init__(self, token, expression, block):
        super().__init__(token)
        self.expression = expression
        self.block = block
        self.tag_children()


class Escolha(ASTNode):
    def __init__(self, token, expression, cases, default_case):
        super().__init__(token)
        self.expression = expression
        self.cases = cases
        self.default_case = default_case
        self.tag_children()


class Para(ASTNode):
    def __init__(self, token, expression=None, statement=None):
        super().__init__(token)
        self.expression = expression
        self.statement = statement
        self.tag_children()


class ParaExpr(ASTNode):
    def __init__(self, name=None, range_expr=None):
        super().__init__(name)
        self.name = name
        self.range_expr = range_expr
        self.tag_children()


class RangeExpr(ASTNode):
    def __init__(self, token, start=None, end=None, inc=None):
        super().__init__(token)
        self.start = start
        self.end = end
        self.inc = inc
        self.tag_children()


class Call(Expr):
    def __init__(self, callee=None, paren=None, fargs=[]):
        super().__init__(paren)
        self.callee = callee
        self.fargs = fargs
        self.tag_children()


class ListLiteral(Expr):
    def __init__(self, token, *, list_type=None, elements=None):
        super().__init__(token)
        self.list_type = list_type
        self.elements = elements
        self.tag_children()


class Get(Expr):
    def __init__(self, target=None, member=None):
        super().__init__(member)
        self.target = target
        self.member = member
        self.tag_children()

    def is_assignable(self):
        return True


class IndexGet(Expr):
    def __init__(self, token, target, index):
        super().__init__(token)
        self.target = target
        self.index = index
        self.tag_children()

    def is_assignable(self):
        return True


class IndexSet(Expr):
    def __init__(self, token, index, value):
        super().__init__(token)
        self.index = index
        self.value = value
        self.tag_children()

    def is_assignable(self):
        return True


class Set(Expr):
    def __init__(self, target=None, expr=None):
        super().__init__(expr.token)
        self.target = target
        self.expr = expr
        self.tag_children()


class FunctionDecl(ASTNode):
    def __init__(self, name=None, block=None, func_type=None, params=[]):
        super().__init__(name)
        self.name = name
        self.params = params
        self.func_type = func_type
        self.block = block
        self.is_native = False
        self.tag_children()


class ClassDecl(ASTNode):
    def __init__(self, name=None, superclass=None, body=None):
        super().__init__(name)
        self.name = name
        self.superclass = superclass
        self.body = body
        self.tag_children()


class ClassBody(Block):
    """Specialized block class for Amanda class declarations.
    It allows for names to be used before their declarations."""

    def __init__(self):
        # Indicates if name resolution pass has occurred
        super().__init__()
        self.resolved = False


class Param(ASTNode):
    def __init__(self, param_type=None, name=None):
        super().__init__(name)
        self.param_type = param_type
        self.name = name
        self.tag_children()


class Type(ASTNode):
    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.tag_children()


@dataclass
class ArrayType(ASTNode):
    element_type: Type


# Base class for visitor objects
class Visitor:

    """Dispatcher method that chooses the correct
    return visiting method"""

    def visit(self, node, args=None):
        pass

    def general_visit(self, node):
        pass
