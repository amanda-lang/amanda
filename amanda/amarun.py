import sys
from amanda.error import AmandaError, handle_exception, throw_error
from amanda.bltins import bltin_objs
from amanda.parse import Parser
from amanda.compile import Generator
from amanda.semantic import Analyzer


def run(src, *, gen_out=False, outname="output.py"):
    try:
        program = Parser(src).parse()
        valid_program = Analyzer().visit_program(program)
    except AmandaError as e:
        throw_error(e, src)
    generator = Generator()
    code, line_info = generator.generate_code(valid_program)
    if gen_out:
        with open(outname, "w") as output:
            output.write(code)
    pycode_obj = compile(code, outname, "exec")
    try:
        # Run compiled python code
        exec(pycode_obj, bltin_objs)
    except Exception as e:
        ama_error = handle_exception(e, outname, line_info)
        if not ama_error:
            raise e
        throw_error(ama_error, src)
