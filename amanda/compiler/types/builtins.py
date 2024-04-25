from typing import ClassVar, cast
from amanda.compiler.module import Module
from amanda.compiler.types.core import Primitive, Registo, Types
from amanda.compiler.symbols.base import Type, TypeVar
from amanda.compiler.symbols.core import Scope, VariableSymbol, MethodSym
from amanda.config import STD_LIB
import os.path as path

builtin_module = Module(path.join(STD_LIB, "embutidos.ama"))


class Builtins:
    Int = Primitive(builtin_module, Types.TINT, True)
    Real = Primitive(builtin_module, Types.TREAL, True)
    Bool = Primitive(builtin_module, Types.TBOOL, True)
    Texto = Primitive(builtin_module, Types.TTEXTO, True)
    Vazio = Primitive(builtin_module, Types.TVAZIO, False)
    Indef = Primitive(builtin_module, Types.TINDEF, False)
    Nulo = Primitive(builtin_module, Types.TNULO, False)
    Unknown = Primitive(builtin_module, Types.TUNKNOWN, False)


class SrcBuiltins:
    """
    Builtins declared in code
    """

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
