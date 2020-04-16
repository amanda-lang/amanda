import unittest
from interpreter.parser import Parser
from interpreter.lexer import Lexer
from interpreter.tokens import TokenType,Token
from io import StringIO


#buffer = StringIO("")



class ParserTestCase(unittest.TestCase):
    def setUp(self):
        self.buffer = StringIO()

    def tearDown(self):
        self.buffer = None

    def test_declaration(self):
        phrases = [ "decl int a;","declara real a1;","declara bool a2;",
            "declara real a3;", "decl real troco = 3.14;",
            "vector int array[2+1];","vector string array[(-(-2))+2];"
        ]
        self.buffer.writelines(phrase)
        parser = Parser(Lexer(self.buffer))
        try:
