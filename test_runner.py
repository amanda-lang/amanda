import unittest
import os
import os.path
from io import StringIO
from util import run_script
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
OPERATOR = join(TEST_DIR,"operator")

EXCLUDED = ("lexer.py","parser.py","result.txt")



def run_suite(suite,runner,results):
    ''' Convenience method for running
    a test cases.'''
    for root,dirs,files in os.walk(suite):
        for file in sorted(files):
            if file in EXCLUDED:
                continue
            with open(join(root,file),"r") as script:
                output = run_script(script)
            if output.getvalue().strip() != results.readline().strip():
                print(results.readline().strip())
                print(output.getvalue().strip())
                raise Exception(f"Test failed. file: {file}.")
                
    return True

class TestAmanda(unittest.TestCase):

    def setUp(self):
        self.buffer = StringIO()

    @unittest.skip
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


    @unittest.skip
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



    
    @unittest.skip
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


    
    @unittest.skip
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


    
    @unittest.skip
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



    
    @unittest.skip
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


    
    @unittest.skip
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


    
    @unittest.skip
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


    @unittest.skip
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

    
    def test_operator(self):
        with open(join(OPERATOR,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(OPERATOR,self,res_file))




