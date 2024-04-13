from __future__ import annotations
from enum import Enum
from dataclasses import dataclass
from typing import ClassVar, Dict


class TokenType(Enum):
    # Special eof token
    EOF = "_EOF_"
    # Special token used for program node
    PROGRAM = "PROGRAM"

    # LITERALS
    INTEGER = "inteiro"
    REAL = "real"
    STRING = "cadeia"
    FORMAT_STR = "cadeia formatada"
    IDENTIFIER = "identificador"

    # DELIMETERS
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
    AT = "@"
    COLON = ":"
    QMARK = "?"
    DOUBLECOLON = "::"
    ARROW = "=>"
    NEWLINE = "\\n"

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


def build_tokens_dict() -> Dict[str, TokenType]:
    """Build a dictionary of reserved keywords."""
    tt_list = list(TokenType)
    start_index = tt_list.index(TokenType.LPAR)
    end_index = tt_list.index(TokenType.DOUBLEEQUAL)

    return {
        token_type.value.lower(): token_type
        for token_type in tt_list[start_index : end_index + 1]
    }


@dataclass
class Token:
    token: TokenType
    lexeme: str
    line: int = 0
    col: int = 0
    TOKENS: ClassVar[dict[str, TokenType]] = build_tokens_dict()

    @classmethod
    def from_char(cls, char: str, line: int, col: int) -> Token | None:

        return (
            Token(Token.TOKENS[char], char, line, col)
            if char in Token.TOKENS
            else None
        )

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


_ambiguous_chars = [
    tt.value[0]
    for tt in TokenType
    if len(tt.value) > 1 and tt.value in Token.TOKENS
]


def is_ambiguous_char(char: str) -> bool:

    return char in _ambiguous_chars


KEYWORDS = build_reserved_keywords()
