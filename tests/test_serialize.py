from unittest import TestCase

from amanda.compiler.bindump import dumps, into_bson_int32, into_int32


class TestSerialize(TestCase):
    def test_string(self):
        doc = {"name": "João Boris"}
        ser_doc = dumps(doc)
        print("STRING_FIELD: ", [int(byte) for byte in ser_doc])

    def test_dict(self):
        doc = {"user": {"name": "João Boris", "age": 28, "balance": 1000.52}}
        ser_doc = dumps(doc)
        print("DOC_FIELD: ", [int(byte) for byte in ser_doc])

    def test_array(self):
        doc = {"names": ["João Boris", "Some other dude"]}
        ser_doc = dumps(doc)
        print("ARRAY: ", [int(byte) for byte in ser_doc])

    def test_bytes(self):
        doc = {"bytes": bytes([0, 1, 1, 2, 3, 255])}
        ser_doc = dumps(doc)
        print("BYTES: ", [int(byte) for byte in ser_doc])

    def test_i64(self):
        doc = {"age": 100}
        ser_doc = dumps(doc)
        print("I64: ", [int(byte) for byte in ser_doc])

    def test_f64(self):
        doc = {"credit": 100.50}
        ser_doc = dumps(doc)
        print("F64: ", [int(byte) for byte in ser_doc])
