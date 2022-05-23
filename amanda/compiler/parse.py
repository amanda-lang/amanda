import os
import copy
from io import StringIO
from amanda.compiler.tokens import TokenType as TT
from amanda.compiler.tokens import Token
from amanda.compiler.tokens import KEYWORDS as TK_KEYWORDS
from amanda.compiler.error import AmandaError
import amanda.compiler.ast as ast


# TODO: Stop concatenating strings. Use buffers instead
class Lexer:
    # Special end of file token
    EOF = "__eof__"
    # Errors that happen during tokenization
    INVALID_SYMBOL = "O símbolo '{symbol}' não foi reconhecido"
    INVALID_STRING = "A sequência de caracteres não foi delimitada"

    def __init__(self, filename, src):
        self.filename = filename
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None
        self.src = src  # A file object

    def set_src(self, src):
        self.src = src
        self.line = 1
        self.pos = 1
        self.current_token = None
        self.current_char = None

    def advance(self):
        if self.current_char == Lexer.EOF:
            return
        self.current_char = self.src.read(1)
        if self.current_char == "":
            self.current_char = Lexer.EOF
        else:
            self.pos += 1

    def lookahead(self):
        last_position = self.src.tell()
        next_char = self.src.read(1)
        self.src.seek(last_position)
        return next_char

    def error(self, code, **kwargs):
        message = code.format(**kwargs)
        raise AmandaError.syntax_error(
            self.filename, message, self.line, self.pos
        )

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
            return self.get_op_token(
                self.current_char, TT.GREATER, TT.GREATEREQ
            )
        elif self.current_char == "=":
            return self.get_op_token(
                self.current_char, TT.EQUAL, TT.DOUBLEEQUAL
            )
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

        return Token(
            TT.INTEGER, int(result), self.line, self.pos - (len(result) + 1)
        )

    def escape_seq(self, char, result, seq):
        if self.lookahead() == char:
            result.write(seq)
            self.advance()
            self.advance()
            return True
        return False

    def string(self):
        result = StringIO()
        symbol = self.current_char
        start_pos = self.pos
        self.advance()
        while self.current_char != symbol:
            if self.current_char == "\\":
                # Attempt to read different control sequences
                # if control sequence is not read, just process
                # the char combination as is
                is_ctl_seq = False
                is_ctl_seq |= self.escape_seq("n", result, "\n")
                is_ctl_seq |= self.escape_seq("'", result, "'")
                is_ctl_seq |= self.escape_seq('"', result, '"')
                if not is_ctl_seq:
                    result.write("\\")
                    self.advance()
                continue
            if self.current_char == Lexer.EOF:
                self.error(self.INVALID_STRING, line=self.line)
            result.write(self.current_char)
            self.advance()
        self.advance()
        whole_str = result.getvalue()
        result.close()
        return Token(
            TT.STRING,
            f"{symbol}{whole_str}{symbol}",
            self.line,
            start_pos,
        )

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
        return Token(
            TT.IDENTIFIER, result, self.line, self.pos - (len(result) + 1)
        )

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
            if self.current_char == ":":
                self.advance()
                return Token(TT.DOUBLECOLON, "::", self.line, self.pos - 1)
            return Token(TT.COLON, char, self.line, self.pos)

    def format_str(self):
        self.advance()
        str_lit = self.string()
        return Token(TT.FORMAT_STR, str_lit.lexeme, str_lit.line, str_lit.col)

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
            if self.current_char == "f" and self.lookahead() in ('"', "'"):
                return self.format_str()
            return self.identifier()
        if self.current_char in (
            "(",
            ")",
            ".",
            ";",
            ",",
            "{",
            "}",
            "[",
            "]",
            ":",
        ):
            return self.delimeters()
        if self.current_char == Lexer.EOF:
            return Token(Lexer.EOF, "")
        self.error(self.INVALID_SYMBOL, symbol=self.current_char)


