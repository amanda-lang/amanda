from __future__ import annotations
from amanda.compiler.symbols import Symbol
from enum import auto, IntEnum
from dataclasses import dataclass
from typing import cast, List, Tuple, Optional

# Describes the kind of a type
class Kind(IntEnum):
    TINT = 0
    TREAL = auto()
    TBOOL = auto()
    TTEXTO = auto()
    TINDEF = auto()
    TVAZIO = auto()
    TVEC = auto()
    TKLASS = auto()
    TNULO = auto()

    def __str__(self) -> str:
        return self.name.lower()[1:]


@dataclass
class Type(Symbol):
    def __init__(self, kind: Kind):
        super().__init__(str(kind), None)
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

    def __str__(self) -> str:
        return str(self.kind)

    def is_operable(self) -> bool:
        return self.kind != Kind.TVAZIO and self.kind != Kind.TINDEF

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
            Kind.TKLASS: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TKLASS,),
            Kind.TINDEF: (*primitives, Kind.TKLASS, Kind.TVEC),
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
            Kind.TKLASS: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TKLASS,),
        }
        auto_cast_types = auto_cast_table.get(kind)

        if not auto_cast_types or other_kind not in auto_cast_types:
            return None

        return other


class Vector(Type):
    def __init__(self, element_type: Type):
        super().__init__(Kind.TVEC)
        self.element_type: Type = element_type

    def get_type(self) -> Type:
        if self.element_type.kind != Kind.TVEC:
            return self.element_type

        el_type = cast(Vector, self).element_type
        while el_type.kind != Kind.TVEC:
            subtype = cast(Vector, el_type).element_type
        return el_type

    def __str__(self) -> str:
        return f"[{str(self.element_type)}]"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vector):
            return False
        return self.element_type == other.element_type


class Klass(Type):
    pass


builtin_types: List[Tuple[str, Type]] = [
    ("int", Type(Kind.TINT)),
    ("real", Type(Kind.TREAL)),
    ("bool", Type(Kind.TBOOL)),
    ("texto", Type(Kind.TTEXTO)),
    ("vazio", Type(Kind.TVAZIO)),
    ("indef", Type(Kind.TINDEF)),
    ("nulo", Type(Kind.TNULO)),
]
