from enum import Enum

class TokenType(Enum):
    PLUS = "PLUS"
    MINUS = "MINUS"
    INTEGER = "INTEGER"


class Token:
    def __init__(self,token,lexeme):
        self.token = token
        self.lexeme = lexeme

    def __str__(self):
        return "<Type: %s, Lexeme: %s>"%(self.token.value,self.lexeme)
