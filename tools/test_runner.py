import unittest
import os
import os.path
from io import StringIO
from tools.util import run_script
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
CLASS = join(TEST_DIR,"class")
OPERATOR = join(TEST_DIR,"operator")
COMMENT = join(TEST_DIR,"comment")

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
                raise Exception(f"Test failed. file: {file}.")
                
    return True

class TestAmanda(unittest.TestCase):

    def test_assign(self):
        with open(join(ASSIGNMENT,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(ASSIGNMENT,self,res_file))


    def test_declaration(self):
        with open(join(DECLARATION,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(DECLARATION,self,res_file))

    
    def test_expression(self):
        with open(join(EXPRESSION,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(EXPRESSION,self,res_file))


    
    def test_function(self):
        with open(join(FUNCTION,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(FUNCTION,self,res_file))

    
    def test_enquanto(self):
        with open(join(ENQUANTO,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(ENQUANTO,self,res_file))
    
    def test_mostra(self):
        with open(join(MOSTRA,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(MOSTRA,self,res_file))
    


    
    def test_para(self):
        with open(join(PARA,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(PARA,self,res_file))

    
    def test_retorna(self):
        with open(join(RETORNA,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(RETORNA,self,res_file))
    
    def test_se(self):
        with open(join(SE,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(SE,self,res_file))

    def test_class(self):
        with open(join(CLASS,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(CLASS,self,res_file))
    
    def test_operator(self):
        with open(join(OPERATOR,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(OPERATOR,self,res_file))

    def test_comment(self):
        with open(join(COMMENT,"result.txt"),"r") as res_file:
            self.assertTrue(run_suite(COMMENT,self,res_file))


