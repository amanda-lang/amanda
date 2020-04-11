from tokens import TokenType,Token


class Lexer:
    EOF = "__eof__"

    def __init__(self,src_file):
        self.line = 1
        self.pos = -1
        self.file = open(src_file,"r")
        self.current_token = None
        self.current_char = self.file.read(1)

    def advance(self):
        self.current_char = self.file.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF

    def Lookahead(self):
        last_position = self.file.tell()
        next_char = self.file.read(1)
        self.file.seek(last_position)
        return next_char

    def error(self):
        raise Exception("Error during lexing phase")



    def whitespace(self):
        while self.current_char.isspace() and self.current_char is not None:
            if self.current_char == "\n":
                self.line += 1
            self.advance()

    def arit_operators(self):
        if self.current_char == "+":
            self.advance()
            return Token(TokenType.PLUS,"+")

        elif self.current_char == "-":
            self.advance()
            return Token(TokenType.MINUS,"-")

        elif self.current_char == "*":
            self.advance()
            return Token(TokenType.STAR,"*")

        elif self.current_char == "/":
            self.advance()
            return Token(TokenType.SLASH,"/")

        elif self.current_char == "%":
            self.advance()
            return Token(TokenType.MODULO,"%")

    def logic_operators(self):
        if self.current_char == "<":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.LESSEQ,"<=")
            self.advance()
            return Token(TokenType.LESS,"<")

        elif self.current_char == ">":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.GREATEREQ,">=")
            self.advance()
            return Token(TokenType.GREATER,">")

        elif self.current_char == "=":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.DOUBLEEQUAL,"==")
            self.advance()
            return Token(TokenType.EQUAL,"=")

        elif self.current_char == "!":
            if self.Lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TokenType.NOTEQUAL,"!=")
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
            return Token(TokenType.DECIMAL,float(result))
        return Token(TokenType.INTEGER,int(result))



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
        return Token(TokenType.STRING,f"{symbol}{result}{symbol}")


    def identifier(self):
        result = ""
        while self.current_char.isalnum() or self.current_char == "_":
            result += self.current_char
            self.advance()
        if result == "decl":
            return Token(TokenType.DECL,"decl")
        return Token(TokenType.IDENTIFIER,result)

    def delimeters(self):
        char = self.current_char
        if self.current_char == ")":
            self.advance()
            return Token(TokenType.RPAR,char)
        elif self.current_char == "(":
            self.advance()
            return Token(TokenType.LPAR,char)
        elif self.current_char == ".":
            self.advance()
            return Token(TokenType.DOT,char)
        elif self.current_char == ";":
            self.advance()
            return Token(TokenType.SEMI,char)
        elif self.current_char == ",":
            self.advance()
            return Token(TokenType.COMMA,char)



    def get_next_token(self):
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
        if self.current_char in ["(",")",".",";",","]:
            return self.delimeters()

        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF,"")
        self.error()





if __name__ == "__main__":
    lexer = Lexer("test.pts")
    token = lexer.get_next_token()
    while token.token != Lexer.EOF:
        print(token)
        token = lexer.get_next_token()
