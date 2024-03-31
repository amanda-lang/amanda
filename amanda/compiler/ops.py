from typing import TYPE_CHECKING
from amanda.compiler.symbols.base import Type
from amanda.compiler.tokens import TokenType as TT
from amanda.compiler.types.builtins import Builtins

# HACK: to get around cyclic imports
from amanda.compiler.types.core import Primitive, Types


def primitive_binop(lhs_type: Primitive, op: TT, rhs_type: Type) -> Type | None:
    # Get result type of a binary operation based on
    # on operator and operand type

    if not rhs_type.is_operable():
        return None

    if not isinstance(rhs_type, Primitive):
        return None

    match op:
        case (
            TT.PLUS | TT.MINUS | TT.STAR | TT.SLASH | TT.DOUBLESLASH | TT.MODULO
        ):
            if lhs_type.is_numeric() and rhs_type.is_numeric():
                return (
                    Builtins.Int
                    if lhs_type.tag == Types.TINT
                    and rhs_type.tag == Types.TINT
                    and op != TT.SLASH
                    else Builtins.Real
                )
        case TT.GREATER | TT.LESS | TT.GREATEREQ | TT.LESSEQ:
            if lhs_type.is_numeric() and rhs_type.is_numeric():
                return Builtins.Bool
        case TT.DOUBLEEQUAL | TT.NOTEQUAL:
            if (
                (lhs_type.is_numeric() and rhs_type.is_numeric())
                or lhs_type == rhs_type
                or lhs_type.promote_to(rhs_type)
                or rhs_type.promote_to(lhs_type)
            ):
                return Builtins.Bool
        case TT.E | TT.OU:
            if lhs_type.tag == Types.TBOOL and rhs_type.tag == Types.TBOOL:
                return Builtins.Bool
        case _:
            return None
