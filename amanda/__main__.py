import argparse
import time
from io import StringIO
import sys
from os.path import abspath
from amanda.transpiler import Transpiler
from amanda.runtime import handle_exception,throw_error
from amanda.bltins import bltin_objs

FILENAME = "<output>"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",help = "source file to be executed")
    args = parser.parse_args()

    try:
        with open(abspath(args.file)) as src_file:
            src = StringIO(src_file.read()) 
    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")
        sys.exit()

    amandac = Transpiler(src)
    code = amandac.compile()
    #TODO: Make this optional because i don't need
    #to write output to disk
    with open("output.py","w") as output:
        output.write(str(code))
    #Run compiled python code
    pycode_obj = compile(str(code),FILENAME,"exec")
    try:
        exec(pycode_obj,bltin_objs)
    except Exception as e:
        ama_error = handle_exception(e,amandac.src_map)
        if not ama_error:
            raise e
        throw_error(ama_error,src)

if __name__ == "__main__":
    main()

