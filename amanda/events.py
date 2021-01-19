import sys
import os
import socket

def open_conn(port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("127.0.0.1", port))
        return s
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return None

def close_conn(socket):
    socket.close()

def event_hook(event, args):
    if event == "builtins.input":
        return b"<INPUT>"
    return None

def create_event_hook(socket):
    def event_wrapper(*args, **kwargs):
        message = event_hook(*args, **kwargs)
        if message != None:
            print("Client: Sending message")
            socket.sendall(message)
            print("Client: message sent")
    return event_wrapper





