import unittest
from interpreter.lexer import Lexer
from interpreter.tests.test_lexer import LexerTestCase

TEST_FILE = "./interpreter/test.pts"


def run_lexer():
    lexer = Lexer(TEST_FILE)
    token = lexer.get_token()
    while token.token != Lexer.EOF:
        print(token)
        token = lexer.get_next_token()


def run_tests():
    unittest.main()



run_tests()
