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


    def test_assign(self):
        results = join(ASSIGNMENT,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(ASSIGNMENT):
            for file in sorted(files):
                if join(ASSIGNMENT,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Assignment test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()


    def test_declaration(self):
        results = join(DECLARATION,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(DECLARATION):
            for file in sorted(files):
                if join(DECLARATION,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"declaration test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()



    def test_expression(self):
        results = join(EXPRESSION,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(EXPRESSION):
            for file in sorted(files):
                if join(EXPRESSION,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"expression test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()

    def test_function(self):
        results = join(FUNCTION,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(FUNCTION):
            for file in sorted(files):
                if join(FUNCTION,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"function test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()


    def test_enquanto(self):
        results = join(ENQUANTO,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(ENQUANTO):
            for file in sorted(files):
                if join(ENQUANTO,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Enquanto test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()



    def test_mostra(self):
        results = join(MOSTRA,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(MOSTRA):
            for file in sorted(files):
                if join(MOSTRA,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Mostra test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()


    def test_para(self):
        results = join(PARA,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(PARA):
            for file in sorted(files):
                if join(PARA,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Para test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()


    def test_retorna(self):
        results = join(RETORNA,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(RETORNA):
            for file in sorted(files):
                if join(RETORNA,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Retorna test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()

    def test_se(self):
        results = join(SE,"result.txt")
        res_file = open(results,"r")
        for root,dirs,files in os.walk(SE):
            for file in sorted(files):
                if join(SE,file) == results:
                    continue
                with open(join(root,file),"r") as script:
                    run_script(script,self.buffer)
                self.assertEqual(self.buffer.getvalue()
                ,res_file.readline().strip(),
                f"Se test failure. file: {file}")
                self.buffer = StringIO()
                #assert result
        res_file.close()



if __name__ == "__main__":
    unittest.main()
