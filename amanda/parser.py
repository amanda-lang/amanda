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

    def error(self,message=None):
        handler = error.ErrorHandler.get_handler()
        handler.throw_error(
            error.Syntax(message,self.lexer.line),
            self.lexer.file
        )

    #function that triggers parsing
    def parse(self):
        return self.program()


    def program(self):
        program = AST.Program()
        program.add_child(self.block())
        if self.lookahead.token == Lexer.EOF:
            return program
        else:
            self.error(f"sintaxe inválida para início de bloco {self.lookahead.token}")

    def block(self):
        ''' 
        Method that does bulk of the parsing.
        Called to parse body of functions, compound statements
        and the 'main'function.
        '''

        block = AST.Block()
        start_first = (
            TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,
            TT.VERDADEIRO,TT.FALSO,TT.NAO,
            TT.MOSTRA,TT.RETORNA,TT.SE,TT.VAR,
            TT.FUNC,TT.ENQUANTO,TT.PARA,
            TT.PROC,
            )

        while self.lookahead.token in start_first or self.lookahead.token == TT.NEWLINE:
            if self.lookahead.token in start_first:
                block.add_child(self.declaration())
            else:
                self.consume(TT.NEWLINE)

        return block



    def declaration(self):
        if self.lookahead.token == TT.VAR:
            return self.var_decl()
        elif self.lookahead.token == TT.FUNC:
            return self.function_decl()
        elif self.lookahead.token == TT.PROC:
            return self.procedure_decl()

        elif ( self.lookahead.token in (
                TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
                TT.REAL,TT.STRING,TT.PLUS,
                TT.MINUS,TT.VERDADEIRO,TT.FALSO,
                TT.NAO,TT.MOSTRA,TT.RETORNA,
                TT.SE,TT.LBRACE,TT.ENQUANTO,
                TT.PARA
                )
            ):
            return self.statement()

    def type(self):
        type = self.lookahead
        self.consume(TT.IDENTIFIER)
        #TODO: Add Array syntatic sugar here 
        return type
    

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
            #TODO: Add proper error format
            self.error(error.Syntax.MISSING_TERM)


    def var_decl(self):
        ''' 
        Method for parsing variable declarations

        var my_num : int
        var my_num : int = 2
        '''
        token = self.lookahead
        self.consume(TT.VAR)
        id = self.lookahead
        self.consume(
            TT.IDENTIFIER,
            error.Syntax.EXPECTED_ID.format(symbol=id.lexeme)
        )
        self.consume(TT.COLON)
        type = self.type()
        assign = None
        if self.lookahead.token == TT.EQUAL:
            assign = self.lookahead
            self.consume(TT.EQUAL)
            right = self.expression()
            assign = AST.AssignNode(
                assign,
                left=AST.ExpNode(id),
                right=right
            )
        self.end_stmt()
        return AST.VarDeclNode(token,id=id,type=type,assign=assign)


    #TODO: Find a better workaround for void 'functions'
    def procedure_decl(self):
        ''' 
        Method used to parse procedure declarations.
        Procedures are just functions/methods that don't return anything.
        Ex: 

            proc mostra_func(str:texto)
                mostra str
            fim

        '''

        sym = self.lookahead.lexeme
        self.consume(TT.PROC)
        id = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=sym))
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR,"os parâmetros do procedimento devem estar delimitados por  ')'")
        block = self.block()
        self.consume(TT.FIM,"Os blocos devem ser terminados com a palavra fim")
        return AST.FunctionDecl(id=id,block=block,type=None,params=params)


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
        id = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=sym))
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR,"os parâmetros da função devem estar delimitados por  ')'")
        self.consume(TT.COLON)
        type = self.type()
        block = self.block()
        self.consume(TT.FIM,"Os blocos devem ser terminados com a palavra fim")
        return AST.FunctionDecl(id=id,block=block,type=type,params=params)

    def formal_params(self):
        '''  
        Method for parsing parameters in function
        declarations
        Ex:
        func pow (base :float , expoente :int) 
        '''
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            id = self.lookahead
            self.consume(TT.IDENTIFIER)
            self.consume(TT.COLON,"esperava-se o símbolo ':'.")
            type = self.type()
            params.append(AST.ParamNode(type,id))
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                id = self.lookahead
                self.consume(TT.IDENTIFIER)
                self.consume(TT.COLON,"esperava-se o símbolo ':'.")
                type = self.type()
                params.append(AST.ParamNode(type,id))
        return params


    def statement(self):
        current = self.lookahead.token
        if ( current in (
                    TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
                    TT.REAL,TT.STRING,TT.PLUS,
                    TT.MINUS,TT.VERDADEIRO,TT.FALSO,
                    TT.NAO
                )
            ):
            #expr_statement
            node = self.expression()
            self.end_stmt()
            return node
        elif current == TT.MOSTRA:
            return self.mostra_statement()
        elif current == TT.RETORNA:
            return self.retorna_statement()
        elif current == TT.ENQUANTO:
            return self.enquanto_stmt()
        elif current == TT.SE:
            return self.se_statement()
        elif current == TT.LBRACE:
            return self.block()
        elif current == TT.PARA:
            return self.para_stmt()
        else:
            self.error("instrução inválida. Só pode fazer declarações dentro de blocos ou no escopo principal")

    def mostra_statement(self):
        token = self.lookahead
        self.consume(TT.MOSTRA)
        exp = self.equality()
        self.end_stmt()
        return AST.Statement(token,exp)

    def retorna_statement(self):
        token = self.lookahead
        self.consume(TT.RETORNA)
        exp = self.equality()
        self.end_stmt()
        return AST.Statement(token,exp)

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
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a instrução 'se'")
        return AST.SeStatement(token,condition,then_branch,else_branch)


    def enquanto_stmt(self):
        token = self.lookahead
        self.consume(TT.ENQUANTO)
        condition = self.equality()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a instrução 'enquanto'")
        return AST.WhileStatement(token,condition,block)

    def para_stmt(self):
        token = self.lookahead
        self.consume(TT.PARA)
        expression = self.for_expression()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(TT.FIM,"esperava-se o símbolo fim para terminar a instrução 'para'")
        return AST.ForStatement(token,expression,block)

    def for_expression(self):
        id = self.lookahead
        self.consume(TT.IDENTIFIER)
        self.consume(TT.DE)
        range = self.range_expression()
        return AST.ForExpr(id,range)

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
        return self.add_assign()

    def add_assign(self):
        node = self.multi_assign()
        current = self.lookahead.token
        if current == TT.PLUSEQ or current ==TT.MINUSEQ:
            if not node.is_assignable():
                self.error(error.Syntax.ILLEGAL_ASSIGN)
            #Create separate tokens
            token = Token(None,None,line=self.lookahead.line,col=self.lookahead.col)
            eq = Token(TT.EQUAL,"=",line=self.lookahead.line,col=self.lookahead.col)
            if current == TT.PLUSEQ:
                token.token,token.lexeme = TT.PLUS,"+"
            else:
                token.token,token.lexeme = TT.MINUS,"-"
            self.consume(current)
            node = AST.AssignNode(eq,left=node,right=AST.BinOpNode(token,left=node,right=self.equality()))
        return node

    def multi_assign(self):
        node = self.assignment()
        current = self.lookahead.token
        if current == TT.STAREQ or current ==TT.SLASHEQ:
            if not node.is_assignable():
                self.error(error.Syntax.ILLEGAL_ASSIGN)
            #Create separate tokens
            token = Token(None,None,line=self.lookahead.line,col=self.lookahead.col)
            eq = Token(TT.EQUAL,"=",line=self.lookahead.line,col=self.lookahead.col)
            if current == TT.STAREQ:
                token.token,token.lexeme = TT.STAR,"*"
            else:
                token.token,token.lexeme = TT.SLASH,"/"
            self.consume(current)
            node = AST.AssignNode(eq,left=node,right=AST.BinOpNode(token,left=node,right=self.equality()))
        return node


    def assignment(self):
        node = self.equality()
        current = self.lookahead.token
        if self.lookahead.token == TT.EQUAL:
            token = self.lookahead
            self.consume(TT.EQUAL)
            if not node.is_assignable():
                self.error(error.Syntax.ILLEGAL_ASSIGN)
            node = AST.AssignNode(token,left=node,right=self.assignment())
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
        while self.lookahead.token in (TT.PLUS,TT.MINUS,TT.OU):
            op = self.lookahead
            if self.lookahead.token == TT.OU:
                self.consume(TT.OU)
            else:
                self.add_operator()
            node = AST.BinOpNode(op,left=node,right=self.term())
        return node


    def term(self):
        node = self.factor()
        while self.lookahead.token in (TT.STAR,TT.SLASH,TT.MODULO,TT.E):
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
        elif current in (TT.PLUS,TT.MINUS,TT.NAO):
            token = self.lookahead
            self.consume(current)
            node = AST.UnaryOpNode(token,operand=self.factor())
        #TODO: check if this is dead code
        else:
            self.error(f"início inválido de expressão: '{self.lookahead.lexeme}'")
        return node

    def function_call(self):
        self.consume(TT.LPAR)
        current = self.lookahead.token
        args = []
        if ( current in (
                TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
                TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,
                TT.VERDADEIRO,TT.FALSO,TT.NAO
                ) 
            ):
            args.append(self.equality())
            while self.lookahead.token == TT.COMMA:
                self.consume(TT.COMMA)
                args.append(self.equality())
        self.consume(TT.RPAR,"os argumentos da função devem ser delimitados por ')'")
        return args



    def mult_operator(self):
        current = self.lookahead.token
        if current == TT.E:
            self.consume(TT.E)
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
