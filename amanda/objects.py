import enum
from amanda.error import AmandaError

class Indef:
    def __init__(self,value):
        if isinstance(value,Indef):
            value = value.value
        self.value = value

    def __str__(self):
        string = str(self.value)
        value_type = type(self.value)
        if value_type == int:
            string = f"int -> {self.value}"
        elif value_type == float:
            string = f"real -> {self.value}"
        elif value_type == str:
            string = f"texto -> '{self.value}'"
        elif value_type == bool:
            value = "verdadeiro" if self.value else "falso"
            string = f"bool -> {value}"
        return string 

class Lista:
    def __init__(self,subtype,elements=[]):
        self.elements = elements
        self.subtype = subtype

    def __getitem__(self,key):
        try:
            return self.elements[key]
        except IndexError:
            raise AmandaError(
                "índice de lista inválido",-1
            )

    def __setitem__(self,key,value):
        try:
            if key < 0:
                raise IndexError
            self.elements[key] = value
        except IndexError:
            raise AmandaError(
                "índice de lista inválido",-1
            )

class BaseClass:
    def __init__(self,*args):
        class_dict = self.__class__.__dict__
        for key,value in class_dict.items():
            #Skip special attributes and functions 
            if key.startswith("__") or callable(value):
                continue
            setattr(self,key,value)

        instance_dict = self.__dict__
        for key,initializer in zip(instance_dict,args):
            setattr(self,key,initializer)
            
class Nulo:
    def __getattr__(self,attr):
        raise AmandaError("Não pode aceder uma referência nula",-1)
    def __str__(self):
        return "nulo"
