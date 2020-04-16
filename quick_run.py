import unittest
from interpreter.lexer import Lexer
from interpreter.tests.test_lexer import LexerTestCase
from interpreter.parser import Parser
from io import StringIO
TEST_FILE = "./docs/hello_world.pts"


def run_lexer():
    lexer = Lexer(TEST_FILE)
    token = lexer.get_token()
    while token.token != Lexer.EOF:
        print(token)
        token = lexer.get_token()


def run_tests():
    unittest.main()


def run_parser():
    lexer = Lexer(TEST_FILE)
    parser = Parser(lexer)
    parser.parse().visit()



#run_parser()
run_tests()
#run_lexer()
