import argparse
import time
from os.path import abspath
from backend.transpiler import Transpiler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",help = "source file to be executed")
    args = parser.parse_args()
    # Try and open file
    try:
        with open(abspath(args.file)) as script,\
        open("output.py","w") as output:
            amac = Transpiler(script)
            code = amac.compile()
            output.write(code)
        amac.exec()
    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")



if __name__ == "__main__":
    main()

