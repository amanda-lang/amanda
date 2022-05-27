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
    # Compile VM
    subprocess.run(
        [sys.executable, "-m", "utils.build", "--release"], check=True
    )
    path_sep = os.pathsep
    # Build the things
    pyinst_main.run(
        [
            f"--name={bin_name}",
            "--onefile",
            "--console",
            "--clean",
            "--noconfirm",
            # Standard lib
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
    # Create a symlink pointing to binary in /usr/local/bin/
    # in Mac and linux
    if OS_X or LINUX:
        # target = path.abspath(path.join(build_dir, bin_name))
        # link = path.join(path.abspath("/usr/local/bin"), bin_name)
        # subprocess.run(["ln", "-s", "-f", target, link], check=True)
        pass
    elif WIN_32:
        # Do windows stuff in here
        pass


if __name__ == "__main__":
    main()
