import unittest
import os
import os.path
from io import StringIO
from amanda.lexer import Lexer
from amanda.parser import Parser
from amanda.semantic import Analyzer
from amanda.pypti import Interpreter
import amanda.error as error


join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
RESULTS_FILE = "result.txt"


def run_script(src,output):
    intp = Interpreter(src,True)
    try:
        intp.run()
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
