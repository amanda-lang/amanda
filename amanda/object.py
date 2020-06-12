
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
        str = "\n".join([ f"{key} : {self.memory[key]}" for key in self.memory])
        return f"{self.name}\n{str}"

class AmaCallable(ABC):

    def __init__(self,name):
        self.name = name

    @abstractmethod
    def call(self,interpreter,**kwargs):
        pass

class RTFunction(AmaCallable):
    def __init__(self,name,declaration):
        self.name = name
        self.declaration = declaration

    def call(self,interpreter,**kwargs):
        decl = self.declaration
        args = kwargs["args"]
        env = Environment(decl.name.lexeme,interpreter.memory)
        for param,arg in zip(decl.params,args):
            env.define(param.name.lexeme,arg)
        interpreter.run_block(decl.block,env) 
    def __str__(self):
        return f"{self.name}: Function object"

#Class used as return values for functions
class ReturnValue(Exception):

    def __init__(self,value):
        self.value = value



class AmaClass(AmaCallable):

    def __init__(self,name,members,superclass=None):
        self.name = name
        self.members = members
        self.superclass = superclass

    def call(self,interpreter,**kwargs):
        pass
