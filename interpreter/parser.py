from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST



'''*Class used to parse input file
   *Each method of this file is a rule defined in the grammar '''


class Parser:

    def __init__(self,lexer):
        self.lexer = lexer
        self.lookahead = lexer.get_token()
        self.program_tree = None

    def consume(self,token_t):
        if self.lookahead.token == token_t:
            print(f"Parser consumed {self.lookahead}")
            self.lookahead = self.lexer.get_token()
        else:
            raise Exception(f"ParseError: expected {token_t.value} but got {self.lookahead} on line {self.lexer.line}")

    #function that triggers parsing
    def parse(self):
        self.program_tree = self.program()
        return self.program_tree

    def program(self):
        return self.block()

    def block(self):
        block_node = AST.Block()
        while ( self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.MOSTRA,TT.RETORNA,
                TT.DECL,TT.IDENTIFIER,TT.DEFINA,TT.VECTOR,
                TT.REAL,TT.STRING,TT.PLUS,TT.MINUS) ):
            if (self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.REAL,TT.STRING,
                TT.IDENTIFIER,TT.PLUS,TT.MINUS)):
                block_node.add_child(self.expression())
                self.consume(TT.SEMI)
            elif self.lookahead.token in (TT.MOSTRA,TT.RETORNA,TT.DECL,TT.VECTOR):
                block_node.add_child(self.statement())
                self.consume(TT.SEMI)
            elif self.lookahead.token == TT.DEFINA:
                block_node.add_child(self.function_decl())
        return block_node

    def statement(self):
        current = self.lookahead.token
        if current in (TT.DECL,TT.VECTOR):
            return self.declaration()
        if current == TT.MOSTRA:
            return self.mostra_statement()
        elif current == TT.RETORNA:
            return self.retorna_statement()

    def declaration(self):
        current = self.lookahead.token
        if current == TT.DECL:
            return self.var_decl()
        elif current == TT.VECTOR:
            return self.array_decl()

    def var_decl(self):
        token = self.lookahead
        self.consume(TT.DECL)
        type = self.lookahead
        self.consume(TT.IDENTIFIER)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        if self.lookahead.token == TT.EQUAL:
            assign = self.lookahead
            self.consume(TT.EQUAL)
            right = self.expression()
            assign = AST.AssignNode(assign,left=id,right=right)
            return AST.VarDeclNode(token,id=id,type=type,assign=assign)
        return AST.VarDeclNode(token,id=id,type=type)

    def array_decl(self):
        token = self.lookahead
        self.consume(TT.VECTOR)
        type = self.lookahead
        self.consume(TT.IDENTIFIER)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        self.consume(TT.LBRACKET)
        size = self.expression()
        self.consume(TT.RBRACKET)
        return AST.ArrayDeclNode(token,id=id,type=type,size=size)


    def mostra_statement(self):
        token = self.lookahead
        self.consume(TT.MOSTRA)
        exp = self.expression()
        return AST.Statement(token,exp)

    def retorna_statement(self):
        token = self.lookahead
        self.consume(TT.RETORNA)
        exp = self.expression()
        return AST.Statement(token,exp)



    def expression(self):
        node = self.term()
        current = self.lookahead.token
        while self.lookahead.token in (TT.PLUS,TT.MINUS):
            op = self.lookahead
            self.add_operator()
            node = AST.BinOpNode(op,left=node,right=self.term())
        return node

    def term(self):
        node = self.factor()
        while self.lookahead.token in (TT.STAR,TT.SLASH,TT.MODULO):
            op = self.lookahead
            self.mult_operator()
            node = AST.BinOpNode(op,left=node,right=self.term())
        return node

    def factor(self):
        current = self.lookahead.token
        node = None
        if current in (TT.INTEGER,TT.REAL,TT.STRING,TT.IDENTIFIER):
            if current == TT.IDENTIFIER:
                token = self.lookahead
                self.consume(TT.IDENTIFIER)
                if self.lookahead.token == TT.LPAR:
                    node = AST.FunctionCall(id=token,fargs=self.function_call())
                elif self.lookahead.token == TT.LBRACKET:
                    self.consume(TT.LBRACKET)
                    node = AST.ArrayRef(id=token,index=self.expression())
                    self.consume(TT.RBRACKET)
                    if self.lookahead.token ==TT.EQUAL:
                        token = self.lookahead
                        self.consume(TT.EQUAL)
                        node = AST.AssignNode(token,left=node,right=self.expression())
                elif self.lookahead.token == TT.EQUAL:
                    equal = self.lookahead
                    self.consume(TT.EQUAL)
                    node = AST.AssignNode(token=equal,left=token,right=self.expression())
                else:
                    node = AST.ExpNode(token)
            else:
                node = AST.ExpNode(self.lookahead)
                self.consume(current)
        elif current == TT.LPAR:
            self.consume(TT.LPAR)
            node = self.expression()
            self.consume(TT.RPAR)
        elif current in (TT.PLUS,TT.MINUS):
            token = self.lookahead
            self.consume(current)
            node = AST.UnaryOpNode(token,operand=self.factor())
        else:
            raise Exception("ParseError: Illegal start of expression")
        return node

    def function_call(self):
        self.consume(TT.LPAR)
        current = self.lookahead.token
        args = []
        if ( current in (TT.LPAR,TT.INTEGER,TT.MOSTRA,TT.RETORNA,
            TT.DECL,TT.IDENTIFIER,TT.DEFINA,TT.VECTOR,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS) ):
            args.append(self.expression())
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                args.append(self.expression())
        self.consume(TT.RPAR)
        return args

    def function_decl(self):
        self.consume(TT.DEFINA)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR)
        type = None
        if self.lookahead.token == TT.COLON:
            self.consume(TT.COLON)
            type = self.lookahead
            self.consume(TT.IDENTIFIER)
        self.consume(TT.LBRACE)
        block = self.function_block()
        self.consume(TT.RBRACE)
        return AST.FunctionDecl(id=id,block=block,type=type,params=params)


    def formal_params(self):
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            type = self.lookahead
            self.consume(TT.IDENTIFIER)
            id = self.lookahead
            self.consume(TT.IDENTIFIER)
            params.append(AST.ParamNode(type,id))
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                type = self.lookahead
                self.consume(TT.IDENTIFIER)
                id = self.lookahead
                self.consume(TT.IDENTIFIER)
                params.append(AST.ParamNode(type,id))
        return params

    def function_block(self):
        block_node = AST.Block()
        while ( self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.MOSTRA,TT.RETORNA,
                TT.IDENTIFIER,TT.VECTOR,TT.REAL,
                TT.STRING,TT.PLUS,TT.MINUS) ):
            if (self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.REAL,TT.STRING,
                TT.IDENTIFIER,TT.PLUS,TT.MINUS)):
                block_node.add_child(self.expression())
            elif self.lookahead.token in (TT.MOSTRA,TT.RETORNA,TT.DECL,TT.VECTOR):
                block_node.add_child(self.statement())
            self.consume(TT.SEMI)
        return block_node


    def mult_operator(self):
        current = self.lookahead.token
        if current == TT.STAR:
            self.consume(TT.STAR)
        elif current == TT.SLASH:
            self.consume(TT.SLASH)
        elif current == TT.MODULO:
            self.consume(TT.MODULO)


    def add_operator(self):
        current = self.lookahead.token
        if current == TT.PLUS:
            self.consume(TT.PLUS)
        elif current == TT.MINUS:
            self.consume(TT.MINUS)


'''
*interpreter class contains everything needed
*to run a PTScript
*it is a high-level interpreter and it is
* not designed for powerful stuff
'''

class PTInterpreter(AST.Visitor):

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()

    def execute(self):
        self.visit(self.program)

    def visit_Binopnode(self,node):
        pass
