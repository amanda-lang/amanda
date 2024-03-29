from amanda.compiler.types.core import Primitive, Registo, Types
from amanda.compiler.symbols.base import Type
from amanda.compiler.symbols.core import VariableSymbol, MethodSym


class Builtins:
    Int = Primitive(Types.TINT, True)
    Real = Primitive(Types.TREAL, True)
    Bool = Primitive(Types.TBOOL, True)
    Texto = Primitive(Types.TTEXTO, True)
    Vazio = Primitive(Types.TVAZIO, False)
    Indef = Primitive(Types.TINDEF, False)
    Nulo = Primitive(Types.TNULO, False)
    Opcao = Registo(
        str(Types.TOpcao),
        fields={
            "valor": VariableSymbol("valor", TypeParam("T")),
        },
        ty_params={"T"},
    )


Builtins.Opcao.methods["valor_ou"] = MethodSym(
    "valor_ou",
    Builtins.Opcao,
    TypeParam("T"),
    params={"padrao": VariableSymbol("padrao", TypeParam("T"))},
)


builtin_types: list[tuple[str, Type]] = [
    ("int", Builtins.Int),
    ("real", Builtins.Real),
    ("bool", Builtins.Bool),
    ("texto", Builtins.Texto),
    ("vazio", Builtins.Vazio),
    ("indef", Builtins.Indef),
    ("nulo", Builtins.Nulo),
    ("Opcao", Builtins.Opcao),
]
