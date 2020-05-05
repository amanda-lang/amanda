import sys
import time
from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.semantic import Analyzer
from interpreter.pypti import Interpreter
import interpreter.error as ERR
from io import StringIO

TEST_FILE = "./tests/assignment/type_inc_error.pts"


def run_lexer():
    lexer = Lexer(TEST_FILE)
    token = lexer.get_token()
    while token.token != Lexer.EOF:
        print(token)
        token = lexer.get_token()


def run_parser():
    lexer = Lexer(TEST_FILE)
    parser = Parser(lexer)
    parser.parse().visit()


def run_sem_analysis():
    lexer = Lexer(TEST_FILE)
    parser = Parser(lexer)
    intp = Analyzer(parser)
    intp.check_program()
    print(intp.current_scope)

def run_pypti():
    buffer = StringIO()
    with open(TEST_FILE,"r") as file:
        try:
            analyzer = Analyzer(Parser(Lexer(file)))
            analyzer.check_program()
        except ERR.Error as e:
            message = str(e).lower().strip()
            buffer.write(message)
            print(buffer.getvalue())
            sys.exit()
    intp = Interpreter(analyzer.program,output=buffer)
    start = time.time()
    intp.interpret()
    print(buffer.getvalue())
    #print(intp.memory)
run_pypti()
