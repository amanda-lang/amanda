import os
import os.path as path
import shutil
import sys
import subprocess
import PyInstaller.__main__

OS_X = sys.platform == "darwin"
WIN_32 = sys.platform == "win32"
LINUX = sys.platform == "linux"

def main():
    BINARY_NAME = "amanda"
    SCRIPT = path.abspath(path.join("./amanda","__main__.py"))
    BUILD_DIR = path.abspath("./dist")

    PyInstaller.__main__.run([
        f"--name={BINARY_NAME}", "--onefile",
        "--console" ,"--clean" ,f"{SCRIPT}",
    ])

    # Remove build files
    os.remove(f"{BINARY_NAME}.spec")
    shutil.rmtree("./build")
    #Create a symlink pointing to binary in /usr/local/bin/ 
    #in Mac and linux
    if OS_X or LINUX:
        target = path.abspath(path.join(BUILD_DIR,BINARY_NAME))
        link = path.join(
            path.abspath("/usr/local/bin"),BINARY_NAME
        )
        subprocess.run(["ln","-s","-f",target,link],check = True)
    elif WIN_32:
        #Do windows stuff in here
        pass

if __name__ == "__main__":
    main()
