''' Base class for all PTScript errors '''
class Error(Exception):

    def __init__(self,message,line):
        self.message = message
        self.line = line


''' Errors that happens during lexing or parsing'''

class Syntax(Error):
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido"
    INVALID_STRING = "A sequência de caracteres não foi delimitada"
    MISSING_SEMI = "as instruções devem ser delimitadas por ';'"
    ILLEGAL_EXPRESSION = "início inválido de expressão"
    EXPECTED_ID = "era esperado um identificador depois do símbolo '{symbol}'"
    EXPECTED_TYPE = "era esperado um tipo depois do símbolo '{symbol}'"
    ILLEGAL_ASSIGN = "alvo inválido para atribuição"

    def __str__(self):
        return f"\nErro sintático na linha {self.line}: {self.message}.\n"


class RunTime(Error):
    def __str__(self):
        return f"\n\nErro de execução na linha {self.line}: {self.message}.\n\n"



if __name__=="__main__":
    error = Syntax(Error.INVALID_STRING,symbol="lool",line=3)
    print(error)
