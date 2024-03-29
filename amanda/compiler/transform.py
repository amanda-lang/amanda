from dataclasses import dataclass
import amanda.compiler.ast as ast
from amanda.compiler.tokens import TokenType as TT, Token
from amanda.compiler.ast import node_of_type
from amanda.compiler.symbols import MethodSym, VariableSymbol
from amanda.compiler import symbols
from amanda.compiler.type import Type, Kind
import pprint

from typing import cast, Union, Tuple, Optional, Callable


def var_node(name: str, tok: Token) -> ast.Variable:
    return ast.Variable(
        token=Token(TT.IDENTIFIER, name, tok.line, tok.col),
    )


@dataclass
class ASTTransformer:
    def transform(self, node, args=None) -> ast.ASTNode:
        node_class = type(node).__name__.lower()
        method_name = f"transform_{node_class}"
        visitor_method = getattr(self, method_name, self.general_transform)
        new_node: ast.ASTNode | None = visitor_method(node)
        if new_node is None or not isinstance(new_node, ast.ASTNode):
            return node
        if new_node == node:
            return node
        parent: ast.ASTNode = node.parent
        if not parent:
            raise ValueError(
                f"Node of type {type(node).__name__} has no parent."
            )
        parent.for_each_child(self.replace_child(parent, node, new_node))
        return new_node

    def replace_child(
        self, parent: ast.ASTNode, old_node: ast.ASTNode, new_node: ast.ASTNode
    ) -> Callable:
        def _replace(child: ast.ASTNode, attr: ast.ChildAttr):
            if child != old_node:
                return
            if isinstance(attr, str):
                setattr(parent, attr, new_node)
            else:
                list_attr, i = attr
                getattr(parent, list_attr)[i] = new_node

        return _replace

    def empty_transform(self, node: ast.ASTNode, loc: ast.ChildAttr):
        self.transform(node)

    def general_transform(self, node: ast.ASTNode) -> Optional[ast.ASTNode]:
        node.for_each_child(self.empty_transform)
        if node.of_type(ast.Converta):
            return node

    def transform_escolha(self, node: ast.Escolha) -> ast.ASTNode:
        token = node.token
        new_token = lambda tt, lexeme: Token(tt, lexeme, token.line, token.col)
        equality_op = lambda left, right: ast.BinOp(
            new_token(TT.DOUBLEEQUAL, "=="),
            left=left,
            right=right,
            ty=Type(Kind.TBOOL),
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

    def transform_call(self, node: ast.Call):
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

    def transform_program(self, node: ast.Program) -> ast.Program:

        for child in node.children:
            self.transform(child)

        return node


def transform(program: ast.Program) -> ast.Program:
    return ASTTransformer().transform_program(program)
