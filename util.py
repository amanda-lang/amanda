import unittest
import os
import os.path
from io import StringIO
from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.semantic import Analyzer
from interpreter.pypti import Interpreter
import interpreter.error as error


join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
RESULTS_FILE = "result.txt"


def run_script(file,output):
    try:
        analyzer = Analyzer(Parser(Lexer(file)))
        analyzer.check_program()
    except error.Error as e:
        message = str(e).lower().strip()
        output.write(message)
        return
    intp = Interpreter(analyzer.program,output=output)
    try:
        intp.interpret()
    except SystemExit:
        pass


def delete_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        result = join(root,RESULTS_FILE)
        try:
            os.remove(result)
        except FileNotFoundError:
            pass

def get_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        for file in sorted(files):
            filename = join(root,file)
            with open(join(root,RESULTS_FILE),"a") as result, open(filename,"r") as src:
                buffer = StringIO()
                run_script(src,buffer)
                result.write(buffer.getvalue()+"\n")


#delete_script_output()
get_script_output()
