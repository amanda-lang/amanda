from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.error as error


'''*Class used to parse input file
   *Each method of this file is a rule defined in the grammar '''

class Parser:

    def __init__(self,lexer):
        self.lexer = lexer
        self.lookahead = lexer.get_token()

    def consume(self,token_t,error=None):
        if self.lookahead.token == token_t:
            #print(f"Parser consumed {self.lookahead}")
            self.lookahead = self.lexer.get_token()
        else:
            if error:
                self.error(error)
            self.error(f"era esperado o símbolo {token_t.value},porém recebeu o símbolo '{self.lookahead.lexeme}'")

    def error(self,message=None):
        raise error.Syntax(message,self.lexer.line)

    #function that triggers parsing
    def parse(self):
        return self.program()


    def program(self):
        program = AST.Program()
        start_first = (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,TT.VAR,TT.VECTOR,TT.DEFINA,
            TT.LBRACE,TT.ENQUANTO,TT.PARA)
        if self.lookahead.token in start_first or self.lookahead.token == Lexer.EOF:
            while self.lookahead.token in start_first:
                program.add_child(self.declaration())
            if self.lookahead.token == Lexer.EOF:
                return program
            else:
                self.error("sintaxe inválida")
        else:
            self.error(f"sintaxe inválida para início de programa {self.lookahead.token}")

    def declaration(self):
        if self.lookahead.token == TT.VAR:
            return self.var_decl()
        elif self.lookahead.token == TT.DEFINA:
            return self.function_decl()
        elif self.lookahead.token == TT.VECTOR:
            return self.array_decl()
        elif (self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,
            TT.LBRACE,TT.ENQUANTO,TT.PARA)):
            return self.statement()


    def var_decl(self):
        token = self.lookahead
        self.consume(TT.VAR)
        type = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_TYPE.format(symbol=token.lexeme))
        id = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=type.lexeme))
        assign = None
        if self.lookahead.token == TT.EQUAL:
            assign = self.lookahead
            self.consume(TT.EQUAL)
            right = self.expression()
            assign = AST.AssignNode(assign,left=AST.ExpNode(id),right=right)
        self.consume(TT.SEMI,error.Syntax.MISSING_SEMI)
        return AST.VarDeclNode(token,id=id,type=type,assign=assign)

    def array_decl(self):
        token = self.lookahead
        self.consume(TT.VECTOR)
        type = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_TYPE.format(symbol=token.lexeme))
        id = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=type.lexeme))
        self.consume(TT.LBRACKET)
        size = self.equality()
        self.consume(TT.RBRACKET)
        self.consume(TT.SEMI,error.Syntax.MISSING_SEMI)
        #print("PARSER: ",size.token)
        return AST.ArrayDeclNode(token,id=id,type=type,size=size)

    def function_decl(self):
        sym = self.lookahead.lexeme
        self.consume(TT.DEFINA)
        id = self.lookahead
        self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_ID.format(symbol=sym))
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(TT.RPAR,"os parâmetros da função devem estar delimitados por  ')'")
        self.consume(TT.COLON)
        # Check if function is void
        type = None
        if self.lookahead.token == TT.IDENTIFIER:
            type = self.lookahead
            self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_TYPE.format(symbol=":"))
        elif self.lookahead.token == TT.VAZIO:
            type = self.lookahead
            self.consume(TT.VAZIO,error.Syntax.EXPECTED_TYPE.format(symbol=":"))
        block = self.block()
        return AST.FunctionDecl(id=id,block=block,type=type,params=params)

    def formal_params(self):
        params = []
        if self.lookahead.token == TT.IDENTIFIER:
            type = self.lookahead
            is_array = False
            self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_TYPE.format(symbol="("))
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
                self.consume(TT.IDENTIFIER,error.Syntax.EXPECTED_TYPE.format(symbol=","))
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
            self.consume(TT.SEMI,error.Syntax.MISSING_SEMI)
            return node
        elif current == TT.MOSTRA:
            return self.mostra_statement()
        elif current == TT.RETORNA:
            return self.retorna_statement()
        elif current == TT.ENQUANTO:
            return self.while_statement()
        elif current == TT.SE:
            return self.se_statement()
        elif current == TT.LBRACE:
            return self.block()
        elif current == TT.PARA:
            return self.for_statement()
        else:
            self.error("Instrução inválida. Só pode fazer declarações dentro de blocos ou no escopo principal")

    def mostra_statement(self):
        token = self.lookahead
        self.consume(TT.MOSTRA)
        exp = self.equality()
        self.consume(TT.SEMI,error.Syntax.MISSING_SEMI)
        return AST.Statement(token,exp)

    def retorna_statement(self):
        token = self.lookahead
        self.consume(TT.RETORNA)
        exp = self.equality()
        self.consume(TT.SEMI,error.Syntax.MISSING_SEMI)
        return AST.Statement(token,exp)

    def se_statement(self):
        token = self.lookahead
        self.consume(TT.SE)
        self.consume(TT.LPAR,"a instrução 'se' deve possuir uma condição")
        condition = self.equality()
        self.consume(TT.RPAR,"a condição deve ser delimitada por ')'")
        self.consume(TT.ENTAO)
        then_branch = self.statement()
        else_branch = None
        if self.lookahead.token == TT.SENAO:
            self.consume(TT.SENAO)
            else_branch = self.statement()
        return AST.SeStatement(token,condition,then_branch,else_branch)


    def while_statement(self):
        token = self.lookahead
        self.consume(TT.ENQUANTO)
        self.consume(TT.LPAR,"a instrução 'enquanto' deve possuir uma condição")
        condition = self.equality()
        self.consume(TT.RPAR,"a condição deve ser delimitada por ')'")
        self.consume(TT.FACA)
        return AST.WhileStatement(token,condition,self.statement())

    def for_statement(self):
        token = self.lookahead
        self.consume(TT.PARA)
        self.consume(TT.LPAR,"a instrução 'para' deve possuir uma expressão")
        expression = self.for_expression()
        self.consume(TT.RPAR,"a expressão deve ser delimitada por ')'")
        self.consume(TT.FACA)
        return AST.ForStatement(token,expression,self.statement())

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


    def block(self):
        block = AST.Block()
        self.consume(TT.LBRACE)
        while ( self.lookahead.token in (TT.LPAR,TT.INTEGER,TT.IDENTIFIER,
            TT.REAL,TT.STRING,TT.PLUS,TT.MINUS,TT.VERDADEIRO,
            TT.FALSO,TT.NOT,TT.MOSTRA,TT.RETORNA,TT.SE,TT.VAR,TT.VECTOR,TT.DEFINA,
            TT.LBRACE,TT.ENQUANTO,TT.PARA) ):
            block.add_child(self.declaration())
        self.consume(TT.RBRACE,"os blocos devem ser delimitados por '}'")
        return block


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
        #TODO: check if this is dead code
        else:
            self.error("início inválido de expressão",self.lookahead)
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
        self.consume(TT.RPAR,"os argumentos da função devem ser delimitados por ')'")
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
