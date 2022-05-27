import amanda.compiler.symbols as symbols
from amanda.compiler.type import Kind, Type
import enum
import pathlib


class BuiltinFn(enum.Enum):
    VEC = "vec"
    TAM = "tam"
    ANEXA = "anexa"
    REMOVA = "remova"

    def __str__(self) -> str:
        return f"{self.value}"


BUILTINS = {key.lower(): value for key, value in BuiltinFn.__members__.items()}
