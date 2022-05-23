import amanda.compiler.symbols as symbols
from amanda.compiler.type import Kind, Type
import enum
import pathlib


class BuiltinFn(enum.Enum):
    VEC = "vec"
    TAM = "tam"
    ANEXA = "anexa"

    def __str__(self) -> str:
        return f"{self.value}"


BUILTINS = {key.lower(): value for key, value in BuiltinFn.__members__.items()}

# HACK: To simplify building list literals, a builtin function
# only available at runtime will be added to the names dict
FN_VEC_FROM_LIT = "vec_from_literal"
