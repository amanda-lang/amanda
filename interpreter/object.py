
''' Module for all object classes used as runtime representations of user defined
and native language constructs (classes and functions).
Also contains other helper classes to be used at runtime
'''
from abc import ABC,abstractmethod



class Environment:

    def __init__(self,name,previous=None):
        self.name = name
        self.previous = previous
        self.memory = {} # initialize it's env with it's own global mem space


    def define(self,name,value):
        self.memory[name] = value

    def resolve(self,name):
        value = self.memory.get(name)
        if value is None and self.previous is not None:
            return self.previous.resolve(name)
        return value

    def resolve_space(self,name):
        if self.memory.get(name) is not None:
            return self
        elif self.previous is not None:
            return self.previous.resolve_space(name)
        return None


    def __str__(self):
        str = ""
        for key in self.memory:
            str += f"{key} : {self.memory[key]}\n"
        return f"{self.name}\n{str}"

class Function(ABC):

    def __init__(self,name):
        self.name = name

    @abstractmethod
    def call(self):
        pass


class RTFunction(Function):
    def __init__(self,name,declaration=None):
        self.name = name
        self.declaration = declaration

    def call(self,interpreter,args=[]):
        decl = self.declaration
        env = Environment(decl.id.lexeme,interpreter.memory)
        for param,arg in zip(decl.params,args):
            env.define(param.id.lexeme,interpreter.execute(arg))
        interpreter.execute(decl.block,env)
