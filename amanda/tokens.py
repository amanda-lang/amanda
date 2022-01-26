from enum import Enum


class TokenType(Enum):
    # Enum used to represents all the different
    # tokens in the amanda grammar

    # ARIT OPERATORS
    PLUS = "PLUS"
    MINUS = "MINUS"
    STAR = "STAR"
    SLASH = "SLASH"
    DOUBLESLASH = "DOUBLESLASH"
    MODULO = "MODULO"
    PLUSEQ = "PLUSEQ"
    MINUSEQ = "MINUSEQ"
    STAREQ = "STAREQ"
    SLASHEQ = "SLASHEQ"

    # LITERALS
    INTEGER = "INTEGER"
    REAL = "REAL"
    STRING = "STRING"
    IDENTIFIER = "IDENTIFIER"

    # GENERAL P
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
    LESS = "LESS"
    GREATER = "GREATER"
    LESSEQ = "LESSEQ"
    GREATEREQ = "GREATEREQ"
    NOTEQUAL = "NOTEQUAL"
    EQUAL = "EQUAL"
    DOUBLEEQUAL = "DOUBLEEQUAL"

    # KEYWORDS
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
    CONVERTE = "CONVERTE"
    FACA = "FACA"
    DE = "DE"
    EU = "EU"
    SUPER = "SUPER"
    INC = "INC"
    FIM = "FIM"
    FUNC = "FUNC"
    INCLUA = "INCLUA"
    COMO = "COMO"
    NULO = "NULO"
    VAZIO = "VAZIO"
    CLASSE = "CLASSE"


class Token:
    def __init__(self, token, lexeme, line=0, col=0):
        self.token = token
        self.lexeme = lexeme
        self.line = line
        self.col = col

    def __str__(self):
        return "<Type: %s, Lexeme: %s Line:%s>" % (
            self.token.value,
            self.lexeme,
            self.line,
        )


def build_reserved_keywords():
    """Build a dictionary of reserved keywords."""
    tt_list = list(TokenType)
    assert (
        len(tt_list) == 58
    ), "New unhandled token. Please update the count here!"
    start_index = tt_list.index(TokenType.MOSTRA)
    end_index = tt_list.index(TokenType.CLASSE)
    reserved_keywords = {
        token_type.value.lower(): Token(token_type, token_type.value.lower())
        for token_type in tt_list[start_index : end_index + 1]
    }
    return reserved_keywords


KEYWORDS = build_reserved_keywords()
