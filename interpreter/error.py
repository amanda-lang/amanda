''' Base class for all PTScript errors '''
class Error(Exception):

    ILLEGAL_EXPRESSION = "Início inválido de expressão"
    def __init__(self,message=None):
        self.message = message


''' Errors that happens during lexing or parsing'''


class LexerError(Error):
        pass


''' Errors thrown by the parser '''

class ParserError(Error):
    def __init__(self,message,line,symbol):
        self.message = message
        self.line = line
        self.symbol = symbol

    def __str__(self):
        return f"\n\nErro sintático na linha {self.line}: {self.message}. provocado por '{self.symbol}'\n\n"


class SemanticError(Error):
    pass
