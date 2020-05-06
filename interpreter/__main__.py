import argparse
from os.path import abspath
from interpreter.lexer import Lexer
from interpreter.parser import Parser
from interpreter.semantic import Analyzer
from interpreter.pypti import Interpreter
import interpreter.error as error




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file",help = "source file to be executed")
    args = parser.parse_args()
    # Try and open file
    try:
        with open(abspath(args.file)) as script:
            run_script(script)
    except FileNotFoundError:
        print(f"The file '{abspath(args.file)}' was not found on this system")
    except error.Error as e:
        print(e)



def run_script(file):
    analyzer = Analyzer(Parser(Lexer(file)))
    analyzer.check_program()
    interpreter = Interpreter(analyzer.program)
    interpreter.interpret()

main()
