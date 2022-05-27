import os
import sys
from io import StringIO
from os.path import join

TEST_DIR = os.path.abspath("./tests/inputs")
STATEMENT = join(TEST_DIR, "statement")
EXCLUDED = "result.txt"
RESULTS_FILE = "result.txt"
RESULTS_DIR = join("./tests/outputs/")

# test paths
DIRS = [
    join(TEST_DIR, "assignment"),
    join(TEST_DIR, "declaration"),
    join(TEST_DIR, "expression"),
    join(TEST_DIR, "function"),
    join(STATEMENT, "enquanto"),
    join(STATEMENT, "mostra"),
    join(STATEMENT, "para"),
    join(STATEMENT, "retorna"),
    join(STATEMENT, "escolha"),
    join(STATEMENT, "se"),
    join(TEST_DIR, "operator"),
    join(TEST_DIR, "call"),
    join(TEST_DIR, "comment"),
    join(TEST_DIR, "transpiler"),
    join(TEST_DIR, "rt_errors"),
    join(TEST_DIR, "indef_type"),
    join(TEST_DIR, "converte"),
    join(TEST_DIR, "builtins"),
    join(TEST_DIR, "list"),
    join(TEST_DIR, "class"),
    join(TEST_DIR, "get"),
    join(TEST_DIR, "set"),
    join(TEST_DIR, "eu"),
    join(TEST_DIR, "nulo"),
]


def load_test_cases(suite):
    for root, dirs, files in os.walk(suite):
        dirname = os.path.basename(
            root
        )  # adds tuple containing test case file path and result file path of test case
        # to the list of test cases of this suite
        test_cases = [
            (
                join(root, filename),
                join(RESULTS_DIR, "_".join(["result", dirname, filename])),
            )
            for filename in files
            if filename not in EXCLUDED
        ]
    return test_cases


def append_test_result(test_cases):
    for test_case, result_file in test_cases:
        with open(result_file, "r", encoding="utf-8") as f:
            result = f.read()
        with open(test_case, "a", encoding="utf8") as test_file:
            test_file.write(f"\n#[output]:{result}")


if __name__ == "__main__":
    for suite in DIRS:
        test_cases = load_test_cases(suite)
        append_test_result(test_cases)
