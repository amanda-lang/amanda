import os
import os.path
from io import StringIO
from amanda.pyamanda import Interpreter
import amanda.error as error


join = os.path.join
#test paths
TEST_DIR = os.path.abspath("./tests")
RESULTS_FILE = "result.txt"


def run_script(src):
    intp = Interpreter(src,True)
    try:
        intp.run()
        return intp.output
    except SystemExit:
        return intp.output
    except UnicodeError:
        raise Exception(f"This is the file causing this: {src}")
    except Exception as e:
        print(f"Error caused by this src file: {src}")
        raise e



def delete_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        result = join(root,RESULTS_FILE)
        try:
            os.remove(result)
        except FileNotFoundError:
            pass

def get_script_output():
    for root,dirs,files in os.walk(TEST_DIR):
        for file in sorted(files):
            #Crazy workaround because of coverage file
            if file == ".coverage":
                continue
            filename = join(root,file)
            with open(join(root,RESULTS_FILE),"a") as result, open(filename,"r") as src:
                buffer = run_script(src)
                result.write(buffer.getvalue().strip()+"\n")

if __name__=="__main__":
    delete_script_output()
    get_script_output()
