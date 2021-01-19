
import unittest
import os
import sys
import tempfile
import subprocess
import socket
from multiprocessing import Process, Queue, Condition

PORT = 12000
HOST = "127.0.0.1"
def run_server(queue):
    print("Starting server")
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((HOST, PORT))
    serversocket.listen(5)
    clients = 0
    while True:
        print("waiting for connections")
        client, _ = serversocket.accept()
        clients += 1
        print("Accepted connection")
        print("Receiving messages")
        print("Server recv thread: waiting for message")
        while (message := client.recv(4096).decode()):
            print(message)
            queue.put(message)
        if clients > 1:
            queue.put("")
            break
    print("Server recv thread: Shutdown")
    serversocket.close()

def is_online():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        s.close()
        return True
    except OSError:
        return False
    finally:
        s.close()
        
class MainTestCase(unittest.TestCase):
    def setUp(self):
        self.filename = "input_test_case.ama"

    def test_report_arg(self):
        with open(self.filename, mode="w") as src:
            src.writelines([
                "str : texto = leia(\"Give us a string\")\n",
                "mostra str\n", 
            ])

        queue = Queue()
        p = Process(target=run_server,args=(queue,))
        p.start()
        
        while not is_online():
            print("Waiting for server to start")
        print("Server has started")

        child_proc = subprocess.Popen([
            sys.executable, "-m", "amanda", "-r", 
            f"{PORT}", os.path.abspath(self.filename)],
            stdin=subprocess.PIPE
        )

        while (message := queue.get()):
            print("Server main thread: Waiting for message")
            print(message)
            print("Server main thread: Got message")
            if message == "<INPUT>":
                child_proc.communicate(b"I got the message")

    def tearDown(self):
        os.remove(self.filename)


