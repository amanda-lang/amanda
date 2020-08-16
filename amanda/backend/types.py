import enum
from amanda.error import AmandaError
#Wrapper around boolean class
class Bool(enum.Enum):
    VERDADEIRO = True
    FALSO = False
    def __str__(self):
        return f"{self.name.lower()}"

    def __bool__(self):
        return self.value


class Indef:
    def __init__(self,value):
        if isinstance(value,Indef):
            value = value.value
        #TODO: Fix this awful hack
        elif isinstance(value,bool):
            value = Bool.VERDADEIRO if value else Bool.FALSO
        self.value = value

    def __str__(self):
        string = str(self.value)
        if isinstance(self.value,int):
            string = f"int -> {self.value}"
        elif isinstance(self.value,float):
            string = f"real -> {self.value}"
        elif isinstance(self.value,str):
            string = f"texto -> '{self.value}'"
        elif isinstance(self.value,Bool):
            string = f"bool -> {str(self.value)}"
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
