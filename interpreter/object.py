
''' Module for all object classes used as runtime representations of user defined
and native language constructs (classes and functions).
Also contains other helper classes to be used at runtime
'''
from abc import ABC,abstractmethod
from interpreter.semantic import Type


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

class Function(ABC):

    def __init__(self,name):
        self.name = name

    @abstractmethod
    def call(self,interpreter,**kwargs):
        pass


class RTFunction(Function):
    def __init__(self,name,declaration):
        self.name = name
        self.declaration = declaration

    def call(self,interpreter,**kwargs):
        decl = self.declaration
        args = kwargs["args"]
        env = Environment(decl.id.lexeme,interpreter.memory)
        for param,arg in zip(decl.params,args):
            env.define(param.id.lexeme,arg)
        interpreter.execute(decl.block,env)

    def __str__(self):
        return f"{self.name}: Function object"


class RTArray:

    def __init__(self,type,size=0):
        self.size = size
        self.elements = []
        if size <= 0:
            raise IndexError
        init = Type.VAZIO
        if type == Type.INT:
            init = 0
        elif type == Type.REAL:
            init = 0.0
        elif type == Type.TEXTO:
            init = ""
        elif type == Type.BOOL:
            init = False
        self.elements = [init for x in range(self.size)]

    def put(self,pos,element):
        if pos < 0 or pos > self.size - 1:
            raise IndexError
        self.elements[pos] = element

    def get(self,pos):
        if pos < 0 or pos > self.size - 1:
            raise IndexError
        return self.elements[pos]


#Class used as return values for functions
class ReturnValue(Exception):

    def __init__(self,value):
        self.value = value
