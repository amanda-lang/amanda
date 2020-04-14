from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT


'''*Class used to parse input file
   *Each method of this file is a rule defined in the grammar '''


class Parser:

    def __init__(self,lexer):
        self.lexer = lexer
        self.lookahead = lexer.get_token()
        #Start parsing from program
        self.program()

    def consume(self,token_t):
        if self.lookahead.token == token_t:
            print(f"Parser consumed {token_t}")
            self.lookahead = self.lexer.get_token()
        raise Exception(f"ParseError: expected {token_t.value} but got {self.lookahead.token.value}")

    def program(self):
        self.block()

    def block(self):
        current = self.lookahead.token
        if ( current in (TT.LPAR,TT.PLUS,
            TT.MINUS,TT.INTEGER) ):
            self.expression()
            self.consume(TT.SEMI)
            self.block()

        elif current == TT.MOSTRA:
            self.statement()
            self.consume(TT.SEMI)
            self.block()

    def statement(self):
        current = self.lookahead.token
        if current == TT.MOSTRA:
            self.mostra_statement()

    def mostra_statement(self):
        self.consume(TT.MOSTRA)
        self.expression()


    def expression(self):
        current = self.lookahead.token
        if current == TT.LPAR:
            self.consume(TT.LPAR)
            self.expression()
            self.consume(TT.RPAR)
            self.expression_end()

        elif current in (TT.PLUS,TT.MINUS):
            self.sign()
            self.expression()
            self.expression_end()

        elif current == TT.INTEGER:
            self.consume(TT.INTEGER)
            self.expression_end()
        else:
            raise Exception("ParseError: Illegal start of expression")


    def expression_end(self):
        current = self.lookahead.token
        if current in (TT.PLUS, TT.MINUS, TT.STAR, TT.SLASH, TT.MODULO):
            self.operator()
            self.expression()
            self.expression_end()

    def operator(self):
        current = self.lookahead.token
        if current in (TT.PLUS,TT.MINUS):
            self.sign()
        elif current == TT.STAR:
            self.consume(TT.STAR)
        elif current == TT.SLASH:
            self.consume(TT.SLASH)
        elif current == TT.MODULO:
            self.consume(TT.MODULO)


    def sign(self):
        current = self.lookahead.token
        if current == TT.PLUS:
            self.consume(TT.PLUS)
        elif current == TT.MINUS:
            self.consume(TT.MINUS)
