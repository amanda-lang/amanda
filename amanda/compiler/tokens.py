from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Dict


class TokenType(Enum):
    # Special eof token
    EOF = "_EOF_"
    # Special token used for program node
    PROGRAM = "PROGRAM"
    # Enum used to represents all the different
    # tokens in the amanda grammar

    # ARIT OPERATORS
    PLUS = "+"
    MINUS = "-"
    STAR = "*"
    SLASH = "/"
    DOUBLESLASH = "//"
    MODULO = "%"
    PLUSEQ = "+="
    MINUSEQ = "-="
    STAREQ = "*="
    SLASHEQ = "/="

    # LITERALS
    INTEGER = "inteiro"
    REAL = "real"
    STRING = "cadeia"
    FORMAT_STR = "cadeia formatada"
    IDENTIFIER = "identificador"

    # GENERAL P
    LPAR = "("
    RPAR = ")"
    DOT = "."
    DDOT = ".."
    SEMI = ";"
    COMMA = ","
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    COLON = ":"
    QMARK = "?"
    DOUBLECOLON = "::"
    NEWLINE = "\\n"

    # LOGIC OP
    LESS = "<"
    GREATER = ">"
    LESSEQ = "<="
    GREATEREQ = ">="
    NOTEQUAL = "!="
    EQUAL = "="
    DOUBLEEQUAL = "=="

    # KEYWORDS
    MOSTRA = "MOSTRA"
    E = "E"
    OU = "OU"
    NAO = "NAO"
    VERDADEIRO = "VERDADEIRO"
    FALSO = "FALSO"
    CASO = "CASO"
    RETORNA = "RETORNA"
    SE = "SE"
    SENAO = "SENAO"
    SENAOSE = "SENAOSE"
    ESCOLHA = "ESCOLHA"
    ENTAO = "ENTAO"
    ENQUANTO = "ENQUANTO"
    PARA = "PARA"
    FACA = "FACA"
    DE = "DE"
    CONTINUA = "CONTINUA"
    QUEBRA = "QUEBRA"
    USA = "USA"
    COMO = "como"
    ALVO = "alvo"
    REGISTO = "registo"
    INC = "INC"
    FIM = "FIM"
    FUNC = "FUNC"
    MET = "MET"
    NULO = "NULO"
    VAZIO = "VAZIO"
    NATIVA = "NATIVA"
    CLASSE = "CLASSE"


@dataclass
class Token:
    token: TokenType
    lexeme: str
    line: int = 0
    col: int = 0

    def __str__(self) -> str:
        return "<Type: %s, Lexeme: %s Line:%s>" % (
            self.token,
            self.lexeme,
            self.line,
        )


def build_reserved_keywords() -> Dict[str, Token]:
    """Build a dictionary of reserved keywords."""
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.MOSTRA)
    end_index = tt_list.index(TokenType.CLASSE)
    reserved_keywords = {
        token_type.value.lower(): Token(token_type, token_type.value.lower())
        for token_type in tt_list[start_index : end_index + 1]
    }
    return reserved_keywords


KEYWORDS = build_reserved_keywords()
