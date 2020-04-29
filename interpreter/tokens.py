from enum import Enum

class TokenType(Enum):
    #ARIT OPERATORS
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    MODULO = "%"
    PLUSEQ = "PLUSEQ"
    MINUSEQ = "MINUSEQ"
    STAREQ = "STAREQ"
    SLASHEQ = "SLASHEQ"


    #OPERANDS
    INTEGER = "INTEGER"
    REAL = "REAL"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"

    #GENERAL P
    LPAR = "LPAR"
    RPAR = "RPAR"
    DOT = "DOT"
    DDOT = "DDOT"
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
    AND = "AND"
    OR = "OR"
    NOT = "NOT"

    #KEYWORDS
    DECL = "DECL"
    MOSTRA = "MOSTRA"
    VERDADEIRO = "VERDADEIRO"
    FALSO = "FALSO"
    RETORNA = "RETORNA"
    DEFINA = "DEFINA"
    VECTOR = "VECTOR"
    SE = "SE"
    SENAO = "SENAO"
    ENTAO = "ENTAO"
    ENQUANTO = "ENQUANTO"
    PARA = "PARA"
    INC = "INC"
    DE = "DE"
    FACA = "FACA"

class Token:
    def __init__(self,token,lexeme,line=0,col=0):
        self.token = token
        self.lexeme = lexeme
        self.line = line
        self.col = col

    def __str__(self):
        return "<Type: %s, Lexeme: %s Line:%s>"%(self.token.value,self.lexeme,self.line)

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
    "vector" : Token(TokenType.VECTOR,"vector"),
    "inc": Token(TokenType.INC,"inc"),
    "e" : Token(TokenType.AND,"e"),
    "ou" : Token(TokenType.OR,"ou"),
    "de" : Token(TokenType.DE,"de"),
    "se" : Token(TokenType.SE,"se"),
    "senao" : Token(TokenType.SENAO,"senao"),
    "entao": Token(TokenType.ENTAO,"entao"),
    "enquanto" : Token(TokenType.ENQUANTO,"enquanto"),
    "para" : Token(TokenType.PARA,"para"),
    "faca" : Token(TokenType.FACA,"faca"),
}
