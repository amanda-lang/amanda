import os
import copy
from io import StringIO
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
from amanda.tokens import KEYWORDS as TK_KEYWORDS
from amanda.error import AmandaError
import amanda.ast as ast


class Lexer:
    # Special end of file token
    EOF = "__eof__"
    # Errors that happen during tokenization
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido"
    INVALID_STRING = "A sequência de caracteres não foi delimitada"

    def __init__(self, src):
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None
        self.file = src  # A file object

    @classmethod
    def string_lexer(cls, string):
        # Constructor to create a lexer with a string
        return cls(StringIO(string))

    def advance(self):
        if self.current_char == Lexer.EOF:
            return
        self.current_char = self.file.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF
        else:
            self.pos += 1

    def lookahead(self):
        last_position = self.file.tell()
        next_char = self.file.read(1)
        self.file.seek(last_position)
        return next_char

    def error(self, code, **kwargs):
        message = code.format(**kwargs)
        raise AmandaError.syntax_error(message, self.line, self.pos)

    def newline(self):
        pos = self.pos
        line = self.line
        self.line += 1
        self.pos = 1
        self.advance()
        return Token(TT.NEWLINE, "\\n", line, pos)

    def whitespace(self):
        while (
            self.current_char != "\n"
            and self.current_char.isspace()
            and self.current_char != Lexer.EOF
        ):
            self.advance()
        if self.current_char == "#":
            self.comment()

    def comment(self):
        while self.current_char != "\n" and self.current_char != Lexer.EOF:
            self.advance()

    def arit_operators(self):
        if self.current_char == "+":
            return self.get_op_token(self.current_char, TT.PLUS, TT.PLUSEQ)
        elif self.current_char == "-":
            return self.get_op_token(self.current_char, TT.MINUS, TT.MINUSEQ)
        elif self.current_char == "*":
            return self.get_op_token(self.current_char, TT.STAR, TT.STAREQ)
        elif self.current_char == "/":
            return self.get_op_token(self.current_char, TT.SLASH, TT.SLASHEQ)
        elif self.current_char == "%":
            self.advance()
            return Token(TT.MODULO, "%", self.line, self.pos)

    def get_op_token(self, op_lexeme, normal_op, cmp_assign):
        if self.lookahead() == "=":
            self.advance()
            self.advance()
            return Token(cmp_assign, op_lexeme + "=", self.line, self.pos - 1)

        if op_lexeme == "/" and self.lookahead() == "/":
            self.advance()
            normal_op = TT.DOUBLESLASH
            op_lexeme = "//"
        self.advance()
        return Token(normal_op, op_lexeme, self.line, self.pos)

    def comparison_operators(self):
        if self.current_char == "<":
            return self.get_op_token(self.current_char, TT.LESS, TT.LESSEQ)
        elif self.current_char == ">":
            return self.get_op_token(self.current_char, TT.GREATER, TT.GREATEREQ)
        elif self.current_char == "=":
            return self.get_op_token(self.current_char, TT.EQUAL, TT.DOUBLEEQUAL)
        elif self.current_char == "!":
            if self.lookahead() == "=":
                self.advance()
                self.advance()
                return Token(TT.NOTEQUAL, "!=", self.line, self.pos - 1)
            self.error(self.INVALID_SYMBOL, symbol=self.current_char)

    def number(self):
        result = ""
        while self.current_char.isdigit():
            result += self.current_char
            self.advance()
        if self.current_char == ".":
            # lookahead to see next char i
            if self.lookahead().isdigit():
                result += "."
                self.advance()
                while self.current_char.isdigit():
                    result += self.current_char
                    self.advance()
        if "." in result:
            return Token(
                TT.REAL, float(result), self.line, self.pos - (len(result) + 1)
            )

        return Token(TT.INTEGER, int(result), self.line, self.pos - (len(result) + 1))

    def string(self):
        result = ""
        symbol = self.current_char
        self.advance()
        while self.current_char != symbol:
            if self.current_char == Lexer.EOF:
                self.error(self.INVALID_STRING, line=self.line)
            result += self.current_char
            self.advance()
        self.advance()
        return Token(TT.STRING, f"{symbol}{result}{symbol}", self.line, self.pos)

    def identifier(self):
        result = ""
        while self.current_char.isalnum() or self.current_char == "_":
            result += self.current_char
            self.advance()
        if TK_KEYWORDS.get(result) is not None:
            token = copy.copy(TK_KEYWORDS.get(result))
            token.line = self.line
            token.col = self.pos - (len(result) + 1)
            return token
        return Token(TT.IDENTIFIER, result, self.line, self.pos - (len(result) + 1))

    def delimeters(self):
        char = self.current_char
        if self.current_char == ")":
            self.advance()
            return Token(TT.RPAR, char, self.line, self.pos)
        elif self.current_char == "(":
            self.advance()
            return Token(TT.LPAR, char, self.line, self.pos)
        elif self.current_char == ".":
            if self.lookahead() == ".":
                self.advance()
                self.advance()
                return Token(TT.DDOT, "..", self.line, self.pos - 1)
            self.advance()
            return Token(TT.DOT, char, self.line, self.pos)
        elif self.current_char == ";":
            self.advance()
            return Token(TT.SEMI, char, self.line, self.pos)
        elif self.current_char == ",":
            self.advance()
            return Token(TT.COMMA, char, self.line, self.pos)
        elif self.current_char == "{":
            self.advance()
            return Token(TT.LBRACE, char, self.line, self.pos)
        elif self.current_char == "}":
            self.advance()
            return Token(TT.RBRACE, char, self.line, self.pos)
        elif self.current_char == "[":
            self.advance()
            return Token(TT.LBRACKET, char, self.line, self.pos)
        elif self.current_char == "]":
            self.advance()
            return Token(TT.RBRACKET, char, self.line, self.pos)
        elif self.current_char == ":":
            self.advance()
            return Token(TT.COLON, char, self.line, self.pos)

    def get_token(self):
        if self.current_char is None:
            self.advance()
        if self.current_char == "#":
            self.comment()
        if self.current_char != "\n" and self.current_char.isspace():
            self.whitespace()
        if self.current_char == "\n":
            return self.newline()
        if self.current_char in ("+", "-", "*", "/", "%"):
            return self.arit_operators()
        if self.current_char in ("<", ">", "!", "="):
            return self.comparison_operators()
        if self.current_char.isdigit():
            return self.number()
        if self.current_char == "'" or self.current_char == '"':
            return self.string()
        if self.current_char.isalpha() or self.current_char == "_":
            return self.identifier()
        if self.current_char in ("(", ")", ".", ";", ",", "{", "}", "[", "]", ":"):
            return self.delimeters()
        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF, "")
        self.error(self.INVALID_SYMBOL, symbol=self.current_char)


