import keyword
import random


types = ["int","real","bool"]


with open("py_builtins.ama","w") as test_case:
    for word in globals().get("__builtins__").__dict__:
        line = f"func {word}()  mostra 'meu nome é {word}';  fim"
        print(line,end="\n\n",file=test_case)
        print(f"{word}()",end="\n\n",file=test_case)
