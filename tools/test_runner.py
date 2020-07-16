import os
from io import StringIO
from amanda.transpiler import Transpiler
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
join(TEST_DIR,"transpiler"),join(TEST_DIR,"rt_errors"),
join(TEST_DIR,"indef_type"),
#join(TEST_DIR,"super")join(TEST_DIR,"get"), # Exclude these tests for now
#join(TEST_DIR,"set"),join(TEST_DIR,"eu"),
#,join(TEST_DIR,"class"),
]

passed = 0
failed = 0
failed_tests = []

def add_success():
    global passed
    passed += 1
    print(".",end="")

def add_failure(test_case,error):
    global failed,failed_tests
    failed += 1
    failed_tests.append(os.path.relpath(test_case))

def print_results():
    print("\n")
    print("Tests have finished running.")
    print(f"Total:{passed + failed}",f"Passed:{passed}",f"Failed:{failed}")
    print("\n\n")
    if len(failed_tests) > 0:
        print("Failed tests:")
        for name in failed_tests:
            print(name)

#TODO: Stop relying on sorted for tests to avoid windows cheese
def load_test_cases(suite):
    for root,dirs,files in os.walk(suite):
        test_cases = [
            join(root,filename) for filename in sorted(files)
            if filename not in EXCLUDED
        ]
    return test_cases

def run_suite(test_cases,results,backend):
    for test_case in test_cases:
        script = open(test_case,"r")
        try:
            output = run_program(script,backend).strip()
            expected = results.readline().strip()
            assert output == expected
            add_success()
        except AssertionError as e:
            add_failure(test_case,str(e))
        except Exception as e:
            add_failure(test_case,str(e))
        script.close()

def main(backend):
    ''' Convenience method for running
    test cases.
    '''
    #Run test files in each test_directors
    for suite in DIRS:
        results = open(join(suite,"result.txt"),"r")
        test_cases = load_test_cases(suite)
        run_suite(test_cases,results,backend)
        results.close()
    print_results()

if __name__ == "__main__":
    main(Transpiler)
