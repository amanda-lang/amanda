import unittest
import os
import os.path
from io import StringIO
from amanda.pyamanda import Interpreter
from tools.util import run_program
import amanda.error as error

join = os.path.join
TEST_DIR = os.path.abspath("./tests")
STATEMENT = join(TEST_DIR,"statement")
EXCLUDED = ("lexer.py","parser.py","result.txt")

#test paths
DIRS = [
join(TEST_DIR,"assignment"),join(TEST_DIR,"declaration"),
join(TEST_DIR,"expression"),
join(TEST_DIR,"function"),
join(STATEMENT,"enquanto"),
join(STATEMENT,"mostra"),join(STATEMENT,"para"),
join(STATEMENT,"retorna"),join(STATEMENT,"se"),
join(TEST_DIR,"class"),join(TEST_DIR,"operator"),
join(TEST_DIR,"call"),join(TEST_DIR,"get"),
join(TEST_DIR,"set"),join(TEST_DIR,"eu"),
join(TEST_DIR,"super"),join(TEST_DIR,"comment")
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
                    symbol = ""
                    if output.strip() == expected:
                        passed += 1
                        symbol = "."
                    else:
                        failed += 1
                        failed_tests.append(test_case)
                        symbol = "x"
                    print(symbol,end="")
    print("\n\n")
    print("Tests have finished running.")
    print(f"Total:{passed + failed}",f"Passed:{passed}",f"Failed:{failed}")
    if len(failed_tests) > 0:
        print("Failed tests:")
        for name in failed_tests:
            print(name)

if __name__ == "__main__":
    run_tests(Interpreter)
