
import unittest
import os
import sys
import tempfile
import subprocess


class MainTestCase(unittest.TestCase):
    def setUp(self):
        self.filename = "input_test_case.ama"

    def test_report_arg(self):
        src = open(self.filename, mode="w")
        src.writelines([
            "str : texto = leia(\"Give us a string\")\n",
            "mostra str\n", 
        ])
        src.close()

        read_fd, write_fd = os.pipe()
        stdin_r, stdin_w = os.pipe()

        os.set_inheritable(write_fd, True)
        
        child_proc = subprocess.Popen([
            sys.executable, "-m", "amanda", "-r", 
            str(write_fd), os.path.abspath(self.filename)],
            close_fds=False, stdin=stdin_r
        )
        os.close(write_fd)
        os.close(stdin_r)

        with os.fdopen(read_fd) as pipe:
            while (message := pipe.readline().strip()) != "END":
                if message == "INPUT":
                    os.write(stdin_w, b"OP")
                    os.close(stdin_w)

    def tearDown(self):
        os.remove(self.filename)


