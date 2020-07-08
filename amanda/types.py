import enum
#Wrapper around boolean class
class Bool(enum.Enum):
    VERDADEIRO = True
    FALSO = False
    def __str__(self):
        return f"{self.name.lower()}"
    def __bool__(self):
        return self.value
