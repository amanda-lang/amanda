import sys
from amanda.symbols import Module
from amanda.error import AmandaError, handle_exception, throw_error
from amanda.bltins import bltin_objs
from amanda.parse import parse
from amanda.compile import Generator
from amanda.semantic import Analyzer
from amanda.bytec import ByteGen


def write_file(name, code):
    with open(name, "w") as output:
        output.write(code)


def run(filename, gen_asm, *, gen_out=False, outname="output.py"):
    try:
        program = parse(filename)
        valid_program = Analyzer(filename, Module(filename)).visit_program(
            program
        )
    except AmandaError as e:
        throw_error(e)
    if gen_asm:
        code = ByteGen().compile(valid_program)
        write_file(f"out.amasm", code)
        return
    generator = Generator()
    code, line_info = generator.generate_code(valid_program)
    if gen_out:
        write_file(outname, code)
    pycode_obj = compile(code, outname, "exec")
    try:
        # Run compiled python code
        exec(pycode_obj, bltin_objs)
    except Exception as e:
        ama_error = handle_exception(e, outname, filename, line_info)
        if not ama_error:
            raise e
        throw_error(ama_error)
