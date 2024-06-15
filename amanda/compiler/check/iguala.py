import typing
import amanda.compiler.ast as ast
import amanda.compiler.symbols.core as symbols
from amanda.compiler.check.checker import Checker
from amanda.compiler.error import Errors
from amanda.compiler.types.builtins import Builtins
from amanda.compiler.types.core import Variant
import utils.tycheck as tycheck


def check_iguala(checker: Checker, iguala: ast.Iguala):
    target = iguala.target
    checker.visit(target)
    if target.eval_type.can_be_matched()
        checker.error(Errors.VOID_FN_MATCH_TARGET)

    check_arm(checker, iguala, iguala.arms[0])
    for arm in iguala.arms:
        check_arm(checker, iguala, arm)


def check_pattern(checker: Checker, arm: ast.IgualaArm, target_ty: Type):
    match arm.pattern:
        case ast.ADTPattern(adt, args):
            checker.visit(adt)
            sym = tycheck.unwrap(
                adt.symbol if isinstance(adt, ast.Path) else adt.var_symbol
            )
            if not sym.is_callable() and args:
                checker.error(Errors.VARIANT_TAKES_NO_ARGS, variant=sym)
            match sym:
                case Variant(params=params):
                    if target_ty != sym.uniao: 
                        checker.error(Errors.INVALID_PATTERN_TYPE, expected=target_ty, received=sym.uniao)
                    for pattern, ty in zip(args, params):
                        match pattern:
                            case ast.BindingPattern():
                                pattern.eval_type = ty
                            case _:
                                check_pattern(checker, arm, ty)
                case _:
                    tycheck.unreachable("Unhandled ADT sym")
            arm.pattern.eval_type = sym
        case ast.IntPattern(): 
            if target_ty != Builtins.Int: 
                checker.error(Errors.INVALID_PATTERN_TYPE, expected=target_ty, received=Builtins.Int)
        case ast.BindingPattern(): 
            arm.pattern.eval_type = target_ty
        case _: 
            tycheck.unreachable("Unhandled pattern type")


def check_arm(checker: Checker, iguala: ast.Iguala, arm: ast.IgualaArm):
    # 1. Check pattern
    check_pattern(checker, arm, iguala.target.eval_type)
