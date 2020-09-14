import os
import os.path as path
import shutil
import sys

OS_X = sys.platform == "darwin"
WIN_32 = sys.platform == "win32"
LINUX = sys.platform == "linux"

def main():
    BINARY_NAME = "amanda"
    SCRIPT = path.join("./amanda","__main__.py")
    BUILD_DIR = "./dist"
    #Build executable
    os.system(f"python3 -m PyInstaller --name={BINARY_NAME} --onefile --console --clean {SCRIPT}")
    # Remove build files
    os.remove(f"{BINARY_NAME}.spec")
    shutil.rmtree("./build")
    #Create a symlink pointing to binary in /usr/local/bin/ 
    #in Mac and linux
    if OS_X or LINUX:
        os.symlink(
            path.abspath(path.join(BUILD_DIR,BINARY_NAME)),
            path.join(path.abspath("/usr/local/bin"),BINARY_NAME)
        )


if __name__ == "__main__":
    main()
