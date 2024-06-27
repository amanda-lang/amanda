import typing
import amanda.compiler.ast as ast
from amanda.compiler.check.exhaustiveness import IgualaCompiler
import amanda.compiler.symbols.core as symbols
from amanda.compiler.check.checker import Checker
from amanda.compiler.error import Errors
from amanda.compiler.types.builtins import Builtins
from amanda.compiler.types.core import Variant, Type, VariantCons
import utils.tycheck as tycheck
import pprint


def check_iguala(checker: Checker, iguala: ast.Iguala):
    scope = symbols.Scope(checker.ctx_scope)
    checker.enter_scope(scope)

    target = iguala.target
    checker.visit(target)
    if target.eval_type == Builtins.Vazio:
        checker.error(Errors.VOID_FN_MATCH_TARGET)

    for arm in iguala.arms:
        check_arm(checker, iguala, arm)

    # if target is not a reference to a var, must store it in a var
    # so that it can be used later
    match target:
        case ast.Variable(var_symbol=var):
            iguala.target_binding = var
        case ast.Alvo():
            iguala.target_binding = target.var_symbol
        case _:
            sym = symbols.VariableSymbol(
                "_target_", target.eval_type, checker.ctx_module
            )
            checker.define_symbol(sym, checker.scope_depth, scope)
            iguala.target_binding = sym

    compiler = IgualaCompiler(scope, checker.ctx_module)
    tree = compiler.compile(iguala)
    if tree.diagnostics.missing:
        # Non-exhaustive pattern matching. Report error
        if target.eval_type.has_finite_constructors():
            missing_patterns = "\n".join(
                [f"* {pattern} => ... " for pattern in tree.missing_patterns()]
            )
            checker.error_with_loc(
                iguala.token,
                Errors.NON_EXHAUSTIVE_PATTERN_MATCH_FINITE,
                ty=target.eval_type,
                missing_patterns=missing_patterns,
            )
        else:
            checker.error_with_loc(
                iguala.token,
                Errors.NON_EXHAUSTIVE_PATTERN_MATCH_INFINITE,
            )
    # Validate reachable blocks
    first_block = tree.diagnostics.reachable[0]
    checker.visit(first_block)
    iguala.eval_type = first_block.eval_type
    for block in tree.diagnostics.reachable[1:]:
        checker.visit(block)
        if block.eval_type != iguala.eval_type:
            checker.error(
                Errors.IGUALA_BLOCK_BAD_RETURN_TY,
                expected=iguala.eval_type,
                actual=block.eval_type,
            )
    checker.leave_scope()


def check_binding_pattern(
    checker: Checker, arm: ast.IgualaArm, target_ty: Type, var: ast.Variable
):
    arm.pattern.eval_type = target_ty
    scope = tycheck.unwrap(arm.body.symbols)
    var_name = var.token.lexeme
    if var_name in scope.symbols:
        checker.error_with_loc(
            var.token, Errors.BINDING_ALREADY_IN_USE, var=var_name
        )
    checker.define_symbol(
        symbols.VariableSymbol(var.token.lexeme, target_ty, checker.ctx_module),
        checker.scope_depth + 1,
        scope,
    )


def check_pattern(checker: Checker, arm: ast.IgualaArm, target_ty: Type):
    match arm.pattern:
        case ast.ADTPattern(adt, args):
            checker.visit(adt)
            sym = tycheck.unwrap(
                adt.symbol if isinstance(adt, ast.Path) else adt.var_symbol
            )
            match sym:
                case Variant(params=params):
                    if not sym.is_callable() and args:
                        checker.error(
                            Errors.VARIANT_TAKES_NO_ARGS,
                            variant=sym.qualified_name(),
                        )
                    for pattern, ty in zip(args, params):
                        match pattern:
                            case ast.BindingPattern(var=var):
                                check_binding_pattern(checker, arm, ty, var)
                            case _:
                                check_pattern(checker, arm, ty)
                case _:
                    tycheck.unreachable("Unhandled ADT sym")
            arm.pattern.eval_type = sym.uniao
            arm.pattern.cons = VariantCons(
                sym.tag, sym.uniao, sym.qualified_name(), sym.params
            )
        case ast.IntPattern():
            arm.pattern.eval_type = Builtins.Int
        case ast.BindingPattern(var=var):
            check_binding_pattern(checker, arm, target_ty, var)
        case _:
            tycheck.unreachable("Unhandled pattern type")
    if arm.pattern.eval_type != target_ty:
        checker.error(
            Errors.INVALID_PATTERN_TYPE,
            expected=target_ty,
            received=arm.pattern.eval_type,
        )


def check_arm(checker: Checker, iguala: ast.Iguala, arm: ast.IgualaArm):
    # 1. Check pattern
    arm.body.symbols = symbols.Scope(checker.ctx_scope)
    check_pattern(checker, arm, iguala.target.eval_type)
