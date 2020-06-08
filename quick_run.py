import sys
import time
from amanda.lexer import Lexer
from amanda.parser import Parser
from amanda.semantic import Analyzer
from amanda.pyamanda import Interpreter
import amanda.error as ERR
from io import StringIO

TEST_FILE = "./test.ama"


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
    file = open(TEST_FILE) 
    parser = Parser(file)
    intp = Analyzer(file)
    intp.check_program(parser.parse())
    file.close()
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

run_sem_analysis()
