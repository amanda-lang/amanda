import argparse
import time
from os.path import abspath
from amanda.lexer import Lexer
from amanda.parser import Parser
from amanda.semantic import Analyzer
from amanda.pyamanda import Interpreter
import amanda.error as error

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",help = "source file to be executed")
    args = parser.parse_args()
    # Try and open file
    try:
        with open(abspath(args.file)) as script:
            py_ama = Interpreter(script)
            py_ama.run()

    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")




if __name__ == "__main__":
    main()

