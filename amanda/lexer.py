import os
import copy
from io import StringIO
from amanda.tokens import TokenType,Token
from amanda.tokens import KEYWORDS as TK_KEYWORDS
import amanda.error as error

class Lexer:
    EOF = "__eof__"

    def __init__(self,file):
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None
        self.file = file # A file object


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
        print(kwargs)
        message = code.format(**kwargs)
        raise error.Syntax(message,self.line)



    def whitespace(self):
        while self.current_char.isspace() and self.current_char != Lexer.EOF:
            if self.current_char == "\n":
                self.line += 1
                self.pos = 1
            self.advance()
        if self.current_char == "$":
            self.comment()

    def comment(self):
        if self.lookahead() == "*":
            #Advance past *
            self.advance()
            self.advance()
            while True:
                if self.current_char == "*" and self.lookahead()=="$":
                    #Advance twice to skip  * and $
                    self.advance()
                    self.advance()
                    if self.current_char.isspace():
                        self.whitespace()
                    break
                elif self.current_char == Lexer.EOF:
                    break
                elif self.current_char == "\n":
                    self.whitespace()
                self.advance()

        else:
            while self.current_char != "\n" and self.current_char != Lexer.EOF:
                self.advance()
            if self.current_char == "\n":
                self.whitespace()



    def arit_operators(self):
        if self.current_char == "+":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.PLUSEQ,"+=",self.line,self.pos)
            self.advance()
            return Token(TokenType.PLUS,"+",self.line,self.pos)

        elif self.current_char == "-":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.MINUSEQ,"-=",self.line,self.pos)
            self.advance()
            return Token(TokenType.MINUS,"-",self.line,self.pos)

        elif self.current_char == "*":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.STAREQ,"*=",self.line,self.pos)
            self.advance()
            return Token(TokenType.STAR,"*",self.line,self.pos)

        elif self.current_char == "/":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.SLASHEQ,"/=",self.line,self.pos)
            self.advance()
            return Token(TokenType.SLASH,"/",self.line,self.pos)

        elif self.current_char == "%":
            self.advance()
            return Token(TokenType.MODULO,"%",self.line,self.pos)

    def logic_operators(self):
        if self.current_char == "<":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.LESSEQ,"<=",self.line,self.pos)
            self.advance()
            return Token(TokenType.LESS,"<",self.line,self.pos)

        elif self.current_char == ">":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.GREATEREQ,">=",self.line,self.pos)
            self.advance()
            return Token(TokenType.GREATER,">",self.line,self.pos)

        elif self.current_char == "=":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.DOUBLEEQUAL,"==",self.line,self.pos)
            self.advance()
            return Token(TokenType.EQUAL,"=",self.line,self.pos)

        elif self.current_char == "!":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.NOTEQUAL,"!=",self.line,self.pos)
            self.advance()
            return Token(TokenType.NOT,"!",self.line,self.pos)


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
            return Token(TokenType.REAL,float(result),self.line,self.pos)
        return Token(TokenType.INTEGER,int(result),self.line,self.pos)



    def string(self):
        result = ""
        symbol = self.current_char
        self.advance()
        while self.current_char != symbol :
            if self.current_char == Lexer.EOF:
                self.error(error.Syntax.INVALID_STRING,line=self.line)
            result += self.current_char
            self.advance()
        self.advance()
        return Token(TokenType.STRING,f"{symbol}{result}{symbol}",self.line,self.pos)


    def identifier(self):
        result = ""
        while self.current_char.isalnum() or self.current_char == "_":
            result += self.current_char
            self.advance()
        if TK_KEYWORDS.get(result) is not None:
            token = copy.copy(TK_KEYWORDS.get(result))
            token.line = self.line
            token.col = self.pos
            return token
        return Token(TokenType.IDENTIFIER,result,self.line,self.pos)

    def delimeters(self):
        char = self.current_char
        if self.current_char == ")":
            self.advance()
            return Token(TokenType.RPAR,char,self.line,self.pos)
        elif self.current_char == "(":
            self.advance()
            return Token(TokenType.LPAR,char,self.line,self.pos)
        elif self.current_char == ".":
            if self.lookahead() == ".":
                self.advance()
                self.advance()
                return Token(TokenType.DDOT,"..",self.line,self.pos)
            self.advance()
            return Token(TokenType.DOT,char,self.line,self.pos)
        elif self.current_char == ";":
            self.advance()
            return Token(TokenType.SEMI,char,self.line,self.pos)
        elif self.current_char == ",":
            self.advance()
            return Token(TokenType.COMMA,char,self.line,self.pos)
        elif self.current_char == "{":
            self.advance()
            return Token(TokenType.LBRACE,char,self.line,self.pos)
        elif self.current_char == "}":
            self.advance()
            return Token(TokenType.RBRACE,char,self.line,self.pos)
        elif self.current_char == "[":
            self.advance()
            return Token(TokenType.LBRACKET,char,self.line,self.pos)
        elif self.current_char == "]":
            self.advance()
            return Token(TokenType.RBRACKET,char,self.line,self.pos)
        elif self.current_char == ":":
            self.advance()
            return Token(TokenType.COLON,char,self.line,self.pos)


    def get_token(self):
        if not self.current_char:
            self.advance()

        if self.current_char == "$":
            self.comment()

        if self.current_char.isspace():
            self.whitespace()
        #arit_operators
        if self.current_char in ["+","-","*","/","%"]:
            return self.arit_operators()

        #logic ops
        if self.current_char in ["<",">","!","="]:
            return self.logic_operators()

        #numbers (real and integer)
        if self.current_char.isdigit():
            return self.number()

        #Strings
        if self.current_char == "'" or self.current_char == '"':
            return self.string()

        #Ids
        if self.current_char.isalpha() or self.current_char == "_":
            return self.identifier()

        #delims
        if ( self.current_char in ( "(",")",".",";",","
            ,"{","}","[","]",":" ) ):
            return self.delimeters()

        if self.current_char == Lexer.EOF:
            if self.file.readable():
                self.file.close()
            return Token(Lexer.EOF,"")
        self.error(error.Syntax.INVALID_SYMBOL,symbol=self.current_char)
