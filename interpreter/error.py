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


class Analysis(Error):

    UNDEFINED_TYPE = "o tipo de dados '{type}' não foi definido"
    ID_IN_USE = "O identificador '{name}' já foi declarado neste escopo"
    NO_RETURN_STMT = "a função '{name}' não possui a instrução 'retorna'"
    REPEAT_PARAM = "o parâmetro '{name}' já foi especificado nesta função"
    UNDECLARED_ID ="o identificador '{name}' não foi declarado"
    INVALID_REF = "o identificador '{name}' não é uma referência válida"
    INVALID_OP = "os tipos '{t1}' e '{t2}' não suportam operações com o operador '{operator}'"
    INVALID_UOP = "o operador unário {operator} não pode ser usado com o tipo '{type}' "
    BAD_STR_OP = "o tipo 'texto' não suporta operações com o operador '{operator}'"
    



    def __str__(self):
        return f"\n\nErro na linha {self.line}: {self.message}.\n\n"


class RunTime(Error):
    def __str__(self):
        return f"\n\nErro na linha {self.line}: {self.message}.\n\n"



if __name__=="__main__":
    error = Syntax(Error.INVALID_STRING,symbol="lool",line=3)
    print(error)
