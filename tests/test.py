import os
import sys
from io import StringIO
from os.path import join
import re
import traceback
import subprocess
from contextlib import redirect_stdout, redirect_stderr

TEST_DIR = os.path.abspath("./tests/test_cases/")
STATEMENT = join(TEST_DIR, "statement")
EXCLUDED = []

# test paths
DIRS = [
    join(TEST_DIR, "assignment"),
    join(STATEMENT, "mostra"),
    join(TEST_DIR, "operator"),
    join(STATEMENT, "se"),
    join(STATEMENT, "enquanto"),
    join(STATEMENT, "escolha"),
    join(TEST_DIR, "function"),
    join(STATEMENT, "retorna"),
    join(STATEMENT, "loop_ctl"),
    join(TEST_DIR, "comment"),
    join(TEST_DIR, "call"),
    join(TEST_DIR, "declaration"),
    join(TEST_DIR, "expression"),
    join(TEST_DIR, "converte"),
    join(TEST_DIR, "vec"),
    join(TEST_DIR, "rt_errors"),
]

passed = 0
failed = 0
failed_tests = []


def add_success():
    global passed
    passed += 1
    print(".", end="")


def add_failure(test_case, error):
    global failed, failed_tests
    failed += 1
    failed_tests.append((os.path.relpath(test_case), error))
    print("x", end="")


def print_failed():
    print("Failed tests:")
    print("\n")
    for filename, error in failed_tests:
        print(filename)
        print("-" * len(filename))
        traceback.print_exception(type(error), error, error.__traceback__)
        print("\n")


def print_results():
    print("\n")
    print("Tests have finished running.")
    print(f"Total:{passed + failed}", f"Passed:{passed}", f"Failed:{failed}")
    print("\n\n")
    if failed_tests:
        print_failed()
        sys.exit("Some tests failed")


# TODO: Find better way to do this
def get_case_output(case):
    output = None
    with open(case, "r", encoding="utf8") as test:
        for line in test:
            if "#[output]" in line:
                output = line.split(":", maxsplit=1)[1].strip()
                break
    assert (
        output is not None
    ), f"Test must have line comment that indicates it's output. File: {case}"
    return output


def load_test_cases(suite):
    for root, dirs, files in os.walk(suite):
        dirname = os.path.basename(root)
        test_cases = [
            (join(root, filename), get_case_output(join(root, filename)))
            for filename in files
            if filename not in EXCLUDED
        ]
    return test_cases


def fmt_error(output):
    return output.strip().split("\n")[-1].strip()


def run_case(filename):
    test_p = subprocess.run(
        ["python", "-m", "amanda", filename],
        capture_output=True,
        encoding="utf8",
    )
    # Print stdout + stderr in case some code ran
    # before error was thrown
    out = test_p.stdout
    err = test_p.stderr
    # HACK: This is to check if
    # the system exit was caused by an AmandaError
    # or some other error in main
    if len(out) and len(err):
        return (out + fmt_error(err)).replace("\n", " ")
    elif len(err):
        return fmt_error(err)
    else:
        return out.replace("\n", " ")


def run_suite(test_cases):
    for test_case, expected in test_cases:
        try:
            output = run_case(test_case).strip()
            assert output == expected
            add_success()
        except AssertionError as e:
            exception = Exception(
                f"\nFailed assertion:\n{output} != {expected}"
            )
            add_failure(test_case, exception)
        except Exception as e:
            add_failure(test_case, e)


if __name__ == "__main__":
    # Compile libamanda
    subprocess.call([sys.executable, "-m", "utils.build"])
    # Run end-to-end tests
    print("Running tests...")
    for suite in DIRS:
        test_cases = load_test_cases(suite)
        run_suite(test_cases)
    print_results()
    if failed > 0:
        sys.exit(1)
