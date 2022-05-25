import ctypes
from amanda.config import LIB_AMANDA_PATH


def run_module(module_bin: bytes) -> int:
    lib_ama = ctypes.CDLL(LIB_AMANDA_PATH)
    count = len(module_bin)
    # Note: Using ubyte to guarantee that arg 1 is an array of bytes
    # on all platforms
    ByteArray = ctypes.c_ubyte * count
    bin_arr = ByteArray(*bytearray(module_bin))
    return lib_ama.run_module(ctypes.byref(bin_arr), count)
