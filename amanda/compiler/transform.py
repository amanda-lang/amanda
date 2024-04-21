from dataclasses import dataclass
import amanda.compiler.ast as ast
from amanda.compiler.module import Module
from amanda.compiler.symbols.base import Type
from amanda.compiler.tokens import TokenType as TT, Token
from amanda.compiler.ast import node_of_type
from amanda.compiler.symbols.core import (
    FunctionSymbol,
    MethodSym,
    VariableSymbol,
)
from amanda.compiler.types.builtins import Builtins, SrcBuiltins

from typing import cast, Callable


def var_node(name: str, tok: Token) -> ast.Variable:
    return ast.Variable(
        token=Token(TT.IDENTIFIER, name, tok.line, tok.col),
    )


@dataclass
class ASTTransformer:
    module: Module
    program: ast.Module

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

    def general_transform(self, node: ast.ASTNode) -> ast.ASTNode | None:
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
            ty=Builtins.Bool,
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

    def _is_option(self, ty: Type) -> bool:
        return ty.is_constructed_from(SrcBuiltins.Opcao)

    def transform_call(self, node: ast.Call):
        self.transform(node.callee)
        for farg in node.fargs:
            self.transform(farg)

        # Ignore non-local and non-property symbols
        if not node.symbol.is_property and not node.symbol.is_external(
            self.module
        ):
            return node

        callee = node.callee
        if not callee.of_type(ast.Get):
            return node

        if (
            isinstance(callee, ast.Get)
            and self._is_option(callee.target.eval_type)
            and callee.member.lexeme == "valor_ou"
        ):
            return ast.Unwrap(option=callee.target, default_val=node.fargs[0])

        if callee.of_type(ast.Get) and callee.target.eval_type.is_module():
            # A call to a function in another module via a module alias
            sym = cast(FunctionSymbol, node.symbol)
            # Add func symbol to symbol table
            # Prefix with the name of the module to avoid overwriting
            # other methods with the same name, from different modules
            sym.name = sym.out_id = f"{callee}::{sym.name}"
            var = var_node(sym.name, node.token)
            call_node = ast.Call(callee=var, fargs=node.fargs)
            call_node.symbol = sym
            self.program.symbols.define(sym.name, sym)
            return call_node
        else:
            # Common method call
            sym = cast(MethodSym, node.symbol)
            instance = cast(ast.Get, node.callee).target
            sym.params = {
                "alvo": VariableSymbol("alvo", sym.return_ty, self.module),
                **sym.params,
            }
            node.fargs.insert(0, instance)
        var = var_node(sym.name, node.token)
        call_node = ast.Call(callee=var, fargs=node.fargs)
        call_node.symbol = sym
        return call_node

    def transform_get(self, node: ast.Get):
        self.transform(node.target)
        return (
            ast.Unwrap(option=node.target, default_val=None)
            if node.target.eval_type.is_constructed_from(SrcBuiltins.Opcao)
            and node.member.lexeme == "valor"
            else node
        )

    def transform_module(self, node: ast.Module) -> ast.Module:
        for child in node.children:
            self.transform(child)

        return node


def transform(ast: ast.Module, module: Module) -> ast.Module:
    return ASTTransformer(module, ast).transform_module(ast)
