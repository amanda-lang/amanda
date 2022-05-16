from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import Dict


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
    FORMAT_STR = "FORMAT_STR"
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
    DOUBLECOLON = "DOUBLECOLON"
    NEWLINE = "NEWLINE"

    # LOGIC OP
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
    EU = "EU"
    SUPER = "SUPER"
    INC = "INC"
    FIM = "FIM"
    FUNC = "FUNC"
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
