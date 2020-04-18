import os
import copy
from interpreter.tokens import TokenType,Token
from interpreter.tokens import KEYWORDS as TK_KEYWORDS
from interpreter.error import LexerError

class Lexer:
    EOF = "__eof__"

    def __init__(self,src_file):
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None
        if type(src_file).__name__ == type("string").__name__:
            self.file = open(src_file,"r")
        else:
            self.file = src_file
        self.advance()

    def advance(self):
        if self.current_char == Lexer.EOF:
            return
        self.current_char = self.file.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF
        else:
            self.pos += 1

    def Lookahead(self):
        last_position = self.file.tell()
        next_char = self.file.read(1)
        self.file.seek(last_position)
        return next_char

    def error(self,message):
        raise LexerError(f"O símbolo '{self.current_char}' não foi reconhecido",self.line)



    def whitespace(self):
        while self.current_char.isspace() and self.current_char != Lexer.EOF:
            if self.current_char == "\n":
                self.line += 1
                self.pos = 1
            self.advance()
        if self.current_char == "$":
            self.comment()

    def comment(self):
        if self.Lookahead() == "*":
            #Advance past *
            self.advance()
            self.advance()
            while True:
                if self.current_char == "*" and self.Lookahead()=="$":
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
            self.advance()
            return Token(TokenType.PLUS,"+",self.line,self.pos)

        elif self.current_char == "-":
            self.advance()
            return Token(TokenType.MINUS,"-",self.line,self.pos)

        elif self.current_char == "*":
            self.advance()
            return Token(TokenType.STAR,"*",self.line,self.pos)

        elif self.current_char == "/":
            self.advance()
            return Token(TokenType.SLASH,"/",self.line,self.pos)

        elif self.current_char == "%":
            self.advance()
            return Token(TokenType.MODULO,"%",self.line,self.pos)

    def logic_operators(self):
        if self.current_char == "<":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.LESSEQ,"<=",self.line,self.pos)
            self.advance()
            return Token(TokenType.LESS,"<",self.line,self.pos)

        elif self.current_char == ">":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.GREATEREQ,">=",self.line,self.pos)
            self.advance()
            return Token(TokenType.GREATER,">",self.line,self.pos)

        elif self.current_char == "=":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.DOUBLEEQUAL,"==",self.line,self.pos)
            self.advance()
            return Token(TokenType.EQUAL,"=",self.line,self.pos)

        elif self.current_char == "!":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.NOTEQUAL,"!=",self.line,self.pos)
            self.error()


    def number(self):
        result = ""
        while self.current_char.isdigit():
            result += self.current_char
            self.advance()
        if self.current_char == ".":
            #Lookahead to see next char i
            if self.Lookahead().isdigit():
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
                self.error()
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
        self.error("Error during tokenization")
