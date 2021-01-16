import sys
import os
from threading import Thread


def create_event_hook(pipe, hook):
    def event_wrapper(*args, **kwargs):
        message = hook(*args, **kwargs)
        #write message to pipe
        if message != None:
            pipe.write(message)
            pipe.flush()
    return event_wrapper

def event_hook(event, args):
    if event == "builtins.input":
        return "INPUT\n"
    return None
