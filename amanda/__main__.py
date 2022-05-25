import argparse
import time
from io import StringIO
import os
import sys
from os import path
from amanda.amarun import run_file


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
