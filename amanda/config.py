import sys
import os
from pathlib import Path
from os import path

BUNDLED = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

if sys.platform == "win32":
    lib_name = "amanda.dll"
elif sys.platform == "linux":
    lib_name = "libamanda.so"
else:
    raise NotImplemented(
        f"Extension for {sys.platform} has not yet been implemeneted"
    )
if not BUNDLED:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
    VM_ROOT = path.join(PROJECT_ROOT, "amanda/vm/")
    VM_CONFIG = path.join(VM_ROOT, "Cargo.toml")
    # Path to std lib
    STD_LIB = path.join(PROJECT_ROOT, "std")
    # Choose dynlib extension
    # Path to vm output
    LIB_OUT_DIR = (
        f"target/release/{lib_name}"
        if os.getenv("PYINST_BUILD")
        else f"target/debug/{lib_name}"
    )
    LIB_AMA = path.join(VM_ROOT, LIB_OUT_DIR)
else:
    BUNDLE_ROOT = sys._MEIPASS
    # Path to vm project
    LIB_AMA = path.join(BUNDLE_ROOT, f"deps/{lib_name}")
    STD_LIB = path.join(BUNDLE_ROOT, "std")
