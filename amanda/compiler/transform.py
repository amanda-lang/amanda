import amanda.compiler.ast as ast
from amanda.compiler.tokens import TokenType as TT, Token
from amanda.compiler.ast import node_of_type
from amanda.compiler.symbols import MethodSym, VariableSymbol
from typing import cast, Union, Tuple


def var_node(name: str, tok: Token) -> ast.Variable:
    return ast.Variable(
        token=Token(TT.IDENTIFIER, name, tok.line, tok.col),
    )


def transform_escolha(node: ast.Escolha) -> ast.ASTNode:
    token = node.token
    new_token = lambda tt, lexeme: Token(tt, lexeme, token.line, token.col)
    equality_op = lambda left, right: ast.BinOp(
        new_token(TT.DOUBLEEQUAL, "=="), left=left, right=right
    )
    # check node
    # transform node into ifs
    expr = node.expression
    # let
    se_node = ast.Se(token, None, None, elsif_branches=[], else_branch=None)
    if not node.cases and not node.default_case:
        return ast.NoOp()
    elif not node.cases and node.default_case:
        se_node.condition = ast.Constant(new_token(TT.VERDADEIRO, "verdadeiro"))
        se_node.then_branch = node.default_case
        return se_node
    else:
        first_case = node.cases[0]
        del node.cases[0]
        se_node.condition = equality_op(
            left=first_case.expression,
            right=node.expression,
        )
        se_node.then_branch = first_case.block
        se_node.else_branch = node.default_case
        for case in node.cases:
            se_node.elsif_branches.append(
                ast.SenaoSe(
                    token,
                    equality_op(left=case.expression, right=node.expression),
                    case.block,
                )
            )
        return se_node


def transform_children(child: ast.ASTNode, attr: Union[str, Tuple[str, int]]):
    new_child = transform(child)
    if isinstance(attr, str):
        setattr(child.parent, attr, new_child)
    else:
        children = getattr(child.parent, attr[0])
        children[attr[1]] = new_child


def transform(node: ast.ASTNode) -> ast.ASTNode:
    if node_of_type(node, ast.Block):
        children = node.children
        for i in range(len(children)):
            children[i] = transform(children[i])
        return node
    # TODO: Actually implement a jump table for escolha
    elif node_of_type(node, ast.Escolha):
        return transform_escolha(node)
    # Ignore all unused expressions
    # WARNING: This might be a nasty bug, please test this
    # TODO: Implement a proper way to do this
    elif node_of_type(node, ast.Call):
        if not node.symbol.is_property:
            return node
        method_sym = cast(MethodSym, node.symbol)
        instance = cast(ast.Get, node.callee).target
        method_sym.params = {
            "alvo": VariableSymbol("alvo", method_sym.return_ty),
            **method_sym.params,
        }
        node.fargs.insert(0, instance)
        var = var_node(method_sym.name, node.token)
        call_node = ast.Call(callee=var, fargs=node.fargs)
        call_node.symbol = method_sym
        return call_node
    elif node_of_type(node, ast.Expr):
        has_side_fx = (
            ast.Assign,
            ast.Call,
            ast.Set,
            ast.IndexGet,
            ast.IndexSet,
        )
        if type(node) not in has_side_fx and node.child_of(ast.Program):
            return ast.NoOp()
    else:
        node.for_each_child(transform_children)
    return node
