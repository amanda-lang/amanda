from amanda.compiler.symbols import Symbol
from enum import auto, IntEnum

# Describes the kind of a type
class Kind(IntEnum):
    TINT = 0
    TREAL = auto()
    TBOOL = auto()
    TTEXTO = auto()
    TINDEF = auto()
    TVAZIO = auto()
    TLISTA = auto()
    TKLASS = auto()
    TNULO = auto()

    def __str__(self):
        return self.name.lower()[1:]

    def cast_to(self, other):
        pass


class Type(Symbol):
    def __init__(self, kind):
        super().__init__(str(kind), None)
        self.kind = kind
        self.is_global = True

    def __eq__(self, other):
        if not isinstance(other, Type):
            return False
        return self.kind == other.kind

    def is_numeric(self):
        return self.kind == Kind.TINT or self.kind == Kind.TREAL

    def is_type(self):
        return True

    def __str__(self):
        return str(self.kind)

    def is_operable(self):
        return self.kind != Kind.TVAZIO and self.kind != Kind.TINDEF

    def check_cast(self, other) -> bool:
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
            Kind.TLISTA: (Kind.TINDEF,),
            Kind.TKLASS: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TKLASS,),
            Kind.TINDEF: (*primitives, Kind.TKLASS, Kind.TLISTA),
        }
        cast_types = cast_table.get(kind)

        if not cast_types or other_kind not in cast_types:
            return False

        return True

    def promote_to(self, other):
        kind = self.kind
        other_kind = other.kind

        auto_cast_table = {
            Kind.TINT: (Kind.TREAL, Kind.TINDEF),
            Kind.TREAL: (Kind.TINDEF,),
            Kind.TBOOL: (Kind.TINDEF,),
            Kind.TTEXTO: (Kind.TINDEF,),
            Kind.TLISTA: (Kind.TINDEF,),
            Kind.TKLASS: (Kind.TINDEF,),
            Kind.TNULO: (Kind.TKLASS,),
        }
        auto_cast_types = auto_cast_table.get(kind)

        if not auto_cast_types or other_kind not in auto_cast_types:
            return None

        return other


class Lista(Type):
    def __init__(self, subtype):
        super().__init__(Kind.TLISTA)
        self.subtype = subtype

    def get_type(self):
        subtype = self.subtype
        while type(subtype) == Lista:
            subtype = subtype.subtype
        return subtype

    def __str__(self):
        return f"[]{self.subtype}"

    def __eq__(self, other):
        if type(other) != Lista:
            return False
        return self.subtype == other.subtype


class Klass(Type):
    def __init__(self, name, members):
        super().__init__(Kind.TKLASS)
        self.name = name
        self.out_id = name
        self.members = members
        self.constructor = None
        self.is_global = False

    def __str__(self):
        return self.name
