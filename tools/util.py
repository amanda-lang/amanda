import os
import os.path
import argparse
from amanda.transpiler import Transpiler



join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
RESULTS_DIR = join(TEST_DIR,"results")
RESULTS_FILE = "result.txt"
EXCLUDED = (
    "results","result.txt",
    "super","get",
    "set","eu","class"
)


def run_program(src,backend_cls):
    backend = backend_cls(src,True)
    try:
        backend.exec()
        return backend.test_buffer.getvalue()
    except SystemExit:
        return backend.test_buffer.getvalue()
    except Exception as e:
        raise e


def delete_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        result = join(root,RESULTS_FILE)
        try:
            os.remove(result)
        except FileNotFoundError:
            pass

def gen_results():
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
    #delete_script_output()
    main()
