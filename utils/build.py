import argparse
import time
import os
import sys
import subprocess
from amanda.config import VM_CONFIG
from os import path


def main():
    parser = argparse.ArgumentParser(
        description="Simple util to compile the rust VM"
    )

    parser.add_argument(
        "-r",
        "--release",
        help="Build vm lib with release flag",
        action="store_true",
    )
    args = parser.parse_args()

    os.environ["RUST_BACKTRACE"] = "1"
    main_args = ["cargo", "build"]
    if args.release:
        print("Bulding VM lib with release optimizations.")
        main_args.append("--release")

    return_code = subprocess.call(
        [*main_args, "--manifest-path", VM_CONFIG],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if return_code != 0:
        subprocess.call(["cargo", "check", "--manifest-path", VM_CONFIG_PATH])
        sys.exit(1)


if __name__ == "__main__":
    main()
