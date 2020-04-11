from tokens import TokenType,Token


class Lexer:
    EOF = "__eof__"
    def __init__(self,src_file):
        self.current_line = 1
        self.pos = -1
        self.file = open(src_file,"r")
        self.current_token = None
        self.current_char = self.file.read()

    def advance(self):
        self.current_char = self.file.read()
        if self.current_char = "":
            self.current_char = Lexer.EOF

    def whitespace(self):
        while self.current_char.isspace() and self.current_char is not None:
            self.advance()

    def integer(self):
        result = ""
        while self.current_char.isdigit():
            result += self.current_char
            self.advance()
        return result

    def get_next_token(self):
        if char.isspace():
            self.whitespace()

        if char.isdigit():
            return self.integer()

        if self.current_char == "+":
            self.advance()
            return Token(TokenType.PLUS,"+")

        if self.current_char == "-":
            self.advance()
            return Token(TokenType.MINUS,"-")

        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF,"")
