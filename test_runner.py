import unittest
import os
import os.path
from io import StringIO
from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.semantic import Analyzer
from interpreter.pypti import Interpreter


#test_path
TEST_DIR = os.path.abspath("./tests")
ARRAY = os.path.join(TEST_DIR,"array")
ASSIGNMENT = os.path.join(TEST_DIR,"assignment")
DECLARATION = os.path.join(TEST_DIR,"declaration")
EXPRESSION = os.path.join(TEST_DIR,"expression")
FUNCTION = os.path.join(TEST_DIR,"function")
STATEMENT = os.path.join(TEST_DIR,"statement")
ENQUANTO = os.path.join(ASSIGNMENT,"enquanto")
MOSTRA = os.path.join(ASSIGNMENT,"mostra")
PARA = os.path.join(ASSIGNMENT,"para")
RETORNA = os.path.join(ASSIGNMENT,"retorna")
SE = os.path.join(ASSIGNMENT,"se")
#utility to run the test programs
def run_script(file,output):
    analyzer = Analyzer(Parser(Lexer(file)))
    analyzer.check_program()
    intp = Interpreter(analyzer.program,ouput=output)
    intp.interpret()





class TestPTI(unittest.TestCase):


    def setUp(self):
        self.buffer = StringIO()


    def test_array(self):
        pass
