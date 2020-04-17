import unittest
from interpreter.lexer import Lexer
from interpreter.tests.test_lexer import LexerTestCase
from interpreter.parser import Parser
from interpreter.pt_intp import PTInterpreter
from io import StringIO
import dis
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


def run_sem_analysis():
    lexer = Lexer(TEST_FILE)
    parser = Parser(lexer)
    intp = PTInterpreter(parser)
    intp.load_symbols()

#run_parser()
#run_tests()
#run_lexer()
run_sem_analysis()