class Parser:
    # Errors messages
    MISSING_TERM = (
        "as instruções devem ser delimitadas por ';' ou por uma nova linha"
    )
    ILLEGAL_EXPRESSION = "início inválido de expressão"
    EXPECTED_ID = "era esperado um identificador depois do símbolo '{symbol}'"
    EXPECTED_TYPE = "era esperado um tipo depois do símbolo '{symbol}'"
    ILLEGAL_ASSIGN = "alvo inválido para atribuição"

    def __init__(self, filename, io_object):
        self.lexer = Lexer(filename, io_object)
        self.delimited = False
        self.filename = filename
        self.lookahead = self.lexer.get_token()

    def consume(self, expected, error=None, skip_newlines=False) -> Token:
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
        raise AmandaError.syntax_error(
            self.filename, message, err_line, self.lookahead.col
        )

    def skip_newlines(self):
        while self.match(TT.NEWLINE):
            self.lookahead = self.lexer.get_token()

    def match(self, token):
        return self.lookahead.token == token

    def parse(self):
        return self.program()

    def program(self):
        program = ast.Program()
        imports = []
        self.skip_newlines()
        while self.match(TT.USA):
            imports.append(self.usa_stmt())
            self.skip_newlines()

        self.append_child(program, imports)
        while not self.match(Lexer.EOF):
            if self.match(TT.NEWLINE):
                self.consume(TT.NEWLINE)
            else:
                child = self.declaration()
                self.append_child(program, child)
        return program

    def usa_stmt(self):
        token = self.consume(TT.USA)
        module = self.consume(TT.STRING)
        alias = None
        if self.match(TT.COMO):
            self.consume(TT.COMO)
            alias = self.consume(TT.IDENTIFIER)
        self.end_stmt()
        return ast.Usa(token, module=module, alias=alias)

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
        if self.match(TT.IDENTIFIER):
            name = self.consume(TT.IDENTIFIER)
            return ast.Type(name)
        elif self.match(TT.LBRACKET):
            self.consume(TT.LBRACKET)
            el_type = self.type()
            self.consume(TT.RBRACKET)
            return ast.ArrayType(el_type)
        else:
            self.error(
                "Tipo inválido. Esperava um identificador ou a descrição de um vector"
            )

    def end_stmt(self):
        if self.match(TT.NEWLINE):
            self.consume(TT.NEWLINE)
        elif self.match(TT.SEMI):
            self.consume(TT.SEMI)
        elif self.match(Lexer.EOF):
            self.consume(Lexer.EOF)
        else:
            self.error(self.MISSING_TERM)

    def function_header(self):
        name = self.consume(
            TT.IDENTIFIER, self.EXPECTED_ID.format(symbol="func")
        )
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
        return ast.FunctionDecl(
            name=name, block=None, func_type=func_type, params=params
        )

    def native_func_decl(self):
        self.consume(TT.NATIVA)
        function = self.function_header()
        function.is_native = True
        self.end_stmt()
        return function

    def function_decl(self):
        self.consume(TT.FUNC)
        if self.match(TT.NATIVA):
            return self.native_func_decl()
        function = self.function_header()
        function.block = self.block()
        self.consume(
            TT.FIM,
            "O corpo de um função deve ser terminado com a directiva 'fim'",
        )
        return function

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
                if (
                    member_type != ast.FunctionDecl
                    and member_type != ast.VarDecl
                ):
                    self.error(
                        "directiva inválida para o corpo de uma classe",
                        member.lineno,
                    )
                if member_type == ast.VarDecl and member.assign is not None:
                    self.error(
                        "Não pode inicializar os campos de um classe",
                        member.lineno,
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
        elif self.match(TT.QUEBRA) or self.match(TT.CONTINUA):
            return self.loop_ctl_statement()
        else:
            return self.decl_stmt()

    def mostra_statement(self):
        token = self.consume(TT.MOSTRA)
        exp = self.equality()
        self.end_stmt()
        return ast.Mostra(token, exp)

    def loop_ctl_statement(self):
        token = self.consume(self.lookahead.token)
        self.end_stmt()
        return ast.LoopCtlStmt(token)

    def retorna_statement(self):
        token = self.consume(TT.RETORNA)
        if self.match(TT.SEMI) or self.match(TT.NEWLINE):
            exp = None
        else:
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
        self.consume(
            TT.FIM, "esperava-se a símbolo fim para terminar a directiva 'se'"
        )
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
            TT.FIM,
            "esperava-se o símbolo fim para terminar a directiva 'enquanto'",
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
                self.consume(TT.EQUAL),
                left=ast.Variable(name),
                right=self.equality(),
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
            name = self.consume(
                TT.IDENTIFIER, self.EXPECTED_ID.format(symbol=",")
            )
            names.append(name)
        token = self.consume(TT.COLON)
        var_type = self.type()
        decls = []
        for var_name in names:
            decl = ast.VarDecl(
                token, name=var_name, var_type=var_type, assign=None
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

    def compound_assignment(self):
        expr = self.assignment()
        compound_operator = (TT.PLUSEQ, TT.MINUSEQ, TT.SLASHEQ, TT.STAREQ)
        current = self.lookahead.token
        if current in compound_operator:
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            # Create separate tokens
            token = Token(
                None, None, line=self.lookahead.line, col=self.lookahead.col
            )
            eq = Token(
                TT.EQUAL, "=", line=self.lookahead.line, col=self.lookahead.col
            )
            token.token, token.lexeme = self.compound_operator()
            self.consume(current)
            if isinstance(expr, ast.Get):
                expr = ast.Set(target=expr, expr=self.assignment())
            elif isinstance(expr, ast.IndexGet):
                expr = ast.IndexSet(
                    token,
                    expr,
                    ast.BinOp(token, left=expr, right=self.equality()),
                )
            else:
                expr = ast.Assign(
                    eq,
                    left=expr,
                    right=ast.BinOp(token, left=expr, right=self.equality()),
                )
        return expr

    def assignment(self):
        expr = self.equality()
        if self.match(TT.EQUAL):
            token = self.consume(TT.EQUAL)
            if not expr.is_assignable():
                self.error(self.ILLEGAL_ASSIGN)
            if isinstance(expr, ast.Get):
                expr = ast.Set(target=expr, expr=self.assignment())
            elif isinstance(expr, ast.IndexGet):
                expr = ast.IndexSet(token, expr, self.assignment())
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
        while self.lookahead.token in (
            TT.GREATER,
            TT.GREATEREQ,
            TT.LESS,
            TT.LESSEQ,
        ):
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
                    TT.RPAR,
                    "os argumentos da função devem ser delimitados por ')'",
                )
                expr = ast.Call(callee=expr, paren=token, fargs=args)
            elif self.match(TT.LBRACKET):
                self.consume(TT.LBRACKET)
                index = self.equality()
                token = self.consume(TT.RBRACKET)
                expr = ast.IndexGet(token, expr, index)
            else:
                self.consume(TT.DOT)
                identifier = self.lookahead
                self.consume(TT.IDENTIFIER)
                expr = ast.Get(target=expr, member=identifier)
        if self.match(TT.DOUBLECOLON):
            token = self.consume(TT.DOUBLECOLON)
            new_type = self.type()
            return ast.Converta(token, expr, new_type)
        return expr

    def parse_fstr_expr(self, token, format_str):
        # Save current parsing state
        ctx_lex = self.lexer
        ctx_tok = self.lookahead

        # Get current expr
        # TODO: Use only one buffer
        expr = StringIO()
        current_str = StringIO()
        char = format_str.read(1)
        while char != "}" and char != "":
            expr.write(char)
            char = format_str.read(1)
        if char == "":
            self.error(
                "String de formatação inválida. Expressões devem ser delimitadas por '{' e '}'"
            )

        # Parse expression
        expr_str = expr.getvalue().strip()
        if not len(expr_str):
            self.error(
                "String de formatação inválida. Expressões vazias não são permitidas"
            )
        # Cannot nest fstrings
        if expr_str[:2] in ("f'", 'f"'):
            self.error(
                "String de formatação inválida. Não pode ter uma f-string dentro de outra f-string"
            )
        expr.seek(0)
        self.lexer = Lexer(self.filename, expr)
        try:
            self.lookahead = self.lexer.get_token()
            expression = self.equality()
        except AmandaError as e:
            raise AmandaError.syntax_error(
                self.filename, e.message, token.line, token.col
            )
        # Restore state
        self.lexer = ctx_lex
        self.lookahead = ctx_tok

        return expression

    def parse_format_str(self):
        token = self.consume(self.lookahead.token)
        # Exclude delimiters from string
        format_str = StringIO(token.lexeme[1:-1])
        char = format_str.read(1)
        parts = []

        tokenify_str = lambda lexeme: ast.Constant(
            Token(TT.STRING, lexeme=lexeme, line=token.line, col=token.col)
        )
        # TODO: Reuse this buffer
        current_str = StringIO()
        # Indicates whether fstr has at least one expression
        has_expr = False
        # Separate the string into individual expressions
        # Everything up to an '{}' will be a separate string
        while char != "":
            if char == "{":
                pos = format_str.tell()
                next_char = format_str.read(1)
                format_str.seek(pos)
                # Found a double "{{", do not treat as expression
                if next_char == "{":
                    current_str.write("{")
                    # Get char after "{{"
                    format_str.read(1)
                    char = format_str.read(1)
                    continue
                lexeme = current_str.getvalue()
                if len(lexeme) > 0:
                    parts.append(tokenify_str(lexeme))
                has_expr = True
                current_str = StringIO()
                parts.append(self.parse_fstr_expr(token, format_str))
                char = format_str.read(1)
                continue
            current_str.write(char)
            char = format_str.read(1)

        buff_str = current_str.getvalue()
        if buff_str:
            parts.append(tokenify_str(buff_str))
        if not has_expr:
            return parts[0]
        return ast.FmtStr(token, parts)

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
            expr = ast.ListLiteral(
                token, list_type=list_type, elements=elements
            )
        elif self.match(TT.FORMAT_STR):
            return self.parse_format_str()
        elif self.match(TT.LPAR):
            self.consume(TT.LPAR)
            expr = self.equality()
            self.consume(TT.RPAR)
        elif self.match(TT.EU):
            expr = ast.Eu(self.lookahead)
            self.consume(TT.EU)
        else:
            self.error(
                f"início inválido de expressão: '{self.lookahead.lexeme}'"
            )
        return expr

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


def parse(filename):
    with open(filename, encoding="utf-8") as src_file:
        src = StringIO(src_file.read())
    return Parser(filename, src).parse()
