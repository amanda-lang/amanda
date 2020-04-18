''' Base class for all PTScript errors '''
class Error(Exception):

    ILLEGAL_EXPRESSION = "Início inválido de expressão"
    ID_NOT_FOUND = "Identificador não declarado"
    
    def __init__(self,message,line):
        self.message = message
        self.line = line


''' Errors that happens during lexing or parsing'''


class LexerError(Error):
    def __str__(self):
        return f"\n\nErro sintático na linha {self.line}: {self.message}.\n\n"



''' Errors thrown by the parser '''

class ParserError(Error):

    def __str__(self):
        return f"\n\nErro sintático na linha {self.line}: {self.message}.\n\n"


class SemanticError(Error):
    def __str__(self):
        return f"\n\nErro semântico na linha {self.line}: {self.message}.\n\n"
