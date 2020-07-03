import unittest
import os
import os.path
from io import StringIO
from amanda.pyamanda import Interpreter
from tools.util import run_program
import amanda.error as error

join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
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
CALL = join(TEST_DIR,"call")
GET = join(TEST_DIR,"get")
SET = join(TEST_DIR,"set")
EU = join(TEST_DIR,"eu")
SUPER = join(TEST_DIR,"super")
COMMENT = join(TEST_DIR,"comment")
EXCLUDED = ("lexer.py","parser.py","result.txt")

DIRS = [
ASSIGNMENT,
DECLARATION,
EXPRESSION,
FUNCTION,
ENQUANTO,
MOSTRA,
PARA,
RETORNA,
SE,
CLASS,
OPERATOR,
CALL,
GET,
SET,
EU,
SUPER,
COMMENT,
]




def run_tests(backend):
    ''' Convenience method for running
    test cases.
    '''
    passed = 0
    failed = 0
    failed_tests = []
    #Run test files in each test_directors
    for suite in DIRS:
        with open(join(suite,"result.txt"),"r") as res_file:
            for root,dirs,files in os.walk(suite):
                for file in sorted(files):
                    if file in EXCLUDED:
                        continue
                    test_case = join(root,file)
                    with open(test_case,"r") as script:
                        output = run_program(script,backend)
                    expected = res_file.readline().strip()
                    if output.strip() == expected:
                        passed += 1
                    else:
                        failed += 1
                        failed_tests.append(test_case)
    print("Tests have finished running.")
    print(f"Total:{passed + failed}",f"Passed:{passed}",f"Failed:{failed}")
    if len(failed_tests) > 0:
        print("Failed tests:")
        for name in failed_tests:
            print(name)

if __name__ == "__main__":
    run_tests(Interpreter)
