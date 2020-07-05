import os
from io import StringIO
from amanda.pyamanda import Interpreter
from backend.transpiler import Transpiler
from tools.util import run_program
import amanda.error as error

join = os.path.join
TEST_DIR = os.path.abspath("./tests")
STATEMENT = join(TEST_DIR,"statement")
EXCLUDED = ("result.txt")

#test paths
DIRS = [
join(TEST_DIR,"assignment"),join(TEST_DIR,"declaration"),
join(TEST_DIR,"expression"),
join(TEST_DIR,"function"),
join(STATEMENT,"enquanto"),
join(STATEMENT,"mostra"),join(STATEMENT,"para"),
join(STATEMENT,"retorna"),join(STATEMENT,"se"),
join(TEST_DIR,"operator"),
join(TEST_DIR,"call"),join(TEST_DIR,"comment"),
join(TEST_DIR,"transpiler")
#join(TEST_DIR,"super")join(TEST_DIR,"get"), # Exclude these tests for now
#join(TEST_DIR,"set"),join(TEST_DIR,"eu"),
#,join(TEST_DIR,"class"),
]




def print_results(passed,failed,failed_tests):
    print("\n")
    print("Tests have finished running.")
    print(f"Total:{passed + failed}",f"Passed:{passed}",f"Failed:{failed}")
    print("\n\n")
    if len(failed_tests) > 0:
        print("Failed tests:")
        for name in failed_tests:
            print(name)



#TODO: Refactor this monster 
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
                        try:
                            output = run_program(script,backend)
                        except Exception as e:
                            pass 
                    expected = res_file.readline().strip()
                    symbol = ""
                    if output.strip() == expected:
                        passed += 1
                        symbol = "."
                    else:
                        failed += 1
                        failed_tests.append(os.path.relpath(test_case))
                        symbol = "x"
                    print(symbol,end="")

    print_results(passed,failed,failed_tests)

if __name__ == "__main__":
    run_tests(Interpreter)
    print("\n\n-------------")
    run_tests(Transpiler)
