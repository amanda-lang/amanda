from dataclasses import dataclass
from typing import Any
from os import path


@dataclass
class Module:
    fpath: str
    ast: Any = None
    loaded: bool = False
    builtin: bool = False
    compiled: bool = False

    def __str__(self) -> str:
        _, tail = path.split(self.fpath)
        return f"{tail}"
