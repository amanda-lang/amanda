import unittest
import os
from lexer import Lexer
from tokens import TokenType,Token

class LexerTestCase(unittest.TestCase):

    def setUp(self):
        self.test_file = open("sample.pts","w")
    def tearDown(self):
        os.remove("sample.pts")

    def test_logic_operators(self):
        self.test_file.write(">\n<\n<=\n>=\n!=\n==\n=")
        self.test_file.close()
        lexer = Lexer("sample.pts")
        self.assertEqual(lexer.get_next_token().token,TokenType.GREATER,msg="GREATER Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.LESS,msg="LESS Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.LESSEQ,msg="LESSEQ Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.GREATEREQ,msg="GREATEREQ Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.NOTEQUAL,msg="NOTEQUAL Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.DOUBLEEQUAL,msg="DOUBLEEQUAL Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.EQUAL,msg="EQUAL Test Failed")

    def test_arit_operators(self):
        self.test_file.write("+\n-\n*\n/\n%")
        self.test_file.close()
        lexer = Lexer("sample.pts")
        self.assertEqual(lexer.get_next_token().token,TokenType.PLUS,msg="PLUS Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.MINUS,msg="MINUS Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.STAR,msg="STAR Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.SLASH,msg="SLASH Test Failed")
        self.assertEqual(lexer.get_next_token().token,TokenType.MODULO,msg="MODULO Test Failed")


    def test_number(self):
        self.test_file.write("3242131\n234.21234")
        self.test_file.close()
        lexer = Lexer("sample.pts")
        token = lexer.get_next_token()
        self.assertEqual(token.token,TokenType.INTEGER,msg="INTEGER Test Failed")
        self.assertEqual(int(token.lexeme),3242131,msg="INTEGER Test Failed")
        token = lexer.get_next_token()
        self.assertEqual(token.token,TokenType.DECIMAL,msg="REAL Test Failed")
        self.assertEqual(float(token.lexeme),234.21234,msg="REAL Test Failed")


    def test

runner = unittest.TextTestRunner()
runner.run(LexerTestCase("test_number"))
