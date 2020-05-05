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
ARRAY = join(TEST_DIR,"array")
ASSIGNMENT = join(TEST_DIR,"assignment")
DECLARATION = join(TEST_DIR,"declaration")
EXPRESSION = join(TEST_DIR,"expression")
FUNCTION = join(TEST_DIR,"function")
STATEMENT = join(TEST_DIR,"statement")
ENQUANTO = join(STATEMENT,"enquanto")
MOSTRA = join(STATEMENT,"mostra")
PARA = join(STATEMENT,"para")
RETORNA = join(STATEMENT,"retorna")
SE = join(STATEMENT,"se")


#utility to run the test programs
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





class TestPTI(unittest.TestCase):


    def setUp(self):
        self.buffer = StringIO()


    def test_array(self):
        results = join(ARRAY,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(ARRAY):
            for file in sorted(files):
                if join(ARRAY,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Array test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()


    @unittest.expectedFailure
    def test_assignment(self):
        for test in assign_tests:
            with open(test[0],"r") as file:
                run_script(file,self.buffer)
            self.assertEqual(self.buffer.getvalue(),test[1],f"Assignment test failure. file: {test[0]}")
            self.buffer = StringIO()




if __name__ == "__main__":
    unittest.main()
