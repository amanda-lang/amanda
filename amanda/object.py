
''' Module for all object classes used as runtime representations of user defined
and native language constructs (classes and functions).
Also contains other helper classes to be used at runtime
'''
from abc import ABC,abstractmethod
import copy


class ReturnValue(Exception):
    ''' Exception class used to return
    values from functions'''
    def __init__(self,value):
        self.value = value

class Environment:

    def __init__(self,name,previous=None):
        self.name = name
        self.previous = previous
        self.memory = {} # initialize it's env with it's own global mem space

    def define(self,name,value):
        self.memory[name] = value

    def resolve(self,name):
        value = self.memory.get(name)
        if value is None and self.previous:
            return self.previous.resolve(name)
        return value

    def resolve_space(self,name):
        if self.memory.get(name) != None:
            return self
        elif self.previous:
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
        previous = interpreter.memory
        #Hack for executing methods:
        #State of instance is passed in the env
        env = Environment(decl.name.lexeme,interpreter.memory)
        for param,arg in zip(decl.params,args):
            env.define(param.name.lexeme,arg)
        try:
            interpreter.run_block(decl.block,env) 
        except ReturnValue as e:
            interpreter.memory = env.previous
            return e.value
        

    def __str__(self):
        return f"{self.name}: Function object"



class AmaInstance:
    ''' Python class that represents an instance of an Amanda
        class.
        Instances are created by invoking the class.
        E.g: Texto("lool")
        '''  
    def __init__(self,klass,members):
        self.klass = klass
        self.members = members



class AmandaNull:
    ''' Class used as default value of uninitalized 
    object variables'''


    def __str__(self):
        return "nulo"


class AmandaMethod(AmaCallable):
    ''' Wrapper around a function defined inside
    a class. Used to link the function to the environment
    of an instance'''

    def __init__(self,instance,function):
        self.instance = instance
        self.function = function

    def call(self,interpreter,**kwargs):
        decl = self.function.declaration
        args = kwargs["args"]
        previous = interpreter.memory
        #Hack for executing methods:
        #State of instance is passed in the env
        env = Environment(decl.name.lexeme,self.instance.members)
        for param,arg in zip(decl.params,args):
            env.define(param.name.lexeme,arg)
        try:
            interpreter.run_block(decl.block,env)
            #Doing this because the previous env
            #of the instance might not be the same
            #as the last one in memory
            interpreter.memory = previous
        except ReturnValue as e:
            interpreter.memory = previous
            return e.value




class AmaClass(AmaCallable):

    def __init__(self,name,members,superclass=None):
        self.name = name
        self.members = members
        self.superclass = superclass

    def call(self,interpreter,**kwargs):
        return AmaInstance(self,copy.copy(self.members))

