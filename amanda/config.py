from pathlib import Path
from os import path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Path to std lib
STD_LIB = path.join(PROJECT_ROOT, "std")

# Path to vm project
VM_CONFIG_PATH = path.join(PROJECT_ROOT, "amanda/vm/Cargo.toml")
LIB_AMANDA_PATH = path.join(PROJECT_ROOT, "amanda/vm/target/debug/libamanda.so")
