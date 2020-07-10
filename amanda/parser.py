from amanda.lexer import Lexer
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
import amanda.ast_nodes as AST
from amanda.error import AmandaError


class Parser:
    #Errors messages
    MISSING_TERM = "as instruções devem ser delimitadas por ';' ou por uma nova linha"
    ILLEGAL_EXPRESSION = "início inválido de expressão"
    EXPECTED_ID = "era esperado um identificador depois do símbolo '{symbol}'"
    EXPECTED_TYPE = "era esperado um tipo depois do símbolo '{symbol}'"
    ILLEGAL_ASSIGN = "alvo inválido para atribuição"

    def __init__(self,io_object):
        self.lexer = Lexer(io_object)
        self.lookahead = self.lexer.get_token()

    def consume(self,expected,error=None):
        if self.lookahead.token == expected:
            consumed = self.lookahead
            self.lookahead = self.lexer.get_token()
            return consumed
        else:
            if error:
                self.error(error)
            self.error(f"era esperado o símbolo {expected.value},porém recebeu o símbolo '{self.lookahead.lexeme}'")

    def error(self,message):
        raise AmandaError.syntax_error(
             message,self.lookahead.line,
             self.lookahead.col
         )

    def parse(self):
        return self.program()

    def match(self,token):
        return self.lookahead.token == token

    def program(self):
        program = AST.Program() 
        while not self.match(Lexer.EOF):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                child = self.declaration()
                self.append_child(program,child)
        return program

    def block(self):
        block = AST.Block()
        #SENAO is because of if statements
        while not self.match(TT.FIM) and not self.match(TT.SENAO):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                child = self.declaration()
                self.append_child(block,child)
        return block

    def append_child(self,body,child):
        ''' Method for desugaring
        multiple statement'''
        if isinstance(child,list):
            body.children += child
        else:
            body.add_child(child)

    def declaration(self):
        if self.match(TT.FUNC):
            return self.function_decl()
        elif self.match(TT.CLASSE):
            return self.class_decl()
        else:
            return self.statement()

    def type(self):
        return self.consume(TT.IDENTIFIER)
    
    def end_stmt(self):
        if self.match(TT.NEWLINE):
            self.consume(TT.NEWLINE)
        elif self.match(TT.SEMI):
            self.consume(TT.SEMI)
        else:
            self.error(self.MISSING_TERM)

    def function_decl(self):
        self.consume(TT.FUNC)
        name = self.consume(
            TT.IDENTIFIER,self.EXPECTED_ID.format(symbol="func")
        )
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR,"os parâmetros da função devem estar delimitados por  ')'")
        func_type = None
        if self.match(TT.COLON):
            self.consume(TT.COLON)
            if self.match(TT.VAZIO): #REMOVE: Maybe remove this
                self.consume(TT.VAZIO)
            else:
                func_type = self.type()
        block = self.block()
        self.consume(TT.FIM,"O corpo de um função deve ser terminado com a directiva 'fim'")
        return AST.FunctionDecl(name=name,block=block,func_type=func_type,params=params)

    #REMOVE: Not sure if superclasses are going
    # to be a thing
    def get_superclass(self):
        #Helper to parse classes with inheritance
        #syntax
        superclass = None
        if self.match(TT.LESS):
            self.consume(TT.LESS)
            superclass = self.lookahead 
            self.consume(TT.IDENTIFIER)
        return superclass

    #REMOVE: Not sure if class syntax will be the same
    def class_decl(self):
        self.consume(TT.CLASSE)
        name = self.lookahead
        self.consume(TT.IDENTIFIER)
        superclass = self.get_superclass()
        body = self.class_body()
        self.consume(TT.FIM,"O corpo de uma classe deve ser terminado com o símbolo fim")
        return AST.ClassDecl(name=name,superclass=superclass,body=body)

    #REMOVE: Not sure if class syntax will be the same
    def class_body(self):
        body = AST.ClassBody()
        while not self.match(TT.FIM):
            if self.match(TT.FUNC):
                body.add_child(self.function_decl())
            elif self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                self.error("Directiva inválida para o corpo de uma classe")
        return body

    def formal_params(self):
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            name = self.consume(TT.IDENTIFIER)
            self.consume(TT.COLON,"esperava-se o símbolo ':'.")
            param_type = self.type()
            params.append(AST.Param(param_type,name))
            while self.match(TT.COMMA):
                self.consume(TT.COMMA)
                name = self.consume(TT.IDENTIFIER)
                self.consume(TT.COLON,"esperava-se o símbolo ':'.")
                param_type = self.type()
                params.append(AST.Param(param_type,name))
        return params

    def statement(self):
        if self.match(TT.MOSTRA):
            return self.mostra_statement()
        elif self.match(TT.RETORNA):
            return self.retorna_statement()
        elif self.match(TT.ENQUANTO):
            return self.enquanto_stmt()
        elif self.match(TT.SE):
            return self.se_statement()
        elif self.match(TT.PARA):
            return self.para_stmt()
        else:
            return self.decl_stmt()

    def mostra_statement(self):
        token = self.consume(TT.MOSTRA)
        exp = self.equality()
        self.end_stmt()
        return AST.Mostra(token,exp)

    def retorna_statement(self):
        token = self.consume(TT.RETORNA)
        exp = self.equality()
        self.end_stmt()
        return AST.Retorna(token,exp)

    def se_statement(self):
        token = self.consume(TT.SE)
        condition = self.equality()
        self.consume(TT.ENTAO)
        then_branch = self.block()
        else_branch = None
        if self.match(TT.SENAO):
            self.consume(TT.SENAO)
            else_branch = self.block()
        self.consume(TT.FIM,"esperava-se a símbolo fim para terminar a directiva 'se'")
        return AST.Se(token,condition,then_branch,else_branch)

    def enquanto_stmt(self):
        token = self.consume(TT.ENQUANTO)
        condition = self.equality()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a directiva 'enquanto'")
        return AST.Enquanto(token,condition,block)

    def para_stmt(self):
        token = self.consume(TT.PARA)
        expression = self.for_expression()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a directiva 'para'")
        return AST.Para(token,expression,block)

    def for_expression(self):
        name = self.consume(TT.IDENTIFIER)
        self.consume(TT.DE)
        range_expr = self.range_expression()
        return AST.ParaExpr(name,range_expr)

    def range_expression(self):
        start = self.equality()
        self.consume(TT.DDOT)
        stop = self.equality()
        inc = None
        if self.lookahead.token == TT.INC:
            self.consume(TT.INC)
            inc = self.equality()
        return AST.RangeExpr(start,stop,inc)

    def decl_stmt(self):
        stmt = self.expression()
        if isinstance(stmt,AST.Variable):
            if self.match(TT.COLON):
                stmt = self.simple_decl(stmt.token)
            elif self.match(TT.COMMA):
                stmt = self.multi_decl(stmt.token)
        self.end_stmt()
        return stmt

    def simple_decl(self,name):
        token = self.consume(TT.COLON)
        var_type = self.type()
        assign = None
        if self.match(TT.EQUAL):
            assign = self.consume(TT.EQUAL)
            right = self.equality()
            assign = AST.Assign(
                assign,left=AST.Variable(name),
                right=right
            )
        return AST.VarDecl(
                token,name=name,var_type=var_type,
                assign=assign
        )

    def multi_decl(self,name):
        names = []
        names.append(name)
        while self.match(TT.COMMA):
            self.consume(TT.COMMA)
            name = self.consume(
                TT.IDENTIFIER,self.EXPECTED_ID.format(symbol=",")
            )
            names.append(name)
        token = self.consume(TT.COLON)
        var_type = self.type()
        decls = []
        for var_name in names:
            decl = AST.VarDecl(
                token,name=var_name,var_type=var_type,
                assign=None
            )
            decls.append(decl)
        return decls

    def expression(self):
        return self.compound_assignment()

    def eq_operator(self):
        if self.match(TT.DOUBLEEQUAL):
            return self.consume(TT.DOUBLEEQUAL)
        elif self.match(TT.NOTEQUAL):
            return self.consume(TT.NOTEQUAL)

    def compound_assignment(self):
        expr = self.assignment()
        compound_operator = (TT.PLUSEQ,TT.MINUSEQ,TT.SLASHEQ,TT.STAREQ)
        current = self.lookahead.token
        if current in compound_operator:
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            #Create separate tokens
            token = Token(None,None,line=self.lookahead.line,col=self.lookahead.col)
            eq = Token(TT.EQUAL,"=",line=self.lookahead.line,col=self.lookahead.col)
            token.token,token.lexeme = self.compound_operator()
            self.consume(current)
            if isinstance(expr,AST.Get):
                expr = AST.Set(target=expr,expr=self.assignment()) 
            else:
                expr = AST.Assign(eq,left=expr,right=AST.BinOp(token,left=expr,right=self.equality()))
        return expr

    def compound_operator(self):
        if self.match(TT.PLUSEQ):
            op = (TT.PLUS,"+")
        elif self.match(TT.MINUSEQ):
            op = (TT.MINUS,"-")
        elif self.match(TT.STAREQ):
            op = (TT.STAR,"*")
        elif self.match(TT.SLASHEQ):
            op = (TT.SLASH,"/")
        return op
 
    def assignment(self):
        expr = self.equality()
        if self.match(TT.EQUAL):
            token = self.consume(TT.EQUAL)
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            if isinstance(expr,AST.Get):
                expr = AST.Set(target=expr,expr=self.assignment()) 
            else:
                expr = AST.Assign(token,left=expr,right=self.assignment())
        return expr

    def equality(self):
        node = self.comparison()
        while self.lookahead.token in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            op = self.eq_operator()
            node = AST.BinOp(op,left=node,right=self.comparison())
        return node

    def comp_operator(self):
        if self.match(TT.GREATER):
            return self.consume(TT.GREATER)
        elif self.match(TT.GREATEREQ):
            return self.consume(TT.GREATEREQ)
        elif self.match(TT.LESS):
            return self.consume(TT.LESS)
        elif self.match(TT.LESSEQ):
            return self.consume(TT.LESSEQ)

    def comparison(self):
        node = self.addition()
        while self.lookahead.token in (TT.GREATER,TT.GREATEREQ,TT.LESS,TT.LESSEQ):
            op = self.comp_operator()
            node = AST.BinOp(op,left=node,right=self.addition())
        return node

    def addition(self):
        node = self.term()
        while self.lookahead.token in (TT.PLUS,TT.MINUS,TT.OU):
            if self.match(TT.OU):
                op = self.consume(TT.OU)
            else:
                op = self.add_operator()
            node = AST.BinOp(op,left=node,right=self.term())
        return node

    def term(self):
        node = self.unary()
        while self.lookahead.token in (TT.STAR,TT.SLASH,TT.MODULO,TT.E):
            op = self.mult_operator()
            node = AST.BinOp(op,left=node,right=self.unary())
        return node

    def unary(self):
        current = self.lookahead.token
        if current in (TT.PLUS,TT.MINUS,TT.NAO):
            token = self.consume(current)
            expr = AST.UnaryOp(token,operand=self.unary())
            return expr
        return self.call()
        
    def call(self):
        expr = self.primary()
        while self.lookahead.token in (TT.LPAR,TT.DOT):
            if self.match(TT.LPAR):
                self.consume(TT.LPAR)
                args = []
                if not self.match(TT.RPAR):
                    args = self.args()
                token = self.consume(
                    TT.RPAR,
                    "os argumentos da função devem ser delimitados por ')'"
                )
                expr = AST.Call(callee=expr,paren=token,fargs=args)
            else:
                self.consume(TT.DOT)
                identifier = self.lookahead
                self.consume(TT.IDENTIFIER)
                expr = AST.Get(target=expr,member=identifier)
        return expr

    def primary(self):
        current = self.lookahead.token
        expr = None
        if current in (TT.INTEGER,TT.REAL,TT.STRING,TT.IDENTIFIER,TT.VERDADEIRO,TT.FALSO):
            if self.match(TT.IDENTIFIER):
                expr = AST.Variable(self.lookahead)
            else:
                expr = AST.Constant(self.lookahead)
            self.consume(current)
        elif self.match(TT.LPAR):
            self.consume(TT.LPAR)
            expr = self.equality()
            self.consume(TT.RPAR)
        #REMOVE: Not in use
        elif self.match(TT.EU):
            expr = AST.Eu(self.lookahead)
            self.consume(TT.EU)
        #REMOVE: Not in use
        elif self.match(TT.SUPER):
            expr = AST.Super(self.consume(TT.SUPER))
        else:
            self.error(f"início inválido de expressão: '{self.lookahead.lexeme}'")
        return expr

    def args(self):
        current = self.lookahead.token
        args = []
        args.append(self.equality())
        while self.match(TT.COMMA):
            self.consume(TT.COMMA)
            args.append(self.equality())
        return args

    def mult_operator(self):
        if self.match(TT.E):
            return self.consume(TT.E)
        if self.match(TT.STAR):
            return self.consume(TT.STAR)
        elif self.match(TT.SLASH):
            return self.consume(TT.SLASH)
        elif self.match(TT.MODULO):
            return self.consume(TT.MODULO)

    def add_operator(self):
        if self.match(TT.PLUS):
            return self.consume(TT.PLUS)
        elif self.match(TT.MINUS):
            return self.consume(TT.MINUS)
