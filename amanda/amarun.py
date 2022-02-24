import sys
import os
import subprocess
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


def run_py(args):
    _run_py(args.file, gen_out=args.generate, outname=args.outname)


def run_frontend(filename):
    try:
        program = parse(filename)
        valid_program = Analyzer(filename, Module(filename)).visit_program(
            program
        )
    except AmandaError as e:
        throw_error(e)
    return valid_program


def _run_py(filename, *, gen_out=False, outname="output.py"):
    valid_program = run_frontend(filename)
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


def run_rs(args):
    asm_code = ByteGen().compile(run_frontend(args.file))
    OUT_FILE = "out.amasm"
    write_file(OUT_FILE, asm_code)

    return_code = subprocess.call(
        ["cargo", "build", "--bins", "--manifest-path", "vm/Cargo.toml"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if return_code != 0:
        sys.exit(1)

    # TODO: This is kinda of sus. Find a better way to do this
    subprocess.call(["vm/target/debug/vm", OUT_FILE])
