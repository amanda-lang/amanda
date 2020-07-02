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
        with open(abspath(args.file)) as script:
            amac = Transpiler(script)
            code = amac.compile()
        
        with open("output.py","w") as output:
            output.write(code)



    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")



if __name__ == "__main__":
    main()

