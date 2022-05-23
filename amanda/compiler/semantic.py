import copy
import keyword
from os import path
from amanda.compiler.parse import parse
from amanda.compiler.tokens import TokenType as TT, Token
import amanda.compiler.ast as ast
import amanda.compiler.symbols as symbols
from amanda.compiler.type import builtin_types, Kind, Type, Vector, Klass
from amanda.compiler.error import AmandaError
from amanda.compiler.builtinfn import BUILTINS, BuiltinFn
from amanda.config import STD_LIB


class Analyzer(ast.Visitor):

    # Error messages
    ID_IN_USE = "O identificador '{name}' já foi declarado neste escopo"
    INVALID_REF = "o identificador '{name}' não é uma referência válida"

    def __init__(self, filename, module):
        # Relative path to the file being run
        self.filename = filename
        # Just to have quick access to things like types and e.t.c
        self.global_scope = symbols.Scope()
        self.scope_depth = 0
        self.ctx_scope = self.global_scope
        self.ctx_node = None
        self.ctx_class = None
        self.ctx_func = None
        self.in_loop = False
        self.imports = {}
        # Module currently being executed
        self.ctx_module = module

        # Initialize builtin types
        for type_id, sym in builtin_types:
            self.global_scope.define(type_id, sym)

        # Load builtin module
        module = symbols.Module(path.join(STD_LIB, "embutidos.ama"))
        self.load_module(module)

    def has_return(self, node):
        """Method that checks if function non void
        function has return statement"""
        node_class = type(node).__name__.lower()
        method_name = f"has_return_{node_class}"
        visitor_method = getattr(self, method_name, self.general_check)
        self.ctx_node = node
        return visitor_method(node)

    def has_return_block(self, node):
        for child in node.children:
            has_return = self.has_return(child)
            if has_return:
                return True
        return False

    def has_return_se(self, node):
        """Method checks for return within
        'se' statements"""
        # If there is no else branch return None immediately
        return (
            False if not node.else_branch else self.has_return(node.else_branch)
        )

    def has_return_enquanto(self, node):
        return self.has_return(node.statement)

    def has_return_para(self, node):
        return self.has_return(node.statement)

    def has_return_retorna(self, node):
        return True

    def general_check(self, node):
        return False

    def general_visit(self, node):
        raise NotImplementedError(
            f"Have not defined method for this node type: {type(node)} {node.__dict__}"
        )

    def error(self, code, **kwargs):
        message = code.format(**kwargs)
        raise AmandaError.common_error(
            self.ctx_module.fpath, message, self.ctx_node.token.line
        )

    def is_valid_name(self, name):
        """Checks whether name is a python keyword, reserved var or
        python builtin object"""
        return not (
            keyword.iskeyword(name)
            or (name.startswith("_") and name.endswith("_"))
            or name in globals().get("__builtins__")
        )

    # 1.Any functions declared inside another
    # should also be regarded as a local
    # 2. After inner function local params are declared,
    # use the non local stmt to get nonlocal names
    # 3. Local names are depth dependent
    # at level 2 __r10__,__r11__
    def define_symbol(self, symbol, depth, scope):
        if not self.is_valid_name(symbol.name) or depth >= 1:
            symbol.out_id = f"_r{depth}{scope.count()}_"
        scope.define(symbol.name, symbol)

    def get_type(self, type_node):
        if not type_node:
            return self.ctx_scope.resolve("vazio")
        node_t = type(type_node)
        if node_t == ast.Type or node_t == ast.Variable:
            type_id = (
                type_node.name.lexeme
                if node_t == ast.Type
                else type_node.token.lexeme
            )
            type_symbol = self.ctx_scope.resolve(type_id)
            if not type_symbol or not type_symbol.is_type():
                self.error(f"o tipo '{type_id}' não foi declarado")
            return type_symbol
        elif type(type_node) == ast.ArrayType:
            return Vector(self.get_type(type_node.element_type))

    def types_match(self, expected, received):
        return expected == received or received.promote_to(expected)

    def visit(self, node, args=None):
        node_class = type(node).__name__.lower()
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self, method_name, self.general_visit)
        self.ctx_node = node
        if node_class == "block":
            return visitor_method(node, args)
        return visitor_method(node)

    def visit_or_transform(self, node):
        nodeT = type(node)
        self.visit(node)
        has_side_fx = (
            ast.Assign,
            ast.Call,
            ast.Set,
            ast.IndexGet,
            ast.IndexSet,
        )
        # TODO: Actually implement a jump table for escolha
        if nodeT == ast.Escolha:
            token = node.token
            new_token = lambda tt, lexeme: Token(
                tt, lexeme, token.line, token.col
            )
            equality_op = lambda left, right: ast.BinOp(
                new_token(TT.DOUBLEEQUAL, "=="), left=left, right=right
            )
            # check node
            # transform node into ifs
            expr = node.expression
            # let
            se_node = ast.Se(
                token, None, None, elsif_branches=[], else_branch=None
            )
            if not node.cases and not node.default_case:
                return None
            elif not node.cases and node.default_case:
                se_node.condition = ast.Constant(
                    new_token(TT.VERDADEIRO, "verdadeiro")
                )
                se_node.then_branch = node.default_case
                return se_node
            else:
                first_case = node.cases[0]
                del node.cases[0]
                se_node.condition = equality_op(
                    left=first_case.expression,
                    right=node.expression,
                )
                se_node.then_branch = first_case.block
                se_node.else_branch = node.default_case
                for case in node.cases:
                    se_node.elsif_branches.append(
                        ast.SenaoSe(
                            token,
                            equality_op(
                                left=case.expression, right=node.expression
                            ),
                            case.block,
                        )
                    )
                return se_node
        # Ignore all unused expressions
        # WARNING: This might be a nasty bug, please test this
        # TODO: Implement a proper way to do this
        elif nodeT not in has_side_fx and isinstance(node, ast.Expr):
            return None
        else:
            return node

    def visit_children(self, children):
        none_count = 0
        for i, child in enumerate(children):
            node = self.visit_or_transform(child)
            if node == None:
                none_count += 1
            children[i] = node

        # TODO: Find a better way to manipulate child list
        for i in range(none_count):
            children.remove(None)

    def visit_program(self, node):
        # Since each function has it's own local scope,
        # The top level global scope will have it's own "locals"
        self.visit_children(node.children)
        node.symbols = self.global_scope
        return node

    def load_module(self, module):
        existing_mod = self.imports.get(module.fpath)
        # Module has already been loaded
        if existing_mod and existing_mod.loaded:
            return
        # Check for a cycle
        # A cycle occurs when a previously seen module
        # is seen again, but it is not loaded yet
        if existing_mod and not existing_mod.loaded:
            self.error(f"Erro ao importar módulo. inclusão cíclica detectada")

        prev_module = self.ctx_module
        self.ctx_module = module
        self.imports[module.fpath] = module

        # TODO: Handle errors while loading another module
        module.ast = self.visit_program(parse(module.fpath))

        module.loaded = True
        self.ctx_module = prev_module

    def visit_usa(self, node):
        fpath = node.module.lexeme.replace("'", "").replace('"', "")
        # Check if path refers to a valid file
        head, tail = path.split(fpath)
        err_msg = f"Erro ao importar módulo. O caminho '{fpath}' não é um ficheiro válido"
        if not tail:
            self.error(err_msg)
        # If file doesn't have .ama extensions, add it
        if tail.split(".")[-1] != "ama":
            tail = tail + ".ama"
        fpath = path.join(head, tail)
        if not path.isfile(fpath):
            self.error(err_msg)

        mod_path = path.abspath(fpath)
        module = symbols.Module(mod_path)
        self.load_module(module)

    def visit_vardecl(self, node):
        name = node.name.lexeme
        if self.ctx_scope.get(name):
            self.error(self.ID_IN_USE, name=name)
        var_type = self.get_type(node.var_type)
        symbol = symbols.VariableSymbol(name, var_type)
        self.define_symbol(symbol, self.scope_depth, self.ctx_scope)
        node.var_type = var_type
        assign = node.assign
        if assign is not None:
            if assign.right.token.lexeme == name:
                self.error(
                    f"Erro ao inicializar variável. Não pode referenciar uma variável durante a sua declaração"
                )
            self.visit(assign)
        if self.scope_depth == 0:
            symbol.is_global = True

    def visit_functiondecl(self, node):
        # TODO: Will add closures to make up for lack of local functions
        if self.scope_depth > 0:
            self.error(f"As funções só podem ser declaradas no escopo global")

        # Check if id is already in use
        name = node.name.lexeme
        if self.ctx_scope.get(name):
            self.error(self.ID_IN_USE, name=name)

        # Check that func is within max param number
        if len(node.params) > (2 ** 8) - 1:
            self.error(f"As funções só podem ter até 255 parâmetros")

        function_type = self.get_type(node.func_type)

        # Check if non void function has return
        symbol = symbols.FunctionSymbol(name, function_type)
        symbol.is_global = True
        self.define_symbol(symbol, self.scope_depth, self.ctx_scope)
        scope, symbol.params = self.define_func_scope(name, node.params)

        # Native functions don't have a body, so there's nothing to visit
        if node.is_native:
            return

        has_return = self.has_return(node.block)
        if not has_return and function_type.kind != Kind.TVAZIO:
            self.ctx_node = node
            self.error(f"a função '{name}' não possui a instrução 'retorna'")

        prev_function = self.ctx_func
        self.ctx_func = symbol

        self.visit(node.block, scope)

        self.ctx_func = prev_function

        symbol.scope = scope

    def define_func_scope(self, name, params):
        params_dict = {}
        klass = self.ctx_class
        for param in params:
            param_name = param.name.lexeme
            if params_dict.get(param_name):
                self.error(
                    f"o parâmetro '{param_name}' já foi especificado nesta função"
                )
            param_symbol = self.visit(param)
            params_dict[param_name] = param_symbol
        scope = symbols.Scope(self.ctx_scope)
        for param_name, param in params_dict.items():
            self.define_symbol(param, self.scope_depth + 1, scope)
            scope.add_local(param.out_id)
        return (scope, params_dict)

    def visit_classdecl(self, node):
        name = node.name.lexeme
        if self.ctx_scope.get(name):
            self.error(self.ID_IN_USE, name=name)
        klass = Klass(name, None)
        self.define_symbol(klass, self.scope_depth, self.ctx_scope)
        self.ctx_scope = symbols.Scope(self.ctx_scope)
        prev_class = self.ctx_class
        self.ctx_class = klass
        klass.members = self.ctx_scope.symbols
        # Will resolve class in two loops:
        # 1. Get all instance variables
        # 2. Analyze all functions declarations
        # This allows forward references inside a class
        declarations = node.body.children
        for declaration in declarations:
            if type(declaration) == ast.VarDecl:
                self.visit(declaration)
        # Make a constructor out of the class instance variables
        # By copying the current members dict
        class_attrs = copy.copy(klass.members)
        klass.constructor = symbols.FunctionSymbol(
            klass.name, klass, class_attrs
        )

        for declaration in declarations:
            if type(declaration) == ast.FunctionDecl:
                self.visit(declaration)

        # Tag class fields of the class
        for symbol in klass.members.values():
            symbol.is_property = True

        node.body.symbols = self.ctx_scope
        self.ctx_scope = self.ctx_scope.enclosing_scope
        self.ctx_class = prev_class

    def visit_eu(self, node):
        if not self.ctx_class or not self.ctx_func:
            self.error(
                "a palavra reservada 'eu' só pode ser usada dentro de um método"
            )
        node.eval_type = self.ctx_class
        return symbols.VariableSymbol("eu", self.ctx_class)

    def visit_block(self, node, scope=None):
        self.scope_depth += 1
        if scope is None:
            scope = symbols.Scope(self.ctx_scope)
        self.ctx_scope = scope
        self.visit_children(node.children)
        node.symbols = scope
        self.ctx_scope = self.ctx_scope.enclosing_scope
        self.scope_depth -= 1

    def visit_param(self, node):
        name = node.name.lexeme
        var_type = self.get_type(node.param_type)
        return symbols.VariableSymbol(name, var_type)

    def visit_fmtstr(self, node):
        txt_type = self.global_scope.resolve("texto")
        node.eval_type = txt_type
        for part in node.parts:
            self.visit(part)
            expr_type = part.eval_type
            if not expr_type.check_cast(txt_type):
                self.ctx_node = node
                self.error(
                    f"Funções invocadas dentro de expressões em fstrings devem retornar valores coercíveis para o tipo 'texto'"
                )

    # TODO: Rename this to literal
    def visit_constant(self, node):
        constant = node.token.token
        scope = self.ctx_scope
        if constant == TT.INTEGER:
            node.eval_type = scope.resolve("int")
        elif constant == TT.REAL:
            node.eval_type = scope.resolve("real")
        elif constant == TT.STRING:
            node.eval_type = scope.resolve("texto")
        elif constant in (TT.VERDADEIRO, TT.FALSO):
            node.eval_type = scope.resolve("bool")
        elif constant == TT.NULO:
            node.eval_type = scope.resolve("nulo")

    def visit_listliteral(self, node):
        elements = node.elements
        list_type = self.get_type(node.list_type)
        node.eval_type = Vector(list_type)
        if len(elements) == 0:
            return
        for i, element in enumerate(elements):
            self.visit(element)
            element_type = element.eval_type
            if not self.types_match(list_type, element_type):
                self.error(
                    f"O tipo do elemento {i} da lista não condiz com o tipo da lista. Esperava elemento do tipo '{list_type}', encontrou elemento do tipo '{element_type}'"
                )
            element.prom_type = element_type.promote_to(list_type)

    # TODO: Rename this to 'name' or 'identifier'
    def visit_variable(self, node):
        name = node.token.lexeme
        sym = self.ctx_scope.resolve(name)
        if not sym:
            self.error(f"o identificador '{name}' não foi declarado")
        elif not sym.can_evaluate():
            self.error(self.INVALID_REF, name=name)
        node.eval_type = sym.type
        node.var_symbol = sym
        assert node.var_symbol
        return sym

    # This function is everywhere because
    # there needs to be a way to check for
    # things that you can't evaluate (functions and other stuff).
    # TODO: Find a better way to find this.
    def validate_get(self, node, sym):
        if isinstance(node, ast.Get) and not sym.can_evaluate():
            self.error(self.INVALID_REF, name=sym.name)

    def visit_get(self, node):
        target = node.target
        self.visit(target)
        if target.eval_type.kind != Kind.TKLASS:
            self.error("Tipos primitivos não possuem atributos")
        # Get the class symbol
        # This hack is for objects that can be created via a literal
        obj_type = target.eval_type
        # check if member exists
        member = node.member.lexeme
        member_obj = obj_type.members.get(member)
        if not member_obj:
            self.error(
                f"O objecto do tipo '{obj_type.name}' não possui o atributo {member}"
            )
        node.eval_type = member_obj.type
        return member_obj

    def visit_set(self, node):
        target = node.target
        expr = node.expr
        # evaluate sides
        ts = self.visit(target)
        es = self.visit(expr)
        # Check both sides for get expression
        self.validate_get(target, ts)
        self.validate_get(expr, es)
        expr.prom_type = expr.eval_type.promote_to(target.eval_type)
        if target.eval_type != expr.eval_type and not expr.prom_type:
            self.ctx_node = node
            self.error(
                f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{target.eval_type.name}' e '{expr.eval_type.name}'"
            )
        node.eval_type = target.eval_type

    def visit_indexget(self, node):
        # Check if index is int
        target = node.target
        self.visit(target)
        t_type = target.eval_type

        index = node.index
        self.visit(index)

        str_or_list = (Kind.TVEC, Kind.TTEXTO)
        if t_type.kind in str_or_list and index.eval_type.kind != Kind.TINT:
            self.error(
                f"Índices para valores do tipo '{t_type}' devem ser inteiros"
            )

        if t_type.kind not in str_or_list:
            self.error(f"O valor do tipo '{t_type}' não contém índices")

        if t_type.kind == Kind.TVEC:
            node.eval_type = t_type.element_type
        elif t_type.kind == Kind.TTEXTO:
            node.eval_type = t_type
        else:
            raise NotImplementedError(
                f"Index eval not implemented for '{t_type}'"
            )

    def visit_indexset(self, node):
        index = node.index
        value = node.value
        self.visit(index)
        if index.eval_type.kind == Kind.TTEXTO:
            self.error(
                f"As strings não podem ser modificadas por meio de índices"
            )
        self.visit(value)
        if not self.types_match(index.eval_type, value.eval_type):
            self.ctx_node = node
            self.error(
                f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{lhs.eval_type}' e '{rhs.eval_type}'"
            )
        node.eval_type = index.eval_type

    def visit_converta(self, node):
        self.visit(node.target)
        t_type = node.target.eval_type
        new_type = self.get_type(node.new_type)
        err_msg = f"Não pode converter um valor do tipo '{t_type}' para o tipo '{new_type}'"
        if not t_type.check_cast(new_type):
            self.error(err_msg)
        node.eval_type = new_type

    def visit_binop(self, node):
        ls = self.visit(node.left)
        rs = self.visit(node.right)
        lhs = node.left
        rhs = node.right
        # Validate in case of get nodes
        self.validate_get(lhs, ls)
        self.validate_get(rhs, rs)
        # Evaluate type of binary
        # arithmetic operation
        operator = node.token
        result = self.get_binop_result(
            lhs.eval_type, operator.token, rhs.eval_type
        )
        if not result:
            self.ctx_node = node
            self.error(
                f"os tipos '{lhs.eval_type}' e '{rhs.eval_type}' não suportam operações com o operador '{operator.lexeme}'"
            )
        node.eval_type = result
        lhs.prom_type = lhs.eval_type.promote_to(rhs.eval_type)
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type)

    def get_binop_result(self, lhs_type, op, rhs_type):
        # Get result type of a binary operation based on
        # on operator and operand type
        scope = self.ctx_scope
        if not lhs_type.is_operable() or not rhs_type.is_operable():
            return None

        if op in (
            TT.PLUS,
            TT.MINUS,
            TT.STAR,
            TT.SLASH,
            TT.DOUBLESLASH,
            TT.MODULO,
        ):
            if lhs_type.is_numeric() and rhs_type.is_numeric():
                return (
                    scope.resolve("int")
                    if lhs_type.kind == Kind.TINT
                    and rhs_type.kind == Kind.TINT
                    and op != TT.SLASH
                    else scope.resolve("real")
                )

        elif op in (TT.GREATER, TT.LESS, TT.GREATEREQ, TT.LESSEQ):
            if lhs_type.is_numeric() and rhs_type.is_numeric():
                return scope.resolve("bool")

        elif op in (TT.DOUBLEEQUAL, TT.NOTEQUAL):
            if (
                (lhs_type.is_numeric() and rhs_type.is_numeric())
                or lhs_type == rhs_type
                or lhs_type.promote_to(rhs_type) != None
                or rhs_type.promote_to(lhs_type) != None
            ):
                return scope.resolve("bool")

        elif op in (TT.E, TT.OU):
            if lhs_type.kind == Kind.TBOOL and rhs_type.kind == Kind.TBOOL:
                return scope.resolve("bool")

        return None

    def visit_unaryop(self, node):
        operand = self.visit(node.operand)
        # Check if operand is a get node that can not be evaluated
        self.validate_get(node.operand, operand)
        operator = node.token.token
        lexeme = node.token.lexeme
        op_type = node.operand.eval_type
        bad_uop = f"o operador unário {lexeme} não pode ser usado com o tipo '{op_type}' "
        if operator in (TT.PLUS, TT.MINUS):
            if op_type.kind != Kind.TINT and op_type.kind != Kind.TREAL:
                self.ctx_node = node
                self.error(bad_uop)
        elif operator == TT.NAO:
            if op_type.kind != Kind.TBOOL:
                self.error(bad_uop)
        node.eval_type = op_type

    def visit_assign(self, node):
        lhs = node.left
        rhs = node.right
        rs = self.visit(rhs)
        # Check rhs of assignment
        # is expression
        self.validate_get(rhs, rs)
        self.visit(lhs)
        # Set node types
        node.eval_type = lhs.eval_type
        node.prom_type = None
        # Set promotion type for right side
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type)
        if not self.types_match(lhs.eval_type, rhs.eval_type):
            self.ctx_node = node
            self.error(
                f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{lhs.eval_type}' e '{rhs.eval_type}'"
            )

    def visit_mostra(self, node):
        sym = self.visit(node.exp)
        # Check if it is trying to reference method
        self.validate_get(node.exp, sym)

    def visit_loopctlstmt(self, node):
        token = node.token
        if not self.in_loop:
            self.ctx_node = node
            self.error(
                f"A directiva '{token.lexeme}' só pode ser usada dentro de uma estrutura de repetição"
            )

    def visit_retorna(self, node):
        if not self.ctx_func:
            self.ctx_node = node
            self.error(
                f"A directiva 'retorna' só pode ser usada dentro de uma função"
            )
        func_type = self.ctx_func.type
        expr = node.exp
        if self.ctx_func.type.kind == Kind.TVAZIO and expr != None:
            self.error("Não pode retornar um valor de uma função vazia")
        elif self.ctx_func.type.kind != Kind.TVAZIO and expr is None:
            self.error(
                "A instrução de retorno vazia só pode ser usada dentro de uma função vazia"
            )

        # Empty return statement, can exit early
        if not expr:
            return
        self.visit(expr)
        expr.prom_type = expr.eval_type.promote_to(func_type)
        if not self.types_match(func_type, expr.eval_type):
            self.error(
                f"expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função"
            )

    def visit_senaose(self, node):
        self.visit(node.condition)
        if node.condition.eval_type.kind != Kind.TBOOL:
            self.error(
                f"a condição da instrução 'senaose' deve ser um valor lógico"
            )
        self.visit(node.then_branch)

    def visit_se(self, node):
        self.visit(node.condition)
        if node.condition.eval_type.kind != Kind.TBOOL:
            self.error(f"a condição da instrução 'se' deve ser um valor lógico")
        self.visit(node.then_branch)
        elsif_branches = node.elsif_branches
        for branch in elsif_branches:
            self.visit(branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_escolha(self, node):
        expr = node.expression
        self.visit(expr)
        expr_type = expr.eval_type
        if expr_type.kind not in (Kind.TINT, Kind.TTEXTO):
            self.error(
                f"A directiva escolha só pode ser usada para avaliar números inteiros e strings"
            )
        for case in node.cases:
            case_expr = case.expression
            self.visit(case_expr)
            if not self.types_match(expr_type, case_expr.eval_type):
                self.error(
                    f"O tipo do valor do caso ({case_expr.eval_type}) deve ser igual ao tipo do valor que está a ser avaliado ({expr_type})"
                )
            self.visit(case.block)
        default_case = node.default_case
        if default_case:
            self.visit(default_case)

    def visit_enquanto(self, node):
        self.visit(node.condition)
        if node.condition.eval_type.kind != Kind.TBOOL:
            self.ctx_node = node
            self.error(
                f"a condição da instrução 'enquanto' deve ser um valor lógico"
            )

        in_loop_state = self.in_loop
        self.in_loop = True

        self.visit(node.statement)

        self.in_loop = in_loop_state

    # TODO: Figure out what to do with this guy
    def visit_para(self, node):
        self.visit(node.expression)
        # Define control variable for loop
        name = node.expression.name.lexeme
        sym = symbols.VariableSymbol(name, self.ctx_scope.resolve("int"))
        scope = symbols.Scope(self.ctx_scope)
        self.define_symbol(sym, self.scope_depth + 1, scope)
        self.visit(node.statement, scope)

    def visit_paraexpr(self, node):
        # self.visit(node.name)
        self.visit(node.range_expr)

    def visit_rangeexpr(self, node):
        self.visit(node.start)
        self.visit(node.end)
        if node.inc is not None:
            self.visit(node.inc)
        else:
            # If node has no inc, inc defaults to 1
            node.inc = ast.Constant(
                Token(
                    TT.INTEGER,
                    lexeme="1",
                    line=node.token.line,
                    col=node.token.col,
                )
            )
            self.visit(node.inc)
        for node in (node.start, node.end, node.inc):
            # Skip inc node in case it's empty lool
            if not node:
                continue
            if node.eval_type.kind != Kind.TINT:
                self.error("os parâmetros de uma série devem ser do tipo 'int'")

    def visit_call(self, node):
        callee = node.callee
        calle_type = type(callee)
        if calle_type == ast.Variable:
            name = callee.token.lexeme
            sym = self.ctx_scope.resolve(name)
            if not sym:
                # TODO: Use the default error message for this
                self.error(
                    f"o identificador '{name}' não foi definido neste escopo"
                )
        elif calle_type == ast.Get:
            sym = self.visit(callee)
        else:
            message = (
                f"Não pode invocar o resultado de uma invocação"
                if calle_type == ast.Call
                else f"o símbolo '{node.callee.token.lexeme}' não é invocável"
            )
            self.error(message)
        if sym.name in BUILTINS:
            self.builtin_call(BUILTINS[sym.name], node)
        else:
            self.validate_call(sym, node.fargs)
            node.eval_type = sym.type
        node.symbol = sym
        return sym

    def check_vec_op(self, fn, node):
        self.check_arity(node.fargs, fn, 2)
        vec_expr = node.fargs[0]
        value = node.fargs[1]
        self.visit(vec_expr)
        self.visit(value)

        vec_t = vec_expr.eval_type
        if vec_t.kind != Kind.TVEC:
            self.error(f"O argumento 1 da função '{fn}' deve ser um vector")

    # Validates call to builtin functions
    def builtin_call(self, fn, node):
        # TODO: Change this into an actual ast node cause it uses
        # special syntax
        if fn == BuiltinFn.VEC:
            # TODO: When vargs are implemented, make sure to
            # come here and change the way this node works
            assert (
                len(node.fargs) < 256
            ), "Builtin call exceeded max number of args"
            if len(node.fargs) < 2:
                self.error(
                    f"Função 'vec' deve ser invocada com pelo menos 2 argumentos"
                )
            # Is size given valid?
            for arg in node.fargs[1:]:
                self.visit(arg)
                if arg.eval_type.kind != Kind.TINT:
                    self.error(
                        "Os tamanhos de um vector devem ser representado por inteiros"
                    )

            type_node = node.fargs[0]
            el_type = self.get_type(type_node)  # Attempt to get type
            # Is arg 1 a vector type?
            if type(el_type) == Vector:
                self.error(f"O tipo de um vector deve ser um tipo simples")
            # Set type based on dimensions
            vec_type = Vector(el_type)
            for i in range(len(node.fargs[1:]) - 1):
                vec_type = Vector(vec_type)
            node.eval_type = vec_type
        elif fn == BuiltinFn.ANEXA:
            vec_expr = node.fargs[0]
            value = node.fargs[1]
            self.check_vec_op(fn, node)

            vec_t = vec_expr.eval_type
            el_type = vec_t.element_type
            val_t = value.eval_type
            if not self.types_match(el_type, val_t):
                self.error(
                    f"incompatibilidade de tipos entre o tipo dos elementos da lista e o valor a anexar: '{el_type}' != '{val_t}'"
                )
            value.prom_type = val_t.promote_to(el_type)
            node.eval_type = self.global_scope.resolve("vazio")
        elif fn == BuiltinFn.REMOVA:
            vec_expr = node.fargs[0]
            index = node.fargs[1]
            self.check_vec_op(fn, node)
            if index.eval_type.kind != Kind.TINT:
                self.error(
                    "O argumento 2 da função 'remova' deve ser um número inteiro"
                )
            node.eval_type = vec_expr.eval_type.element_type

        elif fn == BuiltinFn.TAM:
            self.check_arity(node.fargs, fn, 1)
            seq = node.fargs[0]
            self.visit(seq)

            SEQ_TYPES = (Kind.TTEXTO, Kind.TVEC)
            if seq.eval_type.kind not in SEQ_TYPES:
                self.error(
                    "O argumento 1 da função 'tam' deve ser do tipo 'texto' ou do tipo 'vector'"
                )

            node.eval_type = self.global_scope.resolve("int")
            # TODO: Fix this awful hack
            node.symbol = self.global_scope.resolve("tam")
        else:
            raise NotImplementedError(
                f"Code for the builtin '{fn}' has not been implemented"
            )

    def check_arity(self, fargs, name, param_len):
        arg_len = len(fargs)
        if arg_len != param_len:
            self.error(
                f"número incorrecto de argumentos para a função {name}. Esperava {param_len} argumento(s), porém recebeu {arg_len}"
            )

    def validate_call(self, sym, fargs):
        name = sym.name
        if not sym.is_callable():
            self.error(f"identificador '{name}' não é invocável")
        for arg in fargs:
            self.visit(arg)
        self.check_arity(fargs, name, sym.arity())
        # Type promotion for parameter
        for arg, param in zip(fargs, sym.params.values()):
            arg.prom_type = arg.eval_type.promote_to(param.type)
            if not self.types_match(param.type, arg.eval_type):
                self.error(
                    f"argumento inválido. Esperava-se um argumento do tipo '{param.type}' mas recebeu o tipo '{arg.eval_type}'"
                )
