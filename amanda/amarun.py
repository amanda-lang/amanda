import sys
import os
import subprocess
from contextlib import redirect_stdout, redirect_stderr
from amanda.compiler.symbols import Module
from amanda.compiler.error import AmandaError, handle_exception, throw_error
from amanda.compiler.bltins import bltin_objs
from amanda.compiler.parse import parse
from amanda.compiler.compile import Generator
from amanda.compiler.semantic import Analyzer
from amanda.compiler.codegen import ByteGen
from amanda.config import VM_CONFIG_PATH, VM_BIN_PATH


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
    compiler = ByteGen()
    asm_code = compiler.compile(run_frontend(args.file))
    OUT_FILE = "out.amasm"
    write_file(OUT_FILE, asm_code)

    if args.debug:
        write_file("debug.amasm", compiler.make_debug_asm())

    os.environ["RUST_BACKTRACE"] = "1"
    return_code = subprocess.call(
        ["cargo", "build", "--bins", "--manifest-path", VM_CONFIG_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if return_code != 0:
        subprocess.call(["cargo", "check", "--manifest-path", VM_CONFIG_PATH])
        sys.exit(1)

    # TODO: This is kinda of sus. Find a better way to do this
    if args.test:
        result = subprocess.run(
            [VM_BIN_PATH, OUT_FILE],
            capture_output=True,
            encoding="utf8",
        )
        print(result.stdout, end="")
        if result.returncode != 0:
            subprocess.call([VM_BIN_PATH, OUT_FILE])
    else:
        retcode = subprocess.call(
            [VM_BIN_PATH, OUT_FILE],
        )
