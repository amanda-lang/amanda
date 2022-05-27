import sys
import os
from pathlib import Path
from os import path

BUNDLED = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

if not BUNDLED:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    VM_ROOT = path.join(PROJECT_ROOT, "amanda/vm/")
    VM_CONFIG = path.join(VM_ROOT, "Cargo.toml")
    # Path to std lib
    STD_LIB = path.join(PROJECT_ROOT, "std")
    # Choose dynlib extension
    if sys.platform == "win32":
        ext = "dll"
    elif sys.platform == "linux":
        ext = "so"
    else:
        raise NotImplemented(
            f"Extension for {sys.platform} has not yet been implemeneted"
        )
    # Path to vm output
    LIB_OUT_DIR = (
        f"target/release/libamanda.{ext}"
        if os.getenv("PYINST_BUILD")
        else f"target/debug/libamanda.{ext}"
    )
    LIB_AMA = path.join(VM_ROOT, LIB_OUT_DIR)
else:
    BUNDLE_ROOT = sys._MEIPASS
    # Path to vm project
    LIB_AMA = path.join(BUNDLE_ROOT, "deps/libamanda.so")
    STD_LIB = path.join(BUNDLE_ROOT, "std")
