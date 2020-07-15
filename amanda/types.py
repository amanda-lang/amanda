import enum
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
        self.value = value

    def __str__(self):
        string = str(self.value)
        if isinstance(self.value,int):
            string = f"int -> {self.value}"
        elif isinstance(self.value,float):
            string = f"real -> {self.value}"
        elif isinstance(self.value,str):
            string = f"texto -> {self.value}"
        elif isinstance(self.value,Bool):
            string = f"bool -> {self.value}"
        return string 
        
