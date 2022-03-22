from unittest import TestCase

from amanda.compiler.bindump import dumps, into_bson_int32, into_int32


class TestSerialize(TestCase):
    def test_string(self):
        doc = {"name": "Sténio Alexandre"}
        ser_doc = dumps(doc)
        print(ser_doc)

    def test_dict(self):
        doc = {"user": {"name": "Sténio Alexandre"}}
        ser_doc = dumps(doc)
        print("DICT: ", ser_doc)

    def test_array(self):
        doc = {"names": ["Sténio Alexandre", "Some other dude"]}
        ser_doc = dumps(doc)
        print("ARRAY: ", ser_doc)

    def test_bytes(self):
        doc = {"bytes": bytes([0, 1, 1, 2, 3])}
        ser_doc = dumps(doc)
        print(ser_doc)

    def test_f64(self):
        doc = {"credit": 100.50}
        ser_doc = dumps(doc)
        print(ser_doc)
