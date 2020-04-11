from tokens import TokenType,Token


class Lexer:
    EOF = "__eof__"

    def __init__(self,src_file):
        self.current_line = 1
        self.pos = -1
        self.file = open(src_file,"r")
        self.current_token = None
        self.current_char = self.file.read(1)

    def advance(self):
        self.current_char = self.file.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF

    def whitespace(self):
        while self.current_char.isspace() and self.current_char is not None:
            self.advance()

    def integer(self):
        result = ""
        while self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return int(result)

    def get_next_token(self):
        if self.current_char.isspace():
            self.whitespace()

        if self.current_char.isdigit():
            return Token(TokenType.INTEGER,self.integer())

        if self.current_char == "+":
            self.advance()
            return Token(TokenType.PLUS,"+")

        if self.current_char == "-":
            self.advance()
            return Token(TokenType.MINUS,"-")

        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF,"")

        raise TypeError




lexer = Lexer("test.pts")
token = lexer.get_next_token()

while token.token != Lexer.EOF:
    print(token)
    token = lexer.get_next_token()
