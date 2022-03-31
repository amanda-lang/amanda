import sys
import pdb
from io import StringIO
import amanda.compiler.symbols as symbols
from amanda.compiler.type import Type, Kind
import amanda.compiler.ast as ast
from amanda.compiler.error import AmandaError, throw_error


class Generator:
    INDENT = "    "

    def __init__(self):
        self.py_lineno = 0  # tracks lineno in compiled python src
        self.ama_lineno = 1  # tracks lineno in input amanda src
        self.depth = -1  # current indent level
        self.func_depth = 0
        self.class_depth = 0
        self.program_symtab = None
        self.scope_symtab = None
        self.ctx_module = None
        self.line_info = {}  # Maps py_fileno to ama_fileno

    def generate_code(self, program):
        """ Method that begins compilation of amanda source."""
        self.program_symtab = self.scope_symtab = program.symbols
        py_code = self.gen(program)
        return (py_code, self.line_info)

    def bad_gen(self, node):
        raise NotImplementedError(
            f"Cannot generate code for this node type yet: (TYPE) {type(node)}"
        )

    def gen(self, node, args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self, method_name, self.bad_gen)
        # Update line only if node type has line attribute
        self.ama_lineno = getattr(node, "lineno", self.ama_lineno)
        if node_class == "block":
            return gen_method(node, args)
        return gen_method(node)

    def gen_program(self, node):
        return self.compile_block(node, [])

    def gen_usa(self, node):
        module = node.ast
        generator = Generator()
        mod_src, _ = generator.generate_code(module)
        self.py_lineno += generator.py_lineno
        return mod_src

    def update_line_info(self):
        self.line_info[self.py_lineno] = self.ama_lineno
        self.py_lineno += 1

    def build_str(self, str_buffer):
        string = str_buffer.getvalue()
        str_buffer.close()
        return string

    def compile_block(self, node, stmts):
        # stmts param is a list of stmts
        # node defined here because caller may want
        # to add custom statement to the beginning of
        # a block
        self.depth += 1
        indent_level = self.INDENT * self.depth
        self.scope_symtab = node.symbols
        # Newline for header
        self.update_line_info()
        block = StringIO()
        # Add caller stmts to buffer
        for stmt in stmts:
            block.write(indent_level + stmt)
            block.write("\n")
            self.update_line_info()

        for child in node.children:
            block.write(indent_level + self.gen(child))
            block.write("\n")
            self.update_line_info()
        self.depth -= 1
        self.scope_symtab = self.scope_symtab.enclosing_scope
        # Add pass statement
        if len(block.getvalue()) == 0:
            block.write(f"{indent_level}pass")
            block.write("\n")
            self.update_line_info()
        return self.build_str(block)

    def gen_vardecl(self, node):
        assign = node.assign
        name = node.name.lexeme
        symbol = self.scope_symtab.resolve(name)
        if assign:
            value = self.gen(assign.right)
        else:
            # Check for initializer
            init_values = {
                "int": 0,
                "real": 0.0,
                "bool": "falso",
                "texto": '''""''',
            }
            value = init_values.get(str(node.var_type))
        return f"{symbol.out_id} = {value}"

    def gen_functiondecl(self, node):
        name = node.name.lexeme
        func_def = StringIO()
        func_symbol = self.scope_symtab.resolve(name)
        name = func_symbol.out_id
        params = []
        if func_symbol.is_property:
            params.append("eu")
        for param in func_symbol.params.values():
            params.append(param.out_id)
        params = ",".join(params)
        func_def.write(f"def {name}({params}):\n")
        self.func_depth += 1
        func_def.write(
            self.get_func_block(node.block),
        )
        self.func_depth -= 1
        return self.build_str(func_def)

    def gen_classdecl(self, node):
        name = node.name.lexeme
        class_def = StringIO()
        klass = self.scope_symtab.resolve(name)
        name = klass.out_id
        # name of base class for user defined types
        base_class = "_BaseClass_"
        class_def.write(f"class {name}(_BaseClass_):\n")
        self.class_depth += 1
        class_def.write(self.compile_block(node.body, []))
        self.class_depth -= 1
        return self.build_str(class_def)

    def get_func_block(self, block):
        # Add global and nonlocal statements
        # to beginning of a function
        stmts = []
        scope = block.symbols
        if self.func_depth >= 1:
            global_stmt = self.gen_global_stmt()
            if global_stmt:
                stmts.append(global_stmt)
        if self.func_depth > 1:
            non_local = self.gen_nonlocal_stmt(scope)
            if non_local:
                stmts.append(non_local)
        return self.compile_block(block, stmts)

    def get_names(self, scope, include_funcs=False):
        names = []
        for symbol in scope.symbols.values():
            symbol_type = type(symbol)

            if symbol_type == symbols.VariableSymbol or (
                include_funcs and symbol_type == symbols.FunctionSymbol
            ):
                names.append(symbol.out_id)

        return names

    # TODO: Fix unecessary forward global declarations
    def gen_global_stmt(self):
        """Adds global statements to
        the beginning of a function"""
        names = self.get_names(self.program_symtab)
        if len(names) == 0:
            return None
        names = ",".join(names)
        return f"global {names}"

    def gen_nonlocal_stmt(self, scope):
        """Adds nonlocal statements to
        the beginning of a function"""
        names = []
        scope = scope.enclosing_scope
        while scope and scope.enclosing_scope is not None:
            names += self.get_names(scope)
            scope = scope.enclosing_scope
        if len(names) == 0:
            return None
        names = ",".join(names)
        return f"nonlocal {names}"

    def gen_listliteral(self, node):
        elements = ",".join(
            [str(self.gen(element)) for element in node.elements]
        )
        list_type = node.eval_type.get_type()
        return f"Lista({list_type},[{elements}])"

    def gen_call(self, node):
        args = ",".join([str(self.gen(arg)) for arg in node.fargs])
        callee = self.gen(node.callee)
        func_call = f"{callee}({args})"
        return self.gen_expression(func_call, node.prom_type)

    def gen_eu(self, node):
        return "eu"

    def gen_set(self, node):
        target = self.gen(node.target)
        expr = self.gen(node.expr)
        return f"{target} = {expr}"

    def gen_index(self, node):
        target = self.gen(node.target)
        index = self.gen(node.index)
        index_expr = f"{target}[{index}]"
        return self.gen_expression(index_expr, node.prom_type)

    def gen_get(self, node):
        target = self.gen(node.target)
        member = node.member.lexeme
        klass = node.target.eval_type
        member_sym = klass.members.get(member)
        get_expr = f"{target}.{member_sym.out_id}"
        return self.gen_expression(get_expr, node.prom_type)

    def gen_assign(self, node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        return f"{lhs} = {rhs}"

    def gen_constant(self, node):
        prom_type = node.prom_type
        literal = str(node.token.lexeme)
        return self.gen_expression(literal, prom_type)

    def gen_variable(self, node):
        name = node.token.lexeme
        symbol = node.var_symbol
        # TODO: Make sure that every identifier goes through
        # 'visit_variable' so that symbol attribute can be set
        if symbol is None:
            symbol = self.scope_symtab.resolve(name)
        expr = symbol.out_id
        if self.func_depth > 0 and symbol.is_property:
            expr = f"eu.{expr}"
        prom_type = node.prom_type
        return self.gen_expression(expr, prom_type)

    def gen_binop(self, node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        operator = node.token.lexeme
        if operator == "e":
            operator = "and"
        elif operator == "ou":
            operator = "or"
        binop = f"({lhs} {operator} {rhs})"
        # Promote node
        return self.gen_expression(binop, node.prom_type)

    def gen_unaryop(self, node):
        operator = node.token.lexeme
        operand = self.gen(node.operand)
        if operator == "nao":
            operator = "not"
        unaryop = f"({operator} {operand})"
        return self.gen_expression(unaryop, node.prom_type)

    def gen_converte(self, node):
        expr = self.gen(node.expression)
        new_type = node.new_type
        type_name = str(self.scope_symtab.resolve(new_type.type_name.lexeme))
        if new_type.is_list:
            new_type = f"Lista({type_name},[])"
        else:
            new_type = type_name
        return f"converte({expr},{new_type})"

    def gen_expression(self, expression, prom_type):
        if prom_type == None:
            return expression
        if prom_type.otype == Kind.TINDEF:
            return f"indef({expression})"
        elif prom_type.otype == Kind.TREAL:
            return f"float({expression})"
        else:
            return expression

    def gen_senaose(self, node):
        senaose_stmt = StringIO()
        condition = self.gen(node.condition)
        then_branch = self.compile_branch(node.then_branch)
        indent_level = self.INDENT * self.depth
        senaose_stmt.write(f"{indent_level}elif {condition}:\n{then_branch}")
        return self.build_str(senaose_stmt)

    def gen_se(self, node):
        if_stmt = StringIO()
        condition = self.gen(node.condition)
        then_branch = self.compile_branch(node.then_branch)
        elsif_branches = "".join(
            [self.gen(branch) for branch in node.elsif_branches]
        )
        if_stmt.write(f"if {condition}:\n{then_branch}")
        if_stmt.write(f"{elsif_branches}")
        if node.else_branch:
            indent_level = self.INDENT * self.depth
            else_branch = self.compile_branch(node.else_branch)
            if_stmt.write(f"\n{indent_level}else:\n{else_branch}")
        return self.build_str(if_stmt)

    def compile_branch(self, block):
        scope = block.symbols
        branch = self.compile_block(block, [])
        names = self.get_names(scope, include_funcs=True)
        if len(names) > 0:
            self.update_line_info()
            names = ",".join(names)
            indent_level = self.INDENT * (self.depth + 1)
            branch += f"{indent_level}del {names}"
        return branch

    def gen_enquanto(self, node):
        condition = self.gen(node.condition)
        body = self.compile_branch(node.statement)
        return f"while {condition}:\n{body}"

    def gen_escolha(self, node):
        switch = StringIO()
        expr = self.gen(node.expression)
        cases = node.cases
        default = node.default_case
        indent = self.INDENT * self.depth
        # No need to generate code
        if not len(cases) and not default:
            return ""
        for c, case in enumerate(cases):
            value = self.gen(case.expression)
            block = self.compile_block(case.block, [])
            if c == 0:
                switch.write(f"if {expr} == {value}:\n{block}")
            else:
                switch.write(f"{indent}elif {expr} == {value}:\n{block}")
        if default:
            block = self.compile_block(default, [])
            if not len(cases):
                switch.write(f"if True:\n{block}")
            else:
                switch.write(f"{indent}else:\n{block}")
        return self.build_str(switch)

    def gen_para(self, node):
        scope = node.statement.symbols
        # Change control var name to local name
        para_expr = node.expression
        control_var = scope.resolve(para_expr.name.lexeme)
        body = self.compile_branch(node.statement)
        expression = self.gen_paraexpr(para_expr, control_var)
        return f"for {expression}:\n{body}"

    def gen_paraexpr(self, node, control_var):
        range_expr = node.range_expr
        name = control_var.out_id
        start = self.gen(range_expr.start)
        stop = self.gen(range_expr.end)
        inc = f"-1 if {start} > {stop} else 1"
        if range_expr.inc:
            inc = self.gen(range_expr.inc)
        return f"{name} in range({start},{stop},{inc})"

    def gen_retorna(self, node):
        expression = self.gen(node.exp)
        return f"return {expression}"

    def gen_mostra(self, node):
        expression = self.gen(node.exp)
        if node.exp.eval_type.otype == Kind.TVAZIO:
            expression = "vazio"
        return f"printc({expression})"


class Generator:
    INDENT = "    "

    def __init__(self):
        self.py_lineno = 0  # tracks lineno in compiled python src
        self.ama_lineno = 1  # tracks lineno in input amanda src
        self.depth = -1  # current indent level
        self.func_depth = 0
        self.class_depth = 0
        self.program_symtab = None
        self.scope_symtab = None
        self.ctx_module = None
        self.line_info = {}  # Maps py_fileno to ama_fileno

    def generate_code(self, program):
        """ Method that begins compilation of amanda source."""
        self.program_symtab = self.scope_symtab = program.symbols
        py_code = self.gen(program)
        return (py_code, self.line_info)

    def bad_gen(self, node):
        raise NotImplementedError(
            f"Cannot generate code for this node type yet: (TYPE) {type(node)}"
        )

    def gen(self, node, args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self, method_name, self.bad_gen)
        # Update line only if node type has line attribute
        self.ama_lineno = getattr(node, "lineno", self.ama_lineno)
        if node_class == "block":
            return gen_method(node, args)
        return gen_method(node)

    def gen_program(self, node):
        return self.compile_block(node, [])

    def gen_usa(self, node):
        module = node.ast
        generator = Generator()
        mod_src, _ = generator.generate_code(module)
        self.py_lineno += generator.py_lineno
        return mod_src

    def update_line_info(self):
        self.line_info[self.py_lineno] = self.ama_lineno
        self.py_lineno += 1

    def build_str(self, str_buffer):
        string = str_buffer.getvalue()
        str_buffer.close()
        return string

    def compile_block(self, node, stmts):
        # stmts param is a list of stmts
        # node defined here because caller may want
        # to add custom statement to the beginning of
        # a block
        self.depth += 1
        indent_level = self.INDENT * self.depth
        self.scope_symtab = node.symbols
        # Newline for header
        self.update_line_info()
        block = StringIO()
        # Add caller stmts to buffer
        for stmt in stmts:
            block.write(indent_level + stmt)
            block.write("\n")
            self.update_line_info()

        for child in node.children:
            block.write(indent_level + self.gen(child))
            block.write("\n")
            self.update_line_info()
        self.depth -= 1
        self.scope_symtab = self.scope_symtab.enclosing_scope
        # Add pass statement
        if len(block.getvalue()) == 0:
            block.write(f"{indent_level}pass")
            block.write("\n")
            self.update_line_info()
        return self.build_str(block)

    def gen_vardecl(self, node):
        assign = node.assign
        name = node.name.lexeme
        symbol = self.scope_symtab.resolve(name)
        if assign:
            value = self.gen(assign.right)
        else:
            # Check for initializer
            init_values = {
                "int": 0,
                "real": 0.0,
                "bool": "falso",
                "texto": '''""''',
            }
            value = init_values.get(str(node.var_type))
        return f"{symbol.out_id} = {value}"

    def gen_functiondecl(self, node):
        name = node.name.lexeme
        func_def = StringIO()
        func_symbol = self.scope_symtab.resolve(name)
        name = func_symbol.out_id
        params = []
        if func_symbol.is_property:
            params.append("eu")
        for param in func_symbol.params.values():
            params.append(param.out_id)
        params = ",".join(params)
        func_def.write(f"def {name}({params}):\n")
        self.func_depth += 1
        func_def.write(
            self.get_func_block(node.block),
        )
        self.func_depth -= 1
        return self.build_str(func_def)

    def gen_classdecl(self, node):
        name = node.name.lexeme
        class_def = StringIO()
        klass = self.scope_symtab.resolve(name)
        name = klass.out_id
        # name of base class for user defined types
        base_class = "_BaseClass_"
        class_def.write(f"class {name}(_BaseClass_):\n")
        self.class_depth += 1
        class_def.write(self.compile_block(node.body, []))
        self.class_depth -= 1
        return self.build_str(class_def)

    def get_func_block(self, block):
        # Add global and nonlocal statements
        # to beginning of a function
        stmts = []
        scope = block.symbols
        if self.func_depth >= 1:
            global_stmt = self.gen_global_stmt()
            if global_stmt:
                stmts.append(global_stmt)
        if self.func_depth > 1:
            non_local = self.gen_nonlocal_stmt(scope)
            if non_local:
                stmts.append(non_local)
        return self.compile_block(block, stmts)

    def get_names(self, scope, include_funcs=False):
        names = []
        for symbol in scope.symbols.values():
            symbol_type = type(symbol)

            if symbol_type == symbols.VariableSymbol or (
                include_funcs and symbol_type == symbols.FunctionSymbol
            ):
                names.append(symbol.out_id)

        return names

    # TODO: Fix unecessary forward global declarations
    def gen_global_stmt(self):
        """Adds global statements to
        the beginning of a function"""
        names = self.get_names(self.program_symtab)
        if len(names) == 0:
            return None
        names = ",".join(names)
        return f"global {names}"

    def gen_nonlocal_stmt(self, scope):
        """Adds nonlocal statements to
        the beginning of a function"""
        names = []
        scope = scope.enclosing_scope
        while scope and scope.enclosing_scope is not None:
            names += self.get_names(scope)
            scope = scope.enclosing_scope
        if len(names) == 0:
            return None
        names = ",".join(names)
        return f"nonlocal {names}"

    def gen_listliteral(self, node):
        elements = ",".join(
            [str(self.gen(element)) for element in node.elements]
        )
        list_type = node.eval_type.get_type()
        return f"Lista({list_type},[{elements}])"

    def gen_call(self, node):
        args = ",".join([str(self.gen(arg)) for arg in node.fargs])
        callee = self.gen(node.callee)
        func_call = f"{callee}({args})"
        return self.gen_expression(func_call, node.prom_type)

    def gen_eu(self, node):
        return "eu"

    def gen_set(self, node):
        target = self.gen(node.target)
        expr = self.gen(node.expr)
        return f"{target} = {expr}"

    def gen_index(self, node):
        target = self.gen(node.target)
        index = self.gen(node.index)
        index_expr = f"{target}[{index}]"
        return self.gen_expression(index_expr, node.prom_type)

    def gen_get(self, node):
        target = self.gen(node.target)
        member = node.member.lexeme
        klass = node.target.eval_type
        member_sym = klass.members.get(member)
        get_expr = f"{target}.{member_sym.out_id}"
        return self.gen_expression(get_expr, node.prom_type)

    def gen_assign(self, node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        return f"{lhs} = {rhs}"

    def gen_constant(self, node):
        prom_type = node.prom_type
        literal = str(node.token.lexeme)
        return self.gen_expression(literal, prom_type)

    def gen_variable(self, node):
        name = node.token.lexeme
        symbol = node.var_symbol
        # TODO: Make sure that every identifier goes through
        # 'visit_variable' so that symbol attribute can be set
        if symbol is None:
            symbol = self.scope_symtab.resolve(name)
        expr = symbol.out_id
        if self.func_depth > 0 and symbol.is_property:
            expr = f"eu.{expr}"
        prom_type = node.prom_type
        return self.gen_expression(expr, prom_type)

    def gen_binop(self, node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        operator = node.token.lexeme
        if operator == "e":
            operator = "and"
        elif operator == "ou":
            operator = "or"
        binop = f"({lhs} {operator} {rhs})"
        # Promote node
        return self.gen_expression(binop, node.prom_type)

    def gen_unaryop(self, node):
        operator = node.token.lexeme
        operand = self.gen(node.operand)
        if operator == "nao":
            operator = "not"
        unaryop = f"({operator} {operand})"
        return self.gen_expression(unaryop, node.prom_type)

    def gen_converte(self, node):
        expr = self.gen(node.expression)
        new_type = node.new_type
        type_name = str(self.scope_symtab.resolve(new_type.type_name.lexeme))
        if new_type.is_list:
            new_type = f"Lista({type_name},[])"
        else:
            new_type = type_name
        return f"converte({expr},{new_type})"

    def gen_expression(self, expression, prom_type):
        if prom_type == None:
            return expression
        if prom_type.otype == Kind.TINDEF:
            return f"indef({expression})"
        elif prom_type.otype == Kind.TREAL:
            return f"float({expression})"
        else:
            return expression

    def gen_senaose(self, node):
        senaose_stmt = StringIO()
        condition = self.gen(node.condition)
        then_branch = self.compile_branch(node.then_branch)
        indent_level = self.INDENT * self.depth
        senaose_stmt.write(f"{indent_level}elif {condition}:\n{then_branch}")
        return self.build_str(senaose_stmt)

    def gen_se(self, node):
        if_stmt = StringIO()
        condition = self.gen(node.condition)
        then_branch = self.compile_branch(node.then_branch)
        elsif_branches = "".join(
            [self.gen(branch) for branch in node.elsif_branches]
        )
        if_stmt.write(f"if {condition}:\n{then_branch}")
        if_stmt.write(f"{elsif_branches}")
        if node.else_branch:
            indent_level = self.INDENT * self.depth
            else_branch = self.compile_branch(node.else_branch)
            if_stmt.write(f"\n{indent_level}else:\n{else_branch}")
        return self.build_str(if_stmt)

    def compile_branch(self, block):
        scope = block.symbols
        branch = self.compile_block(block, [])
        names = self.get_names(scope, include_funcs=True)
        if len(names) > 0:
            self.update_line_info()
            names = ",".join(names)
            indent_level = self.INDENT * (self.depth + 1)
            branch += f"{indent_level}del {names}"
        return branch

    def gen_enquanto(self, node):
        condition = self.gen(node.condition)
        body = self.compile_branch(node.statement)
        return f"while {condition}:\n{body}"

    def gen_escolha(self, node):
        switch = StringIO()
        expr = self.gen(node.expression)
        cases = node.cases
        default = node.default_case
        indent = self.INDENT * self.depth
        # No need to generate code
        if not len(cases) and not default:
            return ""
        for c, case in enumerate(cases):
            value = self.gen(case.expression)
            block = self.compile_block(case.block, [])
            if c == 0:
                switch.write(f"if {expr} == {value}:\n{block}")
            else:
                switch.write(f"{indent}elif {expr} == {value}:\n{block}")
        if default:
            block = self.compile_block(default, [])
            if not len(cases):
                switch.write(f"if True:\n{block}")
            else:
                switch.write(f"{indent}else:\n{block}")
        return self.build_str(switch)

    def gen_para(self, node):
        scope = node.statement.symbols
        # Change control var name to local name
        para_expr = node.expression
        control_var = scope.resolve(para_expr.name.lexeme)
        body = self.compile_branch(node.statement)
        expression = self.gen_paraexpr(para_expr, control_var)
        return f"for {expression}:\n{body}"

    def gen_paraexpr(self, node, control_var):
        range_expr = node.range_expr
        name = control_var.out_id
        start = self.gen(range_expr.start)
        stop = self.gen(range_expr.end)
        inc = f"-1 if {start} > {stop} else 1"
        if range_expr.inc:
            inc = self.gen(range_expr.inc)
        return f"{name} in range({start},{stop},{inc})"

    def gen_retorna(self, node):
        expression = self.gen(node.exp)
        return f"return {expression}"

    def gen_mostra(self, node):
        expression = self.gen(node.exp)
        if node.exp.eval_type.otype == Kind.TVAZIO:
            expression = "vazio"
        return f"printc({expression})"
