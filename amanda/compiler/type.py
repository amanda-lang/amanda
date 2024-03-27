from __future__ import annotations
from amanda.compiler.symbols import Symbol, VariableSymbol, MethodSym
from enum import auto, IntEnum, Enum
from dataclasses import dataclass
from typing import cast, List, Tuple, Dict, Optional


# Tag to indicate which type a Type object represents
class Kind(IntEnum):
    TINT = 0
    TREAL = auto()
    TBOOL = auto()
    TTEXTO = auto()
    TINDEF = auto()
    TVAZIO = auto()
    TVEC = auto()
    TREGISTO = auto()
    TNULO = auto()
    # unknown is a type used as a default type value
    # to avoid setting eval_type to null on ast nodes
    TUNKNOWN = auto()
    TGENERIC = auto()
    # Special type to represent nullable values
    TTalvez = auto()

    def __str__(self) -> str:
        if self == Kind.TTalvez:
            return "Talvez"
        return self.name.lower()[1:]


@dataclass
class Type(Symbol):
    def __init__(
        self,
        kind: Kind,
        zero_initialized: bool = False,
        is_generic: bool = False,
    ):
        super().__init__(str(kind), None)
        self.zero_initialized = zero_initialized
        self.kind = kind
        self.is_global = True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return False
        return self.kind == other.kind

    def is_numeric(self) -> bool:
        return self.kind == Kind.TINT or self.kind == Kind.TREAL

    def is_type(self) -> bool:
        return True

    def is_generic(self) -> bool:
        return False

    def __str__(self) -> str:
        return str(self.kind)

    def is_operable(self) -> bool:
        return self.kind != Kind.TVAZIO and self.kind != Kind.TINDEF

    def full_field_path(self, field: str) -> str:
        return self.name + "::" + field

    def check_cast(self, other: Type) -> bool:
        # Allowed conversions:
        # int -> real, bool,real,texto,indef
        # real -> int, bool,real,texto,indef
        # *bool -> texto,indef
        # texto -> int,real,bool,indef
        # indef -> int,real,bool,texto
        kind = self.kind
        other_kind = other.kind

        if kind == other_kind:
            return True

        primitives = (
            Kind.TINT,
            Kind.TTEXTO,
            Kind.TBOOL,
            Kind.TREAL,
            Kind.TINDEF,
        )
        cast_table = {
            Kind.TINT: primitives,
            Kind.TREAL: primitives,
            Kind.TTEXTO: primitives,
            Kind.TBOOL: (Kind.TTEXTO, Kind.TINDEF),
            Kind.TVEC: (Kind.TINDEF,),
            Kind.TREGISTO: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TTalvez,),
            Kind.TINDEF: (*primitives, Kind.TREGISTO, Kind.TVEC),
        }
        cast_types = cast_table.get(kind)

        if not cast_types or other_kind not in cast_types:
            return False

        return True

    def promote_to(self, other: Type) -> Optional[Type]:
        kind = self.kind
        other_kind = other.kind

        auto_cast_table = {
            Kind.TINT: (Kind.TREAL, Kind.TINDEF),
            Kind.TREAL: (Kind.TINDEF,),
            Kind.TBOOL: (Kind.TINDEF,),
            Kind.TTEXTO: (Kind.TINDEF,),
            Kind.TVEC: (Kind.TINDEF,),
            Kind.TREGISTO: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TTalvez,),
        }
        auto_cast_types = auto_cast_table.get(kind)

        if not auto_cast_types or other_kind not in auto_cast_types:
            # If not of type Talvez, return
            if other_kind != Kind.TTalvez or not isinstance(
                other, ConstructedTy
            ):
                return None

            inner_ty = other.bound_ty_args["T"]
            if inner_ty != self and not self.promote_to(inner_ty):
                return None

        return other

    def supports_fields(self) -> bool:
        return False

    def supports_methods(self) -> bool:
        return True

    def get_property(self, prop: str) -> Symbol | None:
        pass

    def is_primitive(self) -> bool:
        return self.kind in (
            Kind.TINT,
            Kind.TTEXTO,
            Kind.TBOOL,
            Kind.TREAL,
            Kind.TINDEF,
        )

    def bind(self, **ty_args: dict[str, Type]) -> ConstructedTy:
        raise NotImplementedError(
            "Bind must be implemented for types that support generics"
        )


