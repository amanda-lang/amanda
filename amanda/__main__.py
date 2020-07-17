import argparse
import time
from os.path import abspath
from amanda.transpiler import Transpiler
from amanda.runtime import run_pycode

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",help = "source file to be executed")
    args = parser.parse_args()
    # Try and open file
    try:
        with open(abspath(args.file)) as script,\
        open("output.py","w") as output:
            amandac = Transpiler(script)
            code = amandac.compile()
            output.write(str(code))
            run_pycode(amandac.src,code)
    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")

if __name__ == "__main__":
    main()

