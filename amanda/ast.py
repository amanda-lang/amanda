# TODO: Rename fields of some classes


class ASTNode:
    def __init__(self, token=None):
        self.token = token
        self.lineno = token.line

    def is_assignable(self):
        return False


class Usa(ASTNode):
    def __init__(self, token, *, module="", alias=None):
        super().__init__(token)
        self.module = module
        self.alias = alias


class Program(ASTNode):
    def __init__(self):
        self.children = []
        self.symbols = None

    def add_child(self, node):
        self.children.append(node)


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


class Variable(Expr):
    def __init__(self, token):
        super().__init__(token)
        self.var_symbol = (
            None  # Symbol will contain extra info for python code gen phase
        )

    def is_assignable(self):
        return True


class Converte(Expr):
    def __init__(self, token, expression, new_type):
        super().__init__(token)
        self.expression = expression
        self.new_type = new_type


class Lista(Expr):
    def __init__(self, token, array_type, expression):
        super().__init__(token)
        self.array_type = array_type
        self.expression = expression


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


class UnaryOp(Expr):
    def __init__(self, token, operand=None):
        super().__init__(token)
        self.operand = operand


class VarDecl(ASTNode):
    def __init__(self, token, name=None, var_type=None, assign=None):
        super().__init__(token)
        self.var_type = var_type
        self.assign = assign
        self.name = name


class Assign(Expr):
    def __init__(self, token, left=None, right=None):
        super().__init__(token)
        self.left = left
        self.right = right


class Statement(ASTNode):
    def __init__(self, token, exp=None):
        super().__init__(token)
        self.exp = exp


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


class SenaoSe(ASTNode):
    def __init__(self, token, condition, then_branch):
        super().__init__(token)
        self.condition = condition
        self.then_branch = then_branch


class Enquanto(ASTNode):
    def __init__(self, token, condition, statement):
        super().__init__(token)
        self.condition = condition
        # TODO: Rename this field to 'block'
        self.statement = statement


class CaseBlock(ASTNode):
    def __init__(self, token, expression, block):
        super().__init__(token)
        self.expression = expression
        self.block = block


class Escolha(ASTNode):
    def __init__(self, token, expression, cases, default_case):
        super().__init__(token)
        self.expression = expression
        self.cases = cases
        self.default_case = default_case


class Para(ASTNode):
    def __init__(self, token, expression=None, statement=None):
        super().__init__(token)
        self.expression = expression
        self.statement = statement


class ParaExpr(ASTNode):
    def __init__(self, name=None, range_expr=None):
        super().__init__(name)
        self.name = name
        self.range_expr = range_expr


class RangeExpr(ASTNode):
    def __init__(self, token, start=None, end=None, inc=None):
        super().__init__(token)
        self.start = start
        self.end = end
        self.inc = inc


class Call(Expr):
    def __init__(self, callee=None, paren=None, fargs=[]):
        super().__init__(paren)
        self.callee = callee
        self.fargs = fargs


class ListLiteral(Expr):
    def __init__(self, token, *, list_type=None, elements=None):
        super().__init__(token)
        self.list_type = list_type
        self.elements = elements


class Get(Expr):
    def __init__(self, target=None, member=None):
        super().__init__(member)
        self.target = target
        self.member = member

    def is_assignable(self):
        return True


class Index(Expr):
    def __init__(self, token, target, index):
        super().__init__(token)
        self.target = target
        self.index = index

    def is_assignable(self):
        return True


class Set(Expr):
    def __init__(self, target=None, expr=None):
        super().__init__(expr.token)
        self.target = target
        self.expr = expr


class FunctionDecl(ASTNode):
    def __init__(self, name=None, block=None, func_type=None, params=[]):
        super().__init__(name)
        self.name = name
        self.params = params
        self.func_type = func_type
        self.block = block


class ClassDecl(ASTNode):
    def __init__(self, name=None, superclass=None, body=None):
        super().__init__(name)
        self.name = name
        self.superclass = superclass
        self.body = body


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


class Type(ASTNode):
    def __init__(self, type_name, *, dim=0, is_list=False):
        super().__init__(type_name)
        self.type_name = type_name
        self.is_list = is_list
        self.dim = dim  # For lists only


# Base class for visitor objects
class Visitor:

    """Dispatcher method that chooses the correct
    return visiting method"""

    def visit(self, node, args=None):
        pass

    def general_visit(self, node):
        pass
