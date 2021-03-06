import argparse
import time
from io import StringIO
import os
import sys
from os.path import abspath
from amanda.amarun import run
from amanda.error import handle_exception, throw_error
from amanda.bltins import bltin_objs


def main(*args):
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="source file to be executed")
    parser.add_argument(
        "-g", "--generate", help="Generate an output file", action="store_true"
    )
    parser.add_argument(
        "-o",
        "--outname",
        type=str,
        help="Name of the output file, Requires the -g option to take effect. Defaults to output.py.",
        default="output.py",
    )
    parser.add_argument(
        "-r",
        "--report",
        help="Activates report mode and sends event messages to specified port on the local machine.",
        type=int,
    )

    if len(args):
        args = parser.parse_args(args)
    else:
        args = parser.parse_args()
    try:
        with open(abspath(args.file), encoding="utf-8") as src_file:
            src = StringIO(src_file.read())
    except FileNotFoundError:
        sys.exit(f"The file '{abspath(args.file)}' was not found on this system")

    run(src, gen_out=args.generate, outname=args.outname)


if __name__ == "__main__":
    main()
