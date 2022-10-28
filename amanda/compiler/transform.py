import amanda.compiler.ast as ast
from amanda.compiler.tokens import TokenType as TT, Token
from amanda.compiler.ast import node_of_type
from amanda.compiler.symbols import MethodSym, VariableSymbol
from typing import cast


def transform_node(node: ast.ASTNode) -> ast.ASTNode:
    nodeT = type(node)
    has_side_fx = (
        ast.Assign,
        ast.Call,
        ast.Set,
        ast.IndexGet,
        ast.IndexSet,
    )
    # TODO: Actually implement a jump table for escolha
    if node_of_type(node, ast.Escolha):
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
            se_node.condition = ast.Constant(
                new_token(TT.VERDADEIRO, "verdadeiro")
            )
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
                        equality_op(
                            left=case.expression, right=node.expression
                        ),
                        case.block,
                    )
                )
            return se_node
    # Ignore all unused expressions
    # WARNING: This might be a nasty bug, please test this
    # TODO: Implement a proper way to do this
    elif nodeT not in has_side_fx and isinstance(node, ast.Expr):
        return ast.NoOp()
    elif node_of_type(node, ast.Call) and node.symbol.is_property:
        method_sym = cast(MethodSym, node.symbol)
        instance = cast(ast.Get, node.callee).target
        method_sym.params = {
            "alvo": VariableSymbol("alvo", method_sym.return_ty),
            **method_sym.params,
        }
        node.fargs.insert(0, instance)
        var = ast.Variable(
            token=Token(
                TT.IDENTIFIER, method_sym.name, node.token.line, node.token.col
            ),
        )
        call_node = ast.Call(callee=var, fargs=node.fargs)
        call_node.symbol = method_sym
        return call_node
    else:
        return node
