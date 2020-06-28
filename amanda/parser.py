from amanda.lexer import Lexer
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
import amanda.ast_nodes as AST
import amanda.error as error


'''*Class used to parse input file
   *Each method of this file is a rule defined in the grammar '''

class Parser:

    def __init__(self,io_object):
        self.lexer = Lexer(io_object)
        self.lookahead = self.lexer.get_token()

    def consume(self,token_t,error=None):
        if self.lookahead.token == token_t:
            #print(f"Parser consumed {self.lookahead}")
            self.lookahead = self.lexer.get_token()
        else:
            if error:
                self.error(error)
            self.error(f"era esperado o símbolo {token_t.value},porém recebeu o símbolo '{self.lookahead.lexeme}'")

    def error(self,message):
        raise error.Syntax(
            message,self.lookahead.line,
            self.lookahead.col)
        

    #function that triggers parsing
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
                program.add_child(self.declaration())
        return program

    def block(self):
        ''' 
        Method that does bulk of the parsing.
        '''
        block = AST.Block()

        #SENAO is because of if statements
        while not self.match(TT.FIM) and not self.match(TT.SENAO):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                block.add_child(self.declaration())
        return block


    def declaration(self):

        if self.match(TT.VAR):
            return self.var_decl()

        elif self.match(TT.FUNC):
            return self.function_decl()

        elif self.match(TT.CLASSE):
            return self.class_decl()

        else:
            return self.statement()

    def type(self):
        type_name = self.lookahead
        self.consume(TT.IDENTIFIER)
        #TODO: Add Array syntatic sugar here 
        return type_name
    

    def end_stmt(self):
        ''' 
            Method used to parse newlines and semicolons at the
            end of statements
        '''
        token = self.lookahead.token
        if token == TT.NEWLINE:
            self.consume(TT.NEWLINE)

        elif token == TT.SEMI:
            self.consume(TT.SEMI)
        else:
            self.error(error.Syntax.MISSING_TERM)


    def var_decl(self):
        ''' 
        Method for parsing variable declarations

        var my_num : int
        var my_num : int = 2
        '''
        token = self.lookahead
        self.consume(TT.VAR)
        name = self.lookahead
        self.consume(
            TT.IDENTIFIER,
            error.Syntax.EXPECTED_ID.format(symbol=name.lexeme)
        )
        self.consume(TT.COLON)
        var_type = self.type()
        assign = None
        if self.lookahead.token == TT.EQUAL:
            assign = self.lookahead
            self.consume(TT.EQUAL)
            right = self.expression()
            assign = AST.Assign(
                assign,
                left=AST.Variable(name),
                right=right
            )
        self.end_stmt()
        return AST.VarDecl(token,name=name,var_type=var_type,assign=assign)


    def function_decl(self):
        ''' 
        Method used to parse function declarations

        Ex: 

            func add(a:int,b:int):int
                retorna a+b
            fim
        '''
        sym = self.lookahead.lexeme
        self.consume(TT.FUNC)
        name = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=sym))
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR,"os parâmetros da função devem estar delimitados por  ')'")
        func_type = None
        if self.match(TT.COLON):
            self.consume(TT.COLON)
            func_type = self.type()
        block = self.block()
        self.consume(TT.FIM,"Os blocos devem ser terminados com a palavra fim")
        return AST.FunctionDecl(name=name,block=block,func_type=func_type,params=params)



    def get_superclass(self):
        #Helper to parse classes with inheritance
        #syntax
        superclass = None
        if self.match(TT.LESS):
            self.consume(TT.LESS)
            superclass = self.lookahead 
            self.consume(TT.IDENTIFIER)
        return superclass


    def class_decl(self):
        self.consume(TT.CLASSE)
        name = self.lookahead
        self.consume(TT.IDENTIFIER)
        superclass = self.get_superclass()
        body = self.class_body()
        self.consume(TT.FIM,"O corpo de uma classe deve ser terminado com o símbolo fim")
        return AST.ClassDecl(name=name,superclass=superclass,body=body)


    def class_body(self):
        body = AST.ClassBody()
        while not self.match(TT.FIM):
            if self.match(TT.VAR):
                body.add_child(self.var_decl())
            elif self.match(TT.FUNC):
                body.add_child(self.function_decl())
            elif self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                self.error("Directiva inválida para o corpo de uma classe")
        return body

        

    def formal_params(self):
        '''  
        Method for parsing parameters in function
        declarations
        Ex:
        func pow (base :float , expoente :int) 
        '''
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            name = self.lookahead
            self.consume(TT.IDENTIFIER)
            self.consume(TT.COLON,"esperava-se o símbolo ':'.")
            param_type = self.type()
            params.append(AST.Param(param_type,name))
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                name = self.lookahead
                self.consume(TT.IDENTIFIER)
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
            expr = self.expression()
            self.end_stmt()
            return expr

    def mostra_statement(self):
        token = self.lookahead
        self.consume(TT.MOSTRA)
        exp = self.equality()
        self.end_stmt()
        return AST.Mostra(token,exp)

    def retorna_statement(self):
        token = self.lookahead
        self.consume(TT.RETORNA)
        exp = self.equality()
        self.end_stmt()
        return AST.Retorna(token,exp)

    def se_statement(self):
        token = self.lookahead
        self.consume(TT.SE)
        condition = self.equality()
        self.consume(TT.ENTAO)
        then_branch = self.block()
        else_branch = None
        if self.lookahead.token == TT.SENAO:
            self.consume(TT.SENAO)
            else_branch = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a directiva 'se'")
        return AST.Se(token,condition,then_branch,else_branch)


    def enquanto_stmt(self):
        token = self.lookahead
        self.consume(TT.ENQUANTO)
        condition = self.equality()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a directiva 'enquanto'")
        return AST.Enquanto(token,condition,block)

    def para_stmt(self):
        token = self.lookahead
        self.consume(TT.PARA)
        expression = self.for_expression()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a directiva 'para'")
        return AST.Para(token,expression,block)

    def for_expression(self):
        name = self.lookahead
        self.consume(TT.IDENTIFIER)
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

    def eq_operator(self):
        current = self.lookahead.token
        if current == TT.DOUBLEEQUAL:
            self.consume(TT.DOUBLEEQUAL)
        elif current == TT.NOTEQUAL:
            self.consume(TT.NOTEQUAL)

    def expression(self):
        return self.compound_assignment()


    def compound_assignment(self):
        expr = self.assignment()
        compound_operator = (TT.PLUSEQ,TT.MINUSEQ,TT.SLASHEQ,TT.STAREQ)
        current = self.lookahead.token
        if current in compound_operator:
            if not expr.is_assignable():
                self.error(error.Syntax.ILLEGAL_ASSIGN)
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
        current = self.lookahead.token
        if self.match(TT.EQUAL):
            token = self.lookahead
            self.consume(TT.EQUAL)
            if not expr.is_assignable():
                self.error(error.Syntax.ILLEGAL_ASSIGN)
            if isinstance(expr,AST.Get):
                expr = AST.Set(target=expr,expr=self.assignment()) 
            else:
                expr = AST.Assign(token,left=expr,right=self.assignment())
        return expr


    def equality(self):
        node = self.comparison()
        while self.lookahead.token in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            op = self.lookahead
            self.eq_operator()
            node = AST.BinOp(op,left=node,right=self.comparison())
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
            node = AST.BinOp(op,left=node,right=self.addition())
        return node

    def addition(self):
        node = self.term()
        while self.lookahead.token in (TT.PLUS,TT.MINUS,TT.OU):
            op = self.lookahead
            if self.lookahead.token == TT.OU:
                self.consume(TT.OU)
            else:
                self.add_operator()
            node = AST.BinOp(op,left=node,right=self.term())
        return node


    def term(self):
        node = self.unary()
        while self.lookahead.token in (TT.STAR,TT.SLASH,TT.MODULO,TT.E):
            op = self.lookahead
            self.mult_operator()
            node = AST.BinOp(op,left=node,right=self.unary())
        return node


    def unary(self):
        current = self.lookahead.token
        if current in (TT.PLUS,TT.MINUS,TT.NAO):
            token = self.lookahead
            self.consume(current)
            expr = AST.UnaryOp(token,operand=self.unary())
            return expr
        return self.call()
        

    def call(self):
        expr = self.primary()
        while self.lookahead.token in (TT.LPAR,TT.DOT):
            current = self.lookahead.token
            if self.match(TT.LPAR):
                self.consume(TT.LPAR)
                args = []
                if not self.match(TT.RPAR):
                    args = self.args()
                token = self.lookahead
                self.consume(TT.RPAR,
                "os argumentos da função devem ser delimitados por ')'")
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
        elif self.match(TT.EU):
            expr = AST.Eu(self.lookahead)
            self.consume(TT.EU)
        elif self.match(TT.SUPER):
            expr = AST.Super(self.lookahead)
            self.consume(TT.SUPER)
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
            self.consume(TT.E)
        if self.match(TT.STAR):
            self.consume(TT.STAR)
        elif self.match(TT.SLASH):
            self.consume(TT.SLASH)
        elif self.match(TT.MODULO):
            self.consume(TT.MODULO)


    def add_operator(self):
        current = self.lookahead.token
        if self.match(TT.PLUS):
            self.consume(TT.PLUS)
        elif self.match(TT.MINUS):
            self.consume(TT.MINUS)
