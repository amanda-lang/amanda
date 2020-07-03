import os
import os.path
import argparse
from io import StringIO
from amanda.pyamanda import Interpreter
import amanda.error as error
from backend.transpiler import Transpiler



join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
RESULTS_FILE = "result.txt"


def run_program(src,backend_cls):
    backend = backend_cls(src,True)
    try:
        backend.exec()
        return backend.test_buffer.getvalue()
    except SystemExit:
        return backend.test_buffer.getvalue()
    except Exception as e:
        raise e


def delete_script_output(test_dir):
    for root,dirs,files in os.walk(test_dir):
        result = join(root,RESULTS_FILE)
        try:
            os.remove(result)
        except FileNotFoundError:
            pass

def get_script_output(test_dir):
    for root,dirs,files in os.walk(test_dir):
        for file in sorted(files):
            #Crazy workaround because of coverage file
            if file == ".coverage":
                continue
            filename = join(root,file)
            with open(join(root,RESULTS_FILE),"a") as result, open(filename,"r") as src:
                buffer = run_script(src)
                result.write(buffer.getvalue().strip()+"\n")


def main():
    ''' Gets test subdirectory from command line args and 
    creates result file'''
    parser = argparse.ArgumentParser()
    parser.add_argument("dir",help = "the directory containing the source files to be executed. Directory must be a subdirectory of test_dir.")
    args = parser.parse_args()
    # Try and open file
    try:
        test_dir = join(TEST_DIR,args.dir)
        get_script_output(test_dir)
    except FileNotFoundError:
        print(f"The directory {args.dir} does not exist") 


if __name__ == "__main__":
    main()
