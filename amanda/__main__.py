import argparse
import time
from io import StringIO
import os
import sys
import subprocess
from os import path
from amanda.compiler.symbols import Module
from amanda.compiler.error import AmandaError, handle_exception, throw_error
from amanda.compiler.parse import parse
from amanda.compiler.compile import Generator
from amanda.compiler.semantic import Analyzer
from amanda.compiler.codegen import ByteGen
from amanda.libamanda import run_module
from amanda.config import VM_CONFIG_PATH


def write_file(name, code):
    with open(name, "w") as output:
        output.write(code)


def run_frontend(filename):
    try:
        program = parse(filename)
        valid_program = Analyzer(filename, Module(filename)).visit_program(
            program
        )
    except AmandaError as e:
        throw_error(e)
    return valid_program


def run_file(args):
    os.environ["RUST_BACKTRACE"] = "1"
    return_code = subprocess.call(
        ["cargo", "build", "--manifest-path", VM_CONFIG_PATH],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if return_code != 0:
        subprocess.call(["cargo", "check", "--manifest-path", VM_CONFIG_PATH])
        sys.exit(1)

    compiler = ByteGen()
    bin_obj = compiler.compile(run_frontend(args.file))

    if args.debug:
        write_file("debug.amasm", compiler.make_debug_asm())

    exit_code = run_module(bin_obj)
    if exit_code != 0:
        sys.exit(exit_code)


def main(*args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-d", "--debug", help="Generate a debug amasm file", action="store_true"
    )

    parser.add_argument("file", help="source file to be executed")

    if len(args):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    if not path.isfile(args.file):
        sys.exit(
            f"The file '{path.abspath(args.file)}' was not found on this system"
        )
    run_file(args)


if __name__ == "__main__":
    main()
