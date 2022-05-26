from io import BytesIO
import struct
from typing import Dict, Any, Sized, List, cast


def into_bson_int32(number: int) -> bytes:
    return struct.pack("<l", number)


def into_bson_int64(number: int) -> bytes:
    return struct.pack("<q", number)


def into_bson_f64(bson_float: float) -> bytes:
    return struct.pack("<d", bson_float)


def into_int32(bson_int: bytes) -> int:
    return cast(int, struct.unpack("<l", bson_int)[0])


def bson_int32_len(obj: Sized) -> bytes:
    if len(obj) >= 2 ** (31):
        raise OverflowError(
            f"Object too large to be bsonyfied. Object size: {len(obj)}"
        )
    return into_bson_int32(len(obj))


def dump_value(buf: BytesIO, type_code: bytes, *args: bytes) -> None:
    buf.write(type_code)
    for arg in args:
        buf.write(arg)


def dumps(data: Dict[str, Any]) -> bytes:
    """
    Converts bytecode ops and extra metadata into the BSON format.
    Link to the spec: https://bsonspec.org/spec.html
    """
    document = BytesIO()
    e_list = BytesIO()
    for key, value in data.items():
        val_t = type(value)
        if val_t == float:
            dump_value(
                e_list, b"\x01", key.encode(), b"\x00", into_bson_f64(value)
            )
        elif val_t == str:
            str_bytes = value.encode()
            str_len = bson_int32_len(str_bytes)
            dump_value(
                e_list,
                b"\x02",
                key.encode(),
                b"\x00",
                str_len,
                value.encode(),
                b"\x00",
            )
        elif val_t == dict:
            dump_value(
                e_list,
                b"\x03",
                key.encode(),
                b"\x00",
                dumps(value),
            )
        elif val_t == list:
            arr_obj = {}
            for i, val in enumerate(value):
                arr_obj[str(i)] = val
            dump_value(
                e_list,
                b"\x04",
                key.encode(),
                b"\x00",
                dumps(arr_obj),
            )
        elif val_t == bytes:
            size = len(value)
            dump_value(
                e_list,
                b"\x05",
                key.encode(),
                b"\x00",
                into_bson_int32(size),
                b"\x80",
                value,
            )
        elif val_t == int:
            dump_value(
                e_list, b"\x12", key.encode(), b"\x00", into_bson_int64(value)
            )
        else:
            raise NotImplementedError(f"Cannot serialize type: {str(val_t)}")
    doc_len = bson_int32_len(e_list.getvalue())
    document.write(doc_len)
    document.write(e_list.getvalue())
    document.write(b"\x00")
    doc = document.getvalue()
    document.close()
    e_list.close()
    return doc
