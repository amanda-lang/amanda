from enum import Enum

class TokenType(Enum):
#Enum used to represents all the different
#tokens in the amanda grammar

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


    #LITERALS
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
    NEWLINE = "NEWLINE"


    #LOGIC OP
    LESS = "LESS"
    GREATER = "GREATER"
    LESSEQ = "LESSEQ"
    GREATEREQ = "GREATEREQ"
    NOTEQUAL = "NOTEQUAL"
    EQUAL = "EQUAL"
    DOUBLEEQUAL = "DOUBLEEQUAL"

    #KEYWORDS
    VAR = "VAR"
    MOSTRA = "MOSTRA"
    E = "E"
    OU = "OU"
    NAO = "NAO"
    VERDADEIRO = "VERDADEIRO"
    FALSO = "FALSO"
    RETORNA = "RETORNA"
    SE = "SE"
    SENAO = "SENAO"
    ENTAO = "ENTAO"
    ENQUANTO = "ENQUANTO"
    PARA = "PARA"
    FACA = "FACA"
    DE = "DE"
    INC = "INC"
    FIM = "FIM"
    FUNC = "FUNC"
    PROC = "PROC"
    NULO = "NULO"
    CLASSE = "CLASSE"



class Token:
    def __init__(self,token,lexeme,line=0,col=0):
        self.token = token
        self.lexeme = lexeme
        self.line = line
        self.col = col

    def __str__(self):
        return "<Type: %s, Lexeme: %s Line:%s>"%(self.token.value,self.lexeme,self.line)


def build_reserved_keywords():
    """Build a dictionary of reserved keywords.
    """
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.VAR)
    end_index = tt_list.index(TokenType.CLASSE)
    reserved_keywords = {
        token_type.value.lower(): Token(token_type,token_type.value.lower())
        for token_type in tt_list[start_index:end_index + 1]
    }
    return reserved_keywords

KEYWORDS = build_reserved_keywords()
if __name__ == "__main__":
    print(build_reserved_keywords())
