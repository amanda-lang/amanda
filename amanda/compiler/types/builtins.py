from typing import ClassVar, cast
from amanda.compiler.types.core import Primitive, Registo, Types
from amanda.compiler.symbols.base import Type, TypeVar
from amanda.compiler.symbols.core import Scope, VariableSymbol, MethodSym


class Builtins:
    Int = Primitive(Types.TINT, True)
    Real = Primitive(Types.TREAL, True)
    Bool = Primitive(Types.TBOOL, True)
    Texto = Primitive(Types.TTEXTO, True)
    Vazio = Primitive(Types.TVAZIO, False)
    Indef = Primitive(Types.TINDEF, False)
    Nulo = Primitive(Types.TNULO, False)
    Unknown = Primitive(Types.TUNKNOWN, False)


class SrcBuiltins:
    Opcao: ClassVar[Registo]

    @classmethod
    def init_embutidos(cls, global_ctx: Scope):
        """
        Initialize builtins declared in code.
        """

        cls.Opcao = cast(Registo, global_ctx.symbols["Opcao"])
        assert cls.Opcao.ty_params, "Opcao should have a single type param"
        assert (
            len(cls.Opcao.ty_params) == 1
        ), "Opcao should have a single type param."


builtin_types: list[tuple[str, Type]] = [
    ("int", Builtins.Int),
    ("real", Builtins.Real),
    ("bool", Builtins.Bool),
    ("texto", Builtins.Texto),
    ("vazio", Builtins.Vazio),
    ("indef", Builtins.Indef),
    ("nulo", Builtins.Nulo),
]
