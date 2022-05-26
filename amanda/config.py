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
    # Path to vm output
    LIB_OUT_DIR = (
        "target/release/libamanda.so"
        if os.getenv("PYINST_BUILD")
        else "target/debug/libamanda.so"
    )
    LIB_AMA = path.join(VM_ROOT, LIB_OUT_DIR)
else:
    BUNDLE_ROOT = sys._MEIPASS
    # Path to vm project
    LIB_AMA = path.join(BUNDLE_ROOT, "deps/libamanda.so")
