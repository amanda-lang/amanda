import argparse
import time
from io import StringIO
import os
import sys
from os import path
from amanda.amarun import run_py, run_rs
from amanda.error import handle_exception, throw_error
from amanda.bltins import bltin_objs


def main(*args):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(
        help="subcommands for running code with the vm"
    )

    py_cmds = subparsers.add_parser(
        "py", description="Run using the python transpiler backend"
    )

    py_cmds.add_argument("file", help="source file to be executed")

    py_cmds.add_argument(
        "-g", "--generate", help="Generate an output file", action="store_true"
    )
    py_cmds.add_argument(
        "-o",
        "--outname",
        type=str,
        help="Name of the output file, Requires the -g option to take effect. Defaults to output.py.",
        default="output.py",
    )
    py_cmds.set_defaults(exec_cmd=run_py)

    rs_cmds = subparsers.add_parser(
        "rs", description="Run using the rust vm backend"
    )

    rs_cmds.add_argument(
        "-d", "--debug", help="Generate a debug amasm file", action="store_true"
    )
    rs_cmds.add_argument("file", help="source file to be executed")
    rs_cmds.set_defaults(exec_cmd=run_rs)

    if len(args):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    if not path.isfile(args.file):
        sys.exit(
            f"The file '{path.abspath(args.file)}' was not found on this system"
        )
    args.exec_cmd(args)


if __name__ == "__main__":
    main()
