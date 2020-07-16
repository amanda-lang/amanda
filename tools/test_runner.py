import os
import traceback
from amanda.transpiler import Transpiler

join = os.path.join
TEST_DIR = os.path.abspath("./tests")
STATEMENT = join(TEST_DIR,"statement")
EXCLUDED = ("result.txt")
RESULTS_FILE = "result.txt"
RESULTS_DIR = join(TEST_DIR,"results")

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

def run_program(src,backend_cls):
    backend = backend_cls(src,True)
    try:
        backend.exec()
        return backend.test_buffer.getvalue()
    except SystemExit:
        return backend.test_buffer.getvalue()
    except Exception as e:
        raise e

#Deletes result files for specific test
#cases
def delete_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        result = join(root,RESULTS_FILE)
        try:
            os.remove(result)
        except FileNotFoundError:
            pass

#Generates result files for test cases
def gen_results():
    EXCLUDED = (
        "results","result.txt",
        "super","get",
        "set","eu","class"
    )
    for root,dirs,files in os.walk(TEST_DIR):
        dirname = os.path.basename(root)
        print(dirname)
        for file in sorted(files):
            #Crazy workaround because of results.txt and result dir
            if file in EXCLUDED  or dirname in EXCLUDED:
                continue
            filename = join(root,file)
            result_fname = "_".join(["result",dirname,file])
            with open(join(RESULTS_DIR,result_fname),"w") as result_file,\
            open(filename,"r") as src:
                result = run_program(src,Transpiler)
                result_file.write(result.strip()+"\n")

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
    if len(failed_tests):
        print_failed()

def load_test_cases(suite):
    for root,dirs,files in os.walk(suite):
        dirname = os.path.basename(root)
        #adds tuple containing test case file path and result file path of test case
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

def run_suite(test_cases,backend):
    for test_case,result_file in test_cases:
        script = open(test_case,"r")
        results = open(result_file,"r")
        try:
            output = run_program(script,backend).strip()
            expected = results.readline().strip()
            assert output == expected
            add_success()
        except AssertionError as e:
            exception = Exception(f"\nFailed assertion:\n{output} != {expected}")
            add_failure(test_case,exception)
        except Exception as e:
            add_failure(test_case,e)
        script.close()
        results.close()

def main(backend):
    ''' Convenience method for running
    test cases.
    '''
    #Run test files in each test_directors
    for suite in DIRS:
        test_cases = load_test_cases(suite)
        run_suite(test_cases,backend)
    print_results()

if __name__ == "__main__":
    main(Transpiler)
