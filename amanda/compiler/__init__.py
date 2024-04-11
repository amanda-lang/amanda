from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from dataclasses import dataclass
from typing import Optional

if TYPE_CHECKING:
    from amanda.compiler.ast import Program


@dataclass
class Module:
    fpath: str
    ast: Optional[Program] = None
    loaded: bool = False


class Symbol:
    def __init__(self, name: str):
        self.name = name
        self.out_id = name  # symbol id in compiled source program
        self.is_property = False  # Avoid this repitition
        self.is_global = False

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.out_id})>"

    def can_evaluate(self) -> bool:
        return False

    def is_type(self) -> bool:
        return False

    def is_callable(self) -> bool:
        return False
