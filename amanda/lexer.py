import os
import copy
from io import StringIO
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
from amanda.tokens import KEYWORDS as TK_KEYWORDS
from amanda.error import AmandaError

class Lexer:
    #Special end of file token
    EOF = "__eof__"
    #Errors that happen during tokenization
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido"
    INVALID_STRING = "A sequência de caracteres não foi delimitada"

    def __init__(self,src):
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None
        self.file = src # A file object

    @classmethod
    def string_lexer(cls,string):
        #Constructor to create a lexer with a string
        return cls(StringIO(string))

    def advance(self):
        if self.current_char == Lexer.EOF:
            return
        self.current_char = self.file.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF
        else:
            self.pos += 1

    def lookahead(self):
        last_position = self.file.tell()
        next_char = self.file.read(1)
        self.file.seek(last_position)
        return next_char

    def error(self,code,**kwargs):
        message = code.format(**kwargs)
        raise AmandaError.syntax_error(message,self.line,self.pos)

    def newline(self):
        pos = self.pos
        line = self.line
        self.line += 1
        self.pos = 1
        self.advance()
        return Token(TT.NEWLINE,"\\n",line,pos)

    def whitespace(self):
        while self.current_char!="\n" and \
        self.current_char.isspace()   and \
        self.current_char != Lexer.EOF:
            self.advance()
        if self.current_char == "#":
            self.comment()

    def comment(self):
        while self.current_char != "\n" and self.current_char != Lexer.EOF:
            self.advance()

    def arit_operators(self):
        if self.current_char == "+":
            return self.get_op_token(self.current_char,TT.PLUS,TT.PLUSEQ)
        elif self.current_char == "-":
            return self.get_op_token(self.current_char,TT.MINUS,TT.MINUSEQ)
        elif self.current_char == "*":
            return self.get_op_token(self.current_char,TT.STAR,TT.STAREQ)
        elif self.current_char == "/":
            return self.get_op_token(self.current_char,TT.SLASH,TT.SLASHEQ)
        elif self.current_char == "%":
            self.advance()
            return Token(TT.MODULO,"%",self.line,self.pos)

    def get_op_token(self,op_lexeme,normal_op,cmp_assign):
        if self.lookahead() == "=":
            self.advance()
            self.advance()
            return Token(cmp_assign,op_lexeme+"=",self.line,self.pos-1)

        if op_lexeme == "/" and self.lookahead() == "/":
            self.advance()
            normal_op = TT.DOUBLESLASH
            op_lexeme = "//"
        self.advance()
        return Token(normal_op,op_lexeme,self.line,self.pos)
 
    def comparison_operators(self):
        if self.current_char == "<":
            return self.get_op_token(self.current_char,TT.LESS,TT.LESSEQ)
        elif self.current_char == ">":
            return self.get_op_token(self.current_char,TT.GREATER,TT.GREATEREQ)
        elif self.current_char == "=":
            return self.get_op_token(self.current_char,TT.EQUAL,TT.DOUBLEEQUAL)
        elif self.current_char == "!":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TT.NOTEQUAL,"!=",self.line,self.pos-1)
            self.error(self.INVALID_SYMBOL,symbol=self.current_char)

    def number(self):
        result = ""
        while self.current_char.isdigit():
            result += self.current_char
            self.advance()
        if self.current_char == ".":
            #lookahead to see next char i
            if self.lookahead().isdigit():
                result += "."
                self.advance()
                while self.current_char.isdigit():
                    result += self.current_char
                    self.advance()
        if "." in result:
            return Token(
                        TT.REAL,float(result),
                        self.line,self.pos-(len(result)+1)
                    )

        return Token(
                    TT.INTEGER,
                    int(result),
                    self.line,
                    self.pos-(len(result)+1)
                )

    def string(self):
        result = ""
        symbol = self.current_char
        self.advance()
        while self.current_char != symbol :
            if self.current_char == Lexer.EOF:
                self.error(self.INVALID_STRING,line=self.line)
            result += self.current_char
            self.advance()
        self.advance()
        return Token(
                    TT.STRING,f"{symbol}{result}{symbol}",
                    self.line,
                    self.pos
                )

    def identifier(self):
        result = ""
        while self.current_char.isalnum() or self.current_char == "_":
            result += self.current_char
            self.advance()
        if TK_KEYWORDS.get(result) is not None:
            token = copy.copy(TK_KEYWORDS.get(result))
            token.line = self.line
            token.col = self.pos - (len(result) + 1)  
            return token
        return Token(
                        TT.IDENTIFIER,result,
                        self.line,
                        self.pos - (len(result) + 1)  
                    )

    def delimeters(self):
        char = self.current_char
        if self.current_char == ")":
            self.advance()
            return Token(TT.RPAR,char,self.line,self.pos)
        elif self.current_char == "(":
            self.advance()
            return Token(TT.LPAR,char,self.line,self.pos)
        elif self.current_char == ".":
            if self.lookahead() == ".":
                self.advance()
                self.advance()
                return Token(TT.DDOT,"..",self.line,self.pos - 1)
            self.advance()
            return Token(TT.DOT,char,self.line,self.pos)
        elif self.current_char == ";":
            self.advance()
            return Token(TT.SEMI,char,self.line,self.pos)
        elif self.current_char == ",":
            self.advance()
            return Token(TT.COMMA,char,self.line,self.pos)
        elif self.current_char == "{":
            self.advance()
            return Token(TT.LBRACE,char,self.line,self.pos)
        elif self.current_char == "}":
            self.advance()
            return Token(TT.RBRACE,char,self.line,self.pos)
        elif self.current_char == "[":
            self.advance()
            return Token(TT.LBRACKET,char,self.line,self.pos)
        elif self.current_char == "]":
            self.advance()
            return Token(TT.RBRACKET,char,self.line,self.pos)
        elif self.current_char == ":":
            self.advance()
            return Token(TT.COLON,char,self.line,self.pos)

    def get_token(self):
        if not self.current_char:
            self.advance()
        if self.current_char == "#":
            self.comment()
        if self.current_char != "\n" and self.current_char.isspace():
            self.whitespace()
        if self.current_char == "\n":
            return self.newline()
        if self.current_char in ("+","-","*","/","%"):
            return self.arit_operators()
        if self.current_char in ("<",">","!","="):
            return self.comparison_operators()
        if self.current_char.isdigit():
            return self.number()
        if self.current_char == "'" or self.current_char == '"':
            return self.string()
        if self.current_char.isalpha() or self.current_char == "_":
            return self.identifier()
        if self.current_char in ("(",")",".",";",",",
        "{","}","[","]",":"):
            return self.delimeters()
        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF,"")
        self.error(self.INVALID_SYMBOL,symbol=self.current_char)
