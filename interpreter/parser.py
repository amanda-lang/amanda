from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
from interpreter.error import ParserError,Error


'''*Class used to parse input file
   *Each method of this file is a rule defined in the grammar '''

class Parser:

    def __init__(self,lexer):
        self.lexer = lexer
        self.lookahead = lexer.get_token()

    def consume(self,token_t):
        if self.lookahead.token == token_t:
            print(f"Parser consumed {self.lookahead}")
            self.lookahead = self.lexer.get_token()
        else:
            self.error(f"O programa esperava o símbolo {token_t.value},porém recebeu o símbolo '{self.lookahead.lexeme}'")

    def error(self,message=None):
        raise ParserError(message,self.lexer.line)

    #function that triggers parsing
    def parse(self):
        return self.program()


    def program(self):
        program = AST.Program()
        start_first = (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,TT.DECL,TT.VECTOR,TT.DEFINA,
            TT.LBRACE)
        if self.lookahead.token in start_first or self.lookahead.token == Lexer.EOF:
            while self.lookahead.token in start_first:
                program.add_child(self.declaration())
            if self.lookahead.token == Lexer.EOF:
                return program
            else:
                self.error("Sintaxe inválida")
        else:
            self.error(f"Sintaxe inválida para início de programa {self.lookahead.token}")

    def declaration(self):
        if self.lookahead.token == TT.DECL:
            return self.var_decl()
        elif self.lookahead.token == TT.DEFINA:
            return self.function_decl()
        elif self.lookahead.token == TT.VECTOR:
            return self.array_decl()
        elif (self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,
            TT.LBRACE)):
            return self.statement()


    def var_decl(self):
        token = self.lookahead
        self.consume(TT.DECL)
        type = self.lookahead
        self.consume(TT.IDENTIFIER)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        assign = None
        if self.lookahead.token == TT.EQUAL:
            assign = self.lookahead
            self.consume(TT.EQUAL)
            right = self.expression()
            assign = AST.AssignNode(assign,left=AST.ExpNode(id),right=right)
        self.consume(TT.SEMI)
        return AST.VarDeclNode(token,id=id,type=type,assign=assign)

    def array_decl(self):
        token = self.lookahead
        self.consume(TT.VECTOR)
        type = self.lookahead
        self.consume(TT.IDENTIFIER)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        self.consume(TT.LBRACKET)
        size = self.equality()
        self.consume(TT.RBRACKET)
        self.consume(TT.SEMI)
        return AST.ArrayDeclNode(token,id=id,type=type,size=size)

    def function_decl(self):
        self.consume(TT.DEFINA)
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR)
        type = Token("VAZIO","vazio")
        if self.lookahead.token == TT.COLON:
            self.consume(TT.COLON)
            type = self.lookahead
            self.consume(TT.IDENTIFIER)
        block = self.block()
        return AST.FunctionDecl(id=id,block=block,type=type,params=params)

    def formal_params(self):
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            type = self.lookahead
            is_array = False
            self.consume(TT.IDENTIFIER)
            if self.lookahead.token == TT.LBRACKET:
                self.consume(TT.LBRACKET)
                self.consume(TT.RBRACKET)
                is_array = True
            id = self.lookahead
            self.consume(TT.IDENTIFIER)
            params.append(AST.ParamNode(type,id,is_array))
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                type = self.lookahead
                is_array = False
                self.consume(TT.IDENTIFIER)
                if self.lookahead.token == TT.LBRACKET:
                    self.consume(TT.LBRACKET)
                    self.consume(TT.RBRACKET)
                    is_array = True
                id = self.lookahead
                self.consume(TT.IDENTIFIER)
                params.append(AST.ParamNode(type,id,is_array=False))
        return params


    def statement(self):
        current = self.lookahead.token
        if (current in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT)):
            #expr_statement
            node = self.expression()
            self.consume(TT.SEMI)
        elif current == TT.MOSTRA:
            return self.mostra_statement()
        elif current == TT.RETORNA:
            return self.retorna_statement()
        elif current == TT.SE:
            return self.se_statement()
        elif current == TT.LBRACE:
            return self.block()
        else:
            self.error("Instrução inválida. Só pode fazer declarações dentro de blocos ou no escopo principal")

    def mostra_statement(self):
        token = self.lookahead
        self.consume(TT.MOSTRA)
        exp = self.equality()
        self.consume(TT.SEMI)
        return AST.Statement(token,exp)

    def retorna_statement(self):
        token = self.lookahead
        self.consume(TT.RETORNA)
        exp = self.equality()
        self.consume(TT.SEMI)
        return AST.Statement(token,exp)

    def se_statement(self):
        token = self.lookahead
        self.consume(TT.SE)
        self.consume(TT.LPAR)
        condition = self.equality()
        self.consume(TT.RPAR)
        then_branch = self.statement()
        else_branch = None
        if self.lookahead.token == TT.SENAO:
            self.consume(TT.SENAO)
            else_branch = self.statement()
        return AST.SeStatement(token,condition,then_branch,else_branch)

    def block(self):
        block = AST.Block()
        self.consume(TT.LBRACE)
        while ( self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,TT.DECL,TT.VECTOR,TT.DEFINA,
            TT.LBRACE) ):
            block.add_child(self.declaration())
        self.consume(TT.RBRACE)
        return block


    def eq_operator(self):
        current = self.lookahead.token
        if current == TT.DOUBLEEQUAL:
            self.consume(TT.DOUBLEEQUAL)
        elif current == TT.NOTEQUAL:
            self.consume(TT.NOTEQUAL)

    def expression(self):
        node = self.equality()
        current = self.lookahead.token
        if self.lookahead.token == TT.EQUAL:
            token = self.lookahead
            self.consume(TT.EQUAL)
            if isinstance(node,AST.ArrayRef) or (isinstance(node,AST.ExpNode) and node.token.token == TT.IDENTIFIER):
                node = AST.AssignNode(token,left=node,right=self.expression())
            else:
                self.error("Erro de atribuição. Só pode atribuir valores à variáveis e a índices de vector")
        return node


    def equality(self):
        node = self.comparison()
        while self.lookahead.token in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            op = self.lookahead
            self.eq_operator()
            node = AST.BinOpNode(op,left=node,right=self.comparison())
        return node

    def comp_operator(self):
        current = self.lookahead.token
        if current == TT.GREATER:
            self.consume(TT.GREATER)
        elif current == TT.GREATEREQ:
            self.consume(TT.GREATEREQ)
        elif current == TT.LESS:
            self.consume(TT.LESS)
        elif current == TT.LESSEQ:
            self.consume(TT.LESSEQ)


    def comparison(self):
        node = self.addition()
        while self.lookahead.token in (TT.GREATER,TT.GREATEREQ,TT.LESS,TT.LESSEQ):
            op = self.lookahead
            self.comp_operator()
            node = AST.BinOpNode(op,left=node,right=self.addition())
        return node

    def addition(self):
        node = self.term()
        while self.lookahead.token in (TT.PLUS,TT.MINUS,TT.OR):
            op = self.lookahead
            if self.lookahead.token == TT.OR:
                self.consume(TT.OR)
            else:
                self.add_operator()
            node = AST.BinOpNode(op,left=node,right=self.term())
        return node


    def term(self):
        node = self.factor()
        while self.lookahead.token in (TT.STAR,TT.SLASH,TT.MODULO,TT.AND):
            op = self.lookahead
            self.mult_operator()
            node = AST.BinOpNode(op,left=node,right=self.term())
        return node

    def factor(self):
        current = self.lookahead.token
        node = None
        if current in (TT.INTEGER,TT.REAL,TT.STRING,TT.IDENTIFIER,TT.VERDADEIRO,TT.FALSO):
            if current == TT.IDENTIFIER:
                token = self.lookahead
                self.consume(TT.IDENTIFIER)
                if self.lookahead.token == TT.LPAR:
                    node = AST.FunctionCall(id=token,fargs=self.function_call())
                elif self.lookahead.token == TT.LBRACKET:
                    self.consume(TT.LBRACKET)
                    node = AST.ArrayRef(id=token,index=self.equality())
                    self.consume(TT.RBRACKET)
                else:
                    node = AST.ExpNode(token)
            else:
                node = AST.ExpNode(self.lookahead)
                self.consume(current)
        elif current == TT.LPAR:
            self.consume(TT.LPAR)
            node = self.equality()
            self.consume(TT.RPAR)
        elif current in (TT.PLUS,TT.MINUS,TT.NOT):
            token = self.lookahead
            self.consume(current)
            node = AST.UnaryOpNode(token,operand=self.factor())
        else:
            self.error(f"{Error.ILLEGAL_EXPRESSION} causado pelo símbolo '{self.lookahead.lexeme}'" )
        return node

    def function_call(self):
        self.consume(TT.LPAR)
        current = self.lookahead.token
        args = []
        if ( current in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT) ):
            args.append(self.equality())
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                args.append(self.equality())
        self.consume(TT.RPAR)
        return args



    def mult_operator(self):
        current = self.lookahead.token
        if current == TT.AND:
            self.consume(TT.AND)
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
