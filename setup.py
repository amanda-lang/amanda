import os
import os.path as path
import shutil
import sys
import subprocess
import PyInstaller.__main__ as pyinst_main
from amanda.config import LIB_AMA

OS_X = sys.platform == "darwin"
WIN_32 = sys.platform == "win32"
LINUX = sys.platform == "linux"


def main():
    bin_name = "amanda"
    script = path.abspath(path.join("./amanda", "__main__.py"))
    build_dir = "./dist"
    os.environ["PYINST_BUILD"] = "1"
    try:
        # Run tests
        subprocess.run([sys.executable, "-m", "tests.test"], check=True)
        # Compile VM
        subprocess.run(
            [sys.executable, "-m", "utils.build", "--release"], check=True
        )
    except Exception as e:
        print("Error during setup: ")
        print(e.output)
        sys.exit(1)
    path_sep = os.pathsep
    # Build the things
    pyinst_main.run(
        [
            f"--name={bin_name}",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            # Builtin modules
            f"--add-data=./std/embutidos.ama{path_sep}./std/",
            # VM dynamic lib
            f"--add-data={LIB_AMA}{path_sep}./deps/",
            f"--distpath={build_dir}",
            f"{script}",
        ]
    )

    # Remove build files
    os.remove(f"{bin_name}.spec")
    shutil.rmtree("./build")


if __name__ == "__main__":
    main()