class Vector(Type):
    def __init__(self, element_type: Type):
        super().__init__(Kind.TVEC)
        self.element_type: Type = element_type

    def get_type(self) -> Type:
        if self.element_type.kind != Kind.TVEC:
            return self.element_type

        el_type = cast(Vector, self).element_type
        while el_type.kind != Kind.TVEC:
            el_type = cast(Vector, el_type).element_type
        return el_type

    def __str__(self) -> str:
        return f"[{str(self.element_type)}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.element_type == other.element_type


class Registo(Type):
    def __init__(
        self,
        name: str,
        fields: Dict[str, Symbol],
        ty_params: set[str] | None = None,
    ):
        super().__init__(Kind.TREGISTO)
        self.name = name
        self.fields = fields
        self.methods: dict[str, Symbol] = {}
        self.ty_params: set[str] | None = ty_params

    def is_callable(self) -> bool:
        return True

    def is_generic(self) -> bool:
        return self.ty_params is not None

    def bind(self, **ty_args) -> ConstructedTy:
        if self.ty_params is None:
            raise NotImplementedError(
                "Cannot bind type params of non generic Registo"
            )
        for ty_arg in ty_args:
            if ty_arg not in self.ty_params:
                raise ValueError(f"Invalid type argument: {ty_arg}")
        return ConstructedTy(self, ty_args)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Type):
            return False
        if not self.kind == other.kind:
            return False
        return self.name == cast(Registo, other).name

    def __str__(self) -> str:
        return self.name

    def get_property(self, prop) -> Symbol | None:
        return self.fields.get(prop, self.methods.get(prop))

    def supports_fields(self) -> bool:
        return True


@dataclass
class ConstructedTy(Type):
    generic_ty: Type
    bound_ty_args: dict[str, Type]

    def __init__(self, generic_ty, bound_ty_args):
        super().__init__(generic_ty.kind)
        self.generic_ty = generic_ty
        self.bound_ty_args = bound_ty_args

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConstructedTy):
            return False
        if self.kind != other.kind:
            return False
        if self.generic_ty != other.generic_ty:
            return False
        # Compare bound type arguments
        for ty_param, ty_arg in self.bound_ty_args.items():
            other_ty_arg = other.bound_ty_args.get(ty_param)
            if not other_ty_arg:
                return False
            if other_ty_arg != ty_arg:
                return False
        return True

    def __str__(self) -> str:
        if self.name == str(Kind.TTalvez):
            ty_arg = self.bound_ty_args["T"]
            return f"{ty_arg}?"
        return self.name


class Builtins(Enum):
    Int = Type(Kind.TINT)
    Real = Type(Kind.TREAL)
    Bool = Type(Kind.TBOOL)
    Texto = Type(Kind.TTEXTO)
    Vazio = Type(Kind.TVAZIO)
    Indef = Type(Kind.TINDEF)
    Nulo = Type(Kind.TNULO)
    Talvez = Registo(
        str(Kind.TTalvez),
        fields={
            "valor": VariableSymbol("valor", TypeParam("T")),
        },
        ty_params={"T"},
    )


Builtins.Talvez.value.fields["valor_ou"] = MethodSym(
    "valor_ou",
    Builtins.Talvez.value,
    TypeParam("T"),
    params={"padrao": VariableSymbol("padrao", TypeParam("T"))},
)


builtin_types: List[Tuple[str, Type]] = [
    ("int", Type(Kind.TINT, True)),
    ("real", Type(Kind.TREAL, True)),
    ("bool", Type(Kind.TBOOL, True)),
    ("texto", Type(Kind.TTEXTO, True)),
    ("vazio", Type(Kind.TVAZIO)),
    ("indef", Type(Kind.TINDEF)),
    ("nulo", Type(Kind.TNULO)),
]
