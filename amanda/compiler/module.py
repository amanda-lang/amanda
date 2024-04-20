from dataclasses import dataclass
from typing import Any


@dataclass
class Module:
    fpath: str
    ast: Any = None
    loaded: bool = False
    builtin: bool = False
    compiled: bool = False
