''' Base class for all PTScript errors '''
class Error(Exception):

    ILLEGAL_EXPRESSION = "Início inválido de expressão."
    ID_NOT_FOUND = "Identificador não declarado."
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido."
    INVALID_STRING = "A sequência de caracteres não foi delimitada."

    def __init__(self,message,line):
        self.message = message
        self.line = line


''' Errors that happens during lexing or parsing'''

class Syntax(Error):
    def __str__(self):
        return f"\nErro sintático na linha {self.line}: {self.message}\n"


class RunTime(Error):
    def __str__(self):
        return f"\n\nErro de execução na linha {self.line}: {self.message}.\n\n"



if __name__=="__main__":
    error = Syntax(Error.INVALID_STRING,symbol="lool",line=3)
    print(error)
