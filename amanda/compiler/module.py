from dataclasses import dataclass
from typing import Any, TYPE_CHECKING


@dataclass
class Module:
    fpath: str
    ast: Any = None
    loaded: bool = False
