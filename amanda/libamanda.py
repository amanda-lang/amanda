import ctypes
from amanda.config import LIB_AMA


# TODO: Use a struct to represent the module instead of using
# BSON
def run_module(module_bin: bytes) -> int:
    lib_ama = ctypes.CDLL(LIB_AMA)
    count = len(module_bin)
    # Note: Using ubyte to guarantee that arg 1 is an array of bytes
    # on all platforms
    ByteArray = ctypes.c_uint8 * count
    bin_arr = ByteArray(*bytearray(module_bin))
    return lib_ama.run_module(ctypes.byref(bin_arr), ctypes.c_int32(count))