class Parser:
    # Errors messages
    MISSING_TERM = "as instruções devem ser delimitadas por ';' ou por uma nova linha"
    ILLEGAL_EXPRESSION = "início inválido de expressão"
    EXPECTED_ID = "era esperado um identificador depois do símbolo '{symbol}'"
    EXPECTED_TYPE = "era esperado um tipo depois do símbolo '{symbol}'"
    ILLEGAL_ASSIGN = "alvo inválido para atribuição"

    def __init__(self, io_object):
        self.lexer = Lexer(io_object)
        self.delimited = False
        self.lookahead = self.lexer.get_token()

    def consume(self, expected, error=None, skip_newlines=False):
        if skip_newlines or self.delimited:
            self.skip_newlines()
        if self.match(expected):
            consumed = self.lookahead
            self.lookahead = self.lexer.get_token()
            return consumed
        else:
            if error:
                self.error(error)
            self.error(
                f"era esperado o símbolo {expected.value},porém recebeu o símbolo '{self.lookahead.lexeme}'"
            )

    def error(self, message, line=None):
        err_line = self.lookahead.line
        if line:
            err_line = line
        raise AmandaError.syntax_error(message, err_line, self.lookahead.col)

    def skip_newlines(self):
        while self.match(TT.NEWLINE):
            self.lookahead = self.lexer.get_token()

    def match(self, token):
        return self.lookahead.token == token

    def parse(self):
        return self.program()

    def program(self):
        program = ast.Program()
        while not self.match(Lexer.EOF):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                child = self.declaration()
                self.append_child(program, child)
        return program

    def block(self):
        block = ast.Block()
        # SENAO is because of se statements
        # SENAOSE is because of se statements
        # EOF is for better error messages
        while (
            not self.match(TT.FIM)
            and not self.match(TT.SENAO)
            and not self.match(TT.SENAOSE)
            and not self.match(TT.CASO)
            and not self.match(Lexer.EOF)
        ):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                child = self.declaration()
                self.append_child(block, child)
        return block

    def append_child(self, body, child):
        """Method for desugaring
        multiple statement"""
        if isinstance(child, list):
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
        is_list = False
        dim = 0
        while self.match(TT.LBRACKET):
            self.consume(TT.LBRACKET)
            self.consume(TT.RBRACKET)
            dim += 1
            is_list = True
        type_name = self.consume(TT.IDENTIFIER)
        return ast.Type(type_name, dim=dim, is_list=is_list)

    def end_stmt(self):
        if self.match(TT.NEWLINE):
            self.consume(TT.NEWLINE)
        elif self.match(TT.SEMI):
            self.consume(TT.SEMI)
        elif self.match(Lexer.EOF):
            self.consume(Lexer.EOF)
        else:
            self.error(self.MISSING_TERM)

    def function_decl(self):
        self.consume(TT.FUNC)
        name = self.consume(TT.IDENTIFIER, self.EXPECTED_ID.format(symbol="func"))
        self.consume(TT.LPAR)
        params = self.formal_params()
        self.consume(
            TT.RPAR, "os parâmetros da função devem estar delimitados por  ')'"
        )
        func_type = None
        if self.match(TT.COLON):
            self.consume(TT.COLON)
            if self.match(TT.VAZIO):  # REMOVE: Maybe remove this
                self.consume(TT.VAZIO)
            else:
                func_type = self.type()
        block = self.block()
        self.consume(
            TT.FIM, "O corpo de um função deve ser terminado com a directiva 'fim'"
        )
        return ast.FunctionDecl(
            name=name, block=block, func_type=func_type, params=params
        )

    def class_decl(self):
        self.consume(TT.CLASSE)
        name = self.consume(TT.IDENTIFIER)
        body = self.class_body()
        self.consume(
            TT.FIM, "O corpo de uma classe deve ser terminado com o símbolo fim"
        )
        return ast.ClassDecl(name=name, body=body)

    def class_body(self):
        body = ast.ClassBody()
        while not self.match(TT.FIM):
            if self.match(TT.NEWLINE):
                self.skip_newlines()
            else:
                member = self.declaration()
                member_type = type(member)
                if member_type != ast.FunctionDecl and member_type != ast.VarDecl:
                    self.error(
                        "directiva inválida para o corpo de uma classe", member.lineno
                    )
                if member_type == ast.VarDecl and member.assign is not None:
                    self.error(
                        "Não pode inicializar os campos de um classe", member.lineno
                    )
                body.add_child(member)
        return body

    def formal_params(self):
        params = []
        self.skip_newlines()
        if self.lookahead.token == TT.IDENTIFIER:
            name = self.consume(TT.IDENTIFIER, skip_newlines=True)
            self.consume(TT.COLON, "esperava-se o símbolo ':'.")
            param_type = self.type()
            params.append(ast.Param(param_type, name))
            while not self.match(TT.RPAR):
                self.consume(TT.COMMA, skip_newlines=True)
                name = self.consume(TT.IDENTIFIER, skip_newlines=True)
                self.consume(TT.COLON, "esperava-se o símbolo ':'.")
                param_type = self.type()
                params.append(ast.Param(param_type, name))
                self.skip_newlines()
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
        elif self.match(TT.ESCOLHA):
            return self.escolha_stmt()
        else:
            return self.decl_stmt()

    def mostra_statement(self):
        token = self.consume(TT.MOSTRA)
        exp = self.equality()
        self.end_stmt()
        return ast.Mostra(token, exp)

    def retorna_statement(self):
        token = self.consume(TT.RETORNA)
        exp = self.equality()
        self.end_stmt()
        return ast.Retorna(token, exp)

    def se_statement(self):
        token = self.consume(TT.SE)
        condition = self.equality()
        self.consume(TT.ENTAO)
        then_branch = self.block()
        else_branch = None
        elsif_branches = []
        while self.match(TT.SENAOSE):
            elsif_branches.append(self.senaose_branch())
        if self.match(TT.SENAO):
            self.consume(TT.SENAO)
            else_branch = self.block()
        self.consume(TT.FIM, "esperava-se a símbolo fim para terminar a directiva 'se'")
        return ast.Se(
            token,
            condition,
            then_branch,
            elsif_branches=elsif_branches,
            else_branch=else_branch,
        )

    def senaose_branch(self):
        token = self.consume(TT.SENAOSE)
        condition = self.equality()
        self.consume(TT.ENTAO)
        then_branch = self.block()
        return ast.SenaoSe(token, condition, then_branch)

    def enquanto_stmt(self):
        token = self.consume(TT.ENQUANTO)
        condition = self.equality()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(
            TT.FIM, "esperava-se o símbolo fim para terminar a directiva 'enquanto'"
        )
        return ast.Enquanto(token, condition, block)

    def para_stmt(self):
        token = self.consume(TT.PARA)
        expression = self.for_expression()
        self.consume(TT.FACA)
        block = self.block()
        self.consume(
            TT.FIM, "esperava-se o símbolo fim para terminar a directiva 'para'"
        )
        return ast.Para(token, expression, block)

    def escolha_stmt(self):
        token = self.consume(TT.ESCOLHA)
        expression = self.equality()
        self.consume(TT.COLON)
        cases = []
        default_case = None
        self.skip_newlines()
        # Parse cases
        while self.match(TT.CASO):
            block_token = self.consume(TT.CASO)
            case_expr = self.equality()
            self.consume(TT.COLON)
            block = self.block()
            cases.append(ast.CaseBlock(block_token, case_expr, block))
        # Default case
        if self.match(TT.SENAO):
            self.consume(TT.SENAO)
            self.consume(TT.COLON)
            default_case = self.block()
        self.consume(TT.FIM)
        return ast.Escolha(token, expression, cases, default_case)

    def for_expression(self):
        name = self.consume(TT.IDENTIFIER)
        self.consume(TT.DE)
        range_expr = self.range_expression(name)
        return ast.ParaExpr(name, range_expr)

    def range_expression(self, token):
        start = self.equality()
        self.consume(TT.DDOT)
        stop = self.equality()
        inc = None
        if self.lookahead.token == TT.INC:
            self.consume(TT.INC)
            inc = self.equality()
        return ast.RangeExpr(token, start, stop, inc)

    def decl_stmt(self):
        stmt = self.expression()
        if isinstance(stmt, ast.Variable):
            if self.match(TT.COLON):
                stmt = self.simple_decl(stmt.token)
            elif self.match(TT.COMMA):
                stmt = self.multi_decl(stmt.token)
        self.end_stmt()
        return stmt

    def get_decl_assign(self, name):
        assign = None
        if self.match(TT.EQUAL):
            assign = ast.Assign(
                self.consume(TT.EQUAL), left=ast.Variable(name), right=self.equality()
            )
        return assign

    def simple_decl(self, name):
        token = self.consume(TT.COLON)
        var_type = self.type()
        assign = self.get_decl_assign(name)
        return ast.VarDecl(token, name=name, var_type=var_type, assign=assign)

    def multi_decl(self, name):
        names = []
        names.append(name)
        while self.match(TT.COMMA):
            self.consume(TT.COMMA)
            name = self.consume(TT.IDENTIFIER, self.EXPECTED_ID.format(symbol=","))
            names.append(name)
        token = self.consume(TT.COLON)
        var_type = self.type()
        decls = []
        for var_name in names:
            decl = ast.VarDecl(token, name=var_name, var_type=var_type, assign=None)
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
        compound_operator = (TT.PLUSEQ, TT.MINUSEQ, TT.SLASHEQ, TT.STAREQ)
        current = self.lookahead.token
        if current in compound_operator:
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            # Create separate tokens
            token = Token(None, None, line=self.lookahead.line, col=self.lookahead.col)
            eq = Token(TT.EQUAL, "=", line=self.lookahead.line, col=self.lookahead.col)
            token.token, token.lexeme = self.compound_operator()
            self.consume(current)
            if isinstance(expr, ast.Get):
                expr = ast.Set(target=expr, expr=self.assignment())
            else:
                expr = ast.Assign(
                    eq,
                    left=expr,
                    right=ast.BinOp(token, left=expr, right=self.equality()),
                )
        return expr

    def compound_operator(self):
        if self.match(TT.PLUSEQ):
            op = (TT.PLUS, "+")
        elif self.match(TT.MINUSEQ):
            op = (TT.MINUS, "-")
        elif self.match(TT.STAREQ):
            op = (TT.STAR, "*")
        elif self.match(TT.SLASHEQ):
            op = (TT.SLASH, "/")
        return op

    def assignment(self):
        expr = self.equality()
        if self.match(TT.EQUAL):
            token = self.consume(TT.EQUAL)
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            if isinstance(expr, ast.Get):
                expr = ast.Set(target=expr, expr=self.assignment())
            else:
                expr = ast.Assign(token, left=expr, right=self.assignment())
        return expr

    def equality(self):
        node = self.comparison()
        while self.lookahead.token in (TT.DOUBLEEQUAL, TT.NOTEQUAL):
            op = self.eq_operator()
            node = ast.BinOp(op, left=node, right=self.comparison())
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
        while self.lookahead.token in (TT.GREATER, TT.GREATEREQ, TT.LESS, TT.LESSEQ):
            op = self.comp_operator()
            node = ast.BinOp(op, left=node, right=self.addition())
        return node

    def addition(self):
        node = self.term()
        while self.lookahead.token in (TT.PLUS, TT.MINUS, TT.OU):
            if self.match(TT.OU):
                op = self.consume(TT.OU)
            else:
                op = self.add_operator()
            node = ast.BinOp(op, left=node, right=self.term())
        return node

    def term(self):
        node = self.unary()
        while self.lookahead.token in (
            TT.STAR,
            TT.DOUBLESLASH,
            TT.SLASH,
            TT.MODULO,
            TT.E,
        ):
            op = self.mult_operator()
            node = ast.BinOp(op, left=node, right=self.unary())
        return node

    def unary(self):
        current = self.lookahead.token
        if current in (TT.PLUS, TT.MINUS, TT.NAO):
            token = self.consume(current)
            expr = ast.UnaryOp(token, operand=self.unary())
            return expr
        return self.call()

    def call(self):
        expr = self.primary()
        while self.lookahead.token in (TT.LPAR, TT.DOT, TT.LBRACKET):
            if self.match(TT.LPAR):
                self.consume(TT.LPAR)
                args = []
                args = self.args()
                token = self.consume(
                    TT.RPAR, "os argumentos da função devem ser delimitados por ')'"
                )
                expr = ast.Call(callee=expr, paren=token, fargs=args)
            elif self.match(TT.LBRACKET):
                self.consume(TT.LBRACKET)
                index = self.equality()
                token = self.consume(TT.RBRACKET)
                expr = ast.Index(token, expr, index)
            else:
                self.consume(TT.DOT)
                identifier = self.lookahead
                self.consume(TT.IDENTIFIER)
                expr = ast.Get(target=expr, member=identifier)
        return expr

    def primary(self):
        current = self.lookahead.token
        expr = None
        if current in (
            TT.INTEGER,
            TT.REAL,
            TT.STRING,
            TT.NULO,
            TT.IDENTIFIER,
            TT.VERDADEIRO,
            TT.FALSO,
        ):
            if self.match(TT.IDENTIFIER):
                expr = ast.Variable(self.lookahead)
            else:
                expr = ast.Constant(self.lookahead)
            self.consume(current)
        elif self.match(TT.LBRACKET):
            token = self.consume(TT.LBRACKET)
            self.skip_newlines()
            list_type = self.type()
            elements = []
            self.consume(TT.COLON)
            if not self.match(TT.RBRACKET):
                self.skip_newlines()
                elements.append(self.equality())
                while not self.match(TT.RBRACKET):
                    self.consume(TT.COMMA, skip_newlines=True)
                    self.skip_newlines()
                    elements.append(self.equality())
                    self.skip_newlines()
            self.consume(TT.RBRACKET, skip_newlines=True)
            expr = ast.ListLiteral(token, list_type=list_type, elements=elements)
        elif self.match(TT.LPAR):
            self.consume(TT.LPAR)
            expr = self.equality()
            self.consume(TT.RPAR)
        elif self.match(TT.EU):
            expr = ast.Eu(self.lookahead)
            self.consume(TT.EU)
        elif self.match(TT.CONVERTE):
            expr = self.converte_expression()
        else:
            self.error(f"início inválido de expressão: '{self.lookahead.lexeme}'")
        return expr

    def converte_expression(self):
        token = self.consume(TT.CONVERTE)
        self.consume(TT.LPAR)
        expression = self.equality()
        self.consume(TT.COMMA)
        new_type = self.type()
        self.consume(TT.RPAR)
        return ast.Converte(token, expression, new_type)

    def args(self):
        current = self.lookahead.token
        args = []
        self.skip_newlines()
        if not self.match(TT.RPAR):
            args.append(self.equality())
        while not self.match(TT.RPAR):
            self.consume(TT.COMMA, skip_newlines=True)
            self.skip_newlines()
            args.append(self.equality())
            self.skip_newlines()
        return args

    def mult_operator(self):
        if self.match(TT.E):
            return self.consume(TT.E)
        elif self.match(TT.STAR):
            return self.consume(TT.STAR)
        elif self.match(TT.SLASH):
            return self.consume(TT.SLASH)
        elif self.match(TT.DOUBLESLASH):
            return self.consume(TT.DOUBLESLASH)
        elif self.match(TT.MODULO):
            return self.consume(TT.MODULO)

    def add_operator(self):
        if self.match(TT.PLUS):
            return self.consume(TT.PLUS)
        elif self.match(TT.MINUS):
            return self.consume(TT.MINUS)
