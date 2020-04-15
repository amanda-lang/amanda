from enum import Enum

class TokenType(Enum):
    #ARIT OPERATORS
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    MODULO = "%"

    #OPERANDS
    INTEGER = "INTEGER"
    REAL = "REAL"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"

    #GENERAL P
    LPAR = "LPAR"
    RPAR = "RPAR"
    DOT = "DOT"
    SEMI = "SEMI"
    COMMA = "COMMA"

    #LOGIC OP
    LESS = "LESS"
    GREATER = "GREATER"
    LESSEQ = "LESSEQ"
    GREATEREQ = "GREATEREQ"
    NOTEQUAL = "NOTEQUAL"
    EQUAL = "EQUAL"
    DOUBLEEQUAL = "DOUBLEEQUAL"

    #KEYWORDS
    DECL = "DECL"
    MOSTRA = "MOSTRA"

class Token:
    def __init__(self,token,lexeme):
        self.token = token
        self.lexeme = lexeme

    def __str__(self):
        return "<Type: %s, Lexeme: %s>"%(self.token.value,self.lexeme)
