import os
import sys
from io import StringIO
from os.path import join 
import re
import traceback
from contextlib import redirect_stdout,redirect_stderr
from amanda.__main__ import main as ama_main

TEST_DIR = os.path.abspath("./tests/inputs")
STATEMENT = join(TEST_DIR,"statement")
EXCLUDED = ("result.txt")
RESULTS_FILE = "result.txt"
RESULTS_DIR = join("./tests/outputs/")

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
join(TEST_DIR,"indef_type"),join(TEST_DIR,"converte"),
join(TEST_DIR,"builtins"),join(TEST_DIR,"list"),
join(TEST_DIR,"class"),
join(TEST_DIR,"get"),join(TEST_DIR,"set")# Exclude these tests for now
#,join(TEST_DIR,"eu"),
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
    failed_tests.append(
        (os.path.relpath(test_case),error)
    )

def print_failed():
    print("Failed tests:")
    print("\n")
    for filename,error in failed_tests:
        print(filename)
        print("-"*len(filename))
        traceback.print_exception(
            type(error),error,
            error.__traceback__
        )
        print("\n")

def print_results():
    print("\n")
    print("Tests have finished running.")
    print(f"Total:{passed + failed}",f"Passed:{passed}",f"Failed:{failed}")
    print("\n\n")
    if failed_tests:
        print_failed()
        sys.exit("Some tests failed")

def load_test_cases(suite):
    for root,dirs,files in os.walk(suite):
        dirname = os.path.basename(root) #adds tuple containing test case file path and result file path of test case
        # to the list of test cases of this suite
        test_cases = [
            (
                join(root,filename),
                join(RESULTS_DIR,"_".join(["result",dirname,filename]))
            )
            for filename in files
            if filename not in EXCLUDED
        ]
    return test_cases

def fmt_error(output):
    regex = re.compile(r"-{3,}") 
    sep = regex.findall(output)[0]
    return output.split(sep)[0].strip()

def run_case(filename):
    stdout = StringIO() 
    stderr = StringIO() 
    try:
        with redirect_stdout(stdout),redirect_stderr(stderr):
            ama_main(filename)
    except SystemExit as e:
        #Print stdout + stderr in case some code ran
        #before error was thrown
        out = stdout.getvalue()
        err = stderr.getvalue()
        #HACK: This is to check if
        #the system exit was caused by an AmandaError
        #or some other error in main
        if len(out) and len(err):
            return (
                out + fmt_error(err)
            ).replace("\n"," ")
        elif len(err):
            return fmt_error(err)
        else:
            raise e
    return stdout.getvalue().replace("\n"," ")

def run_suite(test_cases):
    for test_case,result_file in test_cases:
        results = open(result_file,"r")
        try:
            output = run_case(test_case).strip()
            expected = results.readline().strip()
            assert output == expected
            add_success()
        except AssertionError as e:
            exception = Exception(f"\nFailed assertion:\n{output} != {expected}")
            add_failure(test_case,exception)
        except Exception as e:
            add_failure(test_case,e)
        results.close()


if __name__ == "__main__":
    #Run test files in each test_directors
    for suite in DIRS:
        test_cases = load_test_cases(suite)
        run_suite(test_cases)
    print_results()
