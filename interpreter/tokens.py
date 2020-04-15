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
    LBRACE = "LBRACE"
    RBRACE = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COLON = "COLON"
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
    VERDADEIRO = "VERDADEIRO"
    FALSO = "FALSO"
    RETORNA = "RETORNA"
    DEFINA = "DEFINA"

class Token:
    def __init__(self,token,lexeme):
        self.token = token
        self.lexeme = lexeme

    def __str__(self):
        return "<Type: %s, Lexeme: %s>"%(self.token.value,self.lexeme)

KEYWORDS = {
    "decl" : Token(TokenType.DECL,"decl"),
    "defina" : Token(TokenType.DEFINA,"defina"),
    "def" : Token(TokenType.DEFINA,"def"),
    "declara": Token(TokenType.DECL,"declara"), #Same as decl
    "mostra": Token(TokenType.MOSTRA,"mostra"),
    "verdadeiro": Token(TokenType.VERDADEIRO,"verdadeiro"),
    "falso": Token(TokenType.FALSO,"falso"),
    "recebe": Token(TokenType.EQUAL,"recebe") , # same as equals
    "retorna": Token(TokenType.RETORNA,"retorna"),
}
