import copy
import keyword
from os import path
from typing import Optional, List, cast, Tuple
from amanda.compiler.parse import parse
from amanda.compiler.tokens import TokenType as TT, Token
import amanda.compiler.ast as ast
import amanda.compiler.symbols as symbols
from amanda.compiler.type import (
    builtin_types,
    Kind,
    Type,
    Vector,
    Registo,
    Builtins,
)
from amanda.compiler.error import AmandaError
from amanda.compiler.builtinfn import BUILTINS, BuiltinFn
from amanda.config import STD_LIB
from amanda.compiler.transform import transform


MAX_AMA_INT = 2**63 - 1


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
        self.ctx_node: Optional[ast.ASTNode] = None
        self.ctx_reg = None
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

    # Helper methods
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
    def define_symbol(
        self, symbol: symbols.Symbol, depth: int, scope: symbols.Scope
    ):
        if not self.is_valid_name(symbol.name) or depth >= 1:
            symbol.out_id = f"_r{depth}{scope.count()}_"
        scope.define(symbol.name, symbol)

    def get_type_sym_or_err(self, type_id: str) -> symbols.Symbol:
        type_symbol = self.ctx_scope.resolve(type_id)
        if not type_symbol or not type_symbol.is_type():
            self.error(f"o tipo '{type_id}' não foi declarado")
        return type_symbol  # type: ignore

    def get_type_variable(self, ty_node: ast.Variable) -> Type:
        type_id = ty_node.token.lexeme
        type_symbol = self.get_type_sym_or_err(type_id)
        return cast(Type, type_symbol)

    def get_type(self, type_node: ast.Type) -> Type:
        if not type_node:
            return cast(Type, self.ctx_scope.resolve("vazio"))
        node_t = type(type_node)
        if node_t == ast.Variable:
            return self.get_type_variable(type_node)  # type: ignore
        elif node_t == ast.Type:
            type_id = type_node.name.lexeme
            type_symbol = self.get_type_sym_or_err(type_id)
            if type_node.maybe_ty:
                return Builtins.Talvez.value.bind(T=type_symbol)
            return cast(Type, type_symbol)
        elif type(type_node) == ast.ArrayType:
            vec_ty = Vector(self.get_type(type_node.element_type))
            return (
                Builtins.Talvez.value.bind(T=vec_ty)
                if type_node.maybe_ty
                else vec_ty
            )
        else:
            return Type(Kind.TUNKNOWN)

    def types_match(self, expected: Type, received: Type):
        return expected == received or received.promote_to(expected)

    def enter_scope(self, scope: Optional[symbols.Scope] = None):
        self.scope_depth += 1
        if not scope:
            scope = symbols.Scope(self.ctx_scope)
        self.ctx_scope = scope

    def leave_scope(self):
        self.ctx_scope = cast(symbols.Scope, self.ctx_scope).enclosing_scope
        self.scope_depth -= 1

    # Visitor methods
    def visit(self, node, args=None):
        node_class = type(node).__name__.lower()
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self, method_name, self.general_visit)
        self.ctx_node = node
        if node_class == "block":
            return visitor_method(node, args)
        return visitor_method(node)

    def visit_children(self, children):
        for child in children:
            self.visit(child)

    def visit_program(self, node):
        # Since each function has it's own local scope,
        # The top level global scope will have it's own "locals"
        self.visit_children(node.children)
        node.symbols = self.global_scope
        return transform(node)

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
        in_use = self.ctx_scope.get(name)
        if in_use and not self.ctx_reg:
            self.error(self.ID_IN_USE, name=name)
        elif in_use and self.ctx_reg:
            self.ctx_node = node
            self.error(f"O atributo '{name}' já foi declarado neste registo")
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

    def validate_decl_in_scope(
        self, name: str, local_function_err: str, id_in_use_err: str
    ):
        if self.scope_depth > 0:
            self.error(local_function_err)

        # Check if id is already in use
        if self.ctx_scope.get(name):
            self.error(id_in_use_err, name=name)

    def validate_num_params(self, node: ast.FunctionDecl):
        # Check that func is within max param number
        if len(node.params) > (2**8) - 1:
            is_method = node.of_type(ast.MethodDecl)
            err_msg = (
                "Os métodos só podem ter até 255 parâmetros"
                if is_method
                else f"As funções só podem ter até 255 parâmetros"
            )
            self.error(err_msg)

    def make_func_symbol(
        self, name: str, node: ast.FunctionDecl, symbol: symbols.FunctionSymbol
    ) -> symbols.Scope:
        function_type = self.get_type(node.func_type)
        if node.of_type(ast.MethodDecl):
            symbol.is_property = True
        symbol.is_global = True
        self.define_symbol(symbol, self.scope_depth, self.ctx_scope)
        scope, symbol.params = self.define_func_scope(name, node.params)
        return scope

    def validate_return(
        self, node: ast.FunctionDecl, function_type: Type, no_return_err: str
    ):
        # Check if non void function has return
        has_return = self.has_return(node.block)
        if not has_return and function_type.kind != Kind.TVAZIO:
            self.ctx_node = node
            self.error(no_return_err)

    def check_function_body(
        self,
        node: ast.FunctionDecl,
        symbol: symbols.Symbol,
        scope: symbols.Scope,
    ):
        prev_function = self.ctx_func
        self.ctx_func = symbol

        self.visit(node.block, scope)

        self.ctx_func = prev_function
        symbol.scope = scope
        node.symbol = symbol

    def visit_functiondecl(self, node: ast.FunctionDecl):
        name = node.name.lexeme
        self.validate_decl_in_scope(
            name,
            f"As funções só podem ser declaradas no escopo global",
            self.ID_IN_USE,
        )
        self.validate_num_params(node)

        function_type = self.get_type(node.func_type)
        symbol = symbols.FunctionSymbol(name, function_type)
        scope = self.make_func_symbol(name, node, symbol)
        # Native functions don't have a body, so there's nothing to visit
        if node.is_native:
            return

        self.validate_return(
            node,
            function_type,
            f"a função '{name}' não possui a instrução 'retorna'",
        )

        self.check_function_body(node, symbol, scope)

    def define_func_scope(self, name, params):
        params_dict = {}
        klass = self.ctx_reg
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

    def visit_methoddecl(self, node: ast.MethodDecl):
        target_ty: Registo = self.get_type(node.target_ty)
        method_name = node.name.lexeme
        method_id = target_ty.full_field_path(method_name)
        method_desc = f"O método '{method_name}' do tipo '{target_ty}'"

        # Check if field exists on target type
        if target_ty.fields.get(method_name) or target_ty.methods.get(
            method_name
        ):
            self.error(
                f"A propriedade '{method_name}' já foi definida no tipo '{target_ty}'"
            )

        self.validate_decl_in_scope(
            method_id,
            f"Métodos só podem ser declarados no escopo global",
            f"{method_desc} já foi declarado anteriormente",
        )
        return_ty = self.get_type(node.return_ty)
        symbol = symbols.MethodSym(method_id, target_ty, return_ty, node.params)
        scope = self.make_func_symbol(method_id, node, symbol)
        self.validate_return(
            node,
            return_ty,
            f"{method_desc} não possui a instrução 'retorna'",
        )
        # add alvo param
        self.define_symbol(
            symbols.Symbol("alvo", target_ty), self.scope_depth + 1, scope
        )

        self.check_function_body(node, symbol, scope)
        target_ty.methods[method_name] = symbol

    def visit_registo(self, node: ast.Registo):
        name = node.name.lexeme
        reg_scope = symbols.Scope(self.ctx_scope)
        if cast(symbols.Scope, self.ctx_scope).get(name):
            self.error(self.ID_IN_USE, name=name)

        registo = Registo(name, reg_scope.symbols)
        self.define_symbol(registo, self.scope_depth, self.ctx_scope)
        self.ctx_reg = registo
        self.enter_scope(reg_scope)

        for field in node.fields:
            self.visit_vardecl(field)

        for symbol in cast(symbols.Scope, self.ctx_scope).symbols.values():
            symbol.is_property = True

        self.leave_scope()
        self.define_symbol(registo, self.scope_depth, self.ctx_scope)
        self.ctx_reg = None

    def visit_alvo(self, node: ast.Alvo):
        if type(self.ctx_func) is not symbols.MethodSym:
            self.error(
                "a palavra reservada 'alvo' só pode ser usada dentro de um método"
            )
        method_sym = cast(symbols.MethodSym, self.ctx_func)

        node.eval_type = method_sym.target_ty
        symbol = symbols.VariableSymbol("alvo", node.eval_type)
        node.var_symbol = symbol
        return symbol

    def visit_block(self, node, scope=None):
        self.enter_scope(scope)
        self.visit_children(node.children)
        node.symbols = self.ctx_scope
        self.leave_scope()

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
    def visit_constant(self, node: ast.Constant):
        constant = node.token.token
        scope = self.ctx_scope
        if constant == TT.INTEGER:
            node.eval_type = scope.resolve("int")
            int_value = int(node.token.lexeme)
            if int_value > MAX_AMA_INT:
                self.error(
                    f"Número inteiro demasiado grande. Só pode usar números inteiros iguais ou menores que '{MAX_AMA_INT}'"
                )
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

    def visit_get(self, node: ast.Get):
        target = node.target
        self.visit(target)
        if target.eval_type.kind != Kind.TREGISTO:
            self.error("Tipos primitivos não possuem atributos")
        ty_sym: Registo = target.eval_type  # type: ignore
        field = node.member.lexeme
        field_sym = ty_sym.fields.get(field, ty_sym.methods.get(field))
        if not field_sym:
            self.error(
                f"O objecto do tipo '{ty_sym.name}' não possui o atributo {field}"
            )
        # Check if valid use of get
        # References to methods can only be used in the context of
        # a call expression
        in_eval_ctx = (
            node.child_of(ast.Expr)
            or node.child_of(ast.Set)
            or node.child_of(ast.Assign)
            or node.child_of(ast.Statement)
        )
        if (
            in_eval_ctx
            and not node.child_of(ast.Call)
            and not field_sym.can_evaluate()
        ):
            self.error(self.INVALID_REF, name=field_sym.name)
        node.eval_type = field_sym.type
        return field_sym

    def visit_set(self, node):
        target = node.target
        expr = node.expr
        # evaluate sides
        self.visit(target)
        self.visit(expr)
        expr.prom_type = expr.eval_type.promote_to(target.eval_type)
        if not self.types_match(target.eval_type, expr.eval_type):
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
                f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{index.eval_type}' e '{value.eval_type}'"
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

    def visit_assign(self, node: ast.Assign):
        lhs = node.left
        rhs = node.right
        rs = self.visit(rhs)
        # Check rhs of assignment
        # is expression
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
        for node in (node.start, node.end, node.inc):
            # Skip inc node in case it's empty lool
            if not node:
                continue
            if node.eval_type.kind != Kind.TINT:
                self.error("os parâmetros de uma série devem ser do tipo 'int'")

    def visit_namedarg(self, node: ast.NamedArg):
        self.visit(node.arg)
        node.eval_type = node.arg.eval_type

    def visit_call(self, node: ast.Call):
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
        elif isinstance(sym, Registo):
            self.validate_initializer(sym, node.fargs)
            node.eval_type = sym
        else:
            self.validate_call(cast(symbols.FunctionSymbol, sym), node.fargs)
            node.eval_type = sym.type
        node.symbol = sym
        return sym

    def check_vec_op(self, fn, node):
        self.check_arity(len(node.fargs), fn, 2, False)
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
            self.check_arity(len(node.fargs), fn, 1, False)
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

    def check_arity(self, arg_len: int, name: str, arity: int, is_method: bool):
        if arg_len != arity:
            callable_desc = (
                f"o método {name}" if is_method else f"a função {name}"
            )
            self.error(
                f"número incorrecto de argumentos para {callable_desc}. Esperava {arity} argumento(s), porém recebeu {arg_len}"
            )

    def validate_call(self, sym: symbols.FunctionSymbol, fargs: List[ast.Expr]):
        name = sym.name
        if not sym.is_callable():
            self.error(f"identificador '{name}' não é invocável")
        for arg in fargs:
            if arg.of_type(ast.NamedArg):
                self.ctx_node = arg
                self.error(
                    f"Funções e métodos não suportam argumentos nomeados"
                )
            self.visit(arg)
        self.check_arity(len(fargs), name, sym.arity(), sym.is_property)
        # Type promotion for parameter
        for arg, param in zip(fargs, sym.params.values()):
            arg.prom_type = arg.eval_type.promote_to(param.type)
            if not self.types_match(param.type, arg.eval_type):
                self.error(
                    f"argumento inválido. Esperava-se um argumento do tipo '{param.type}' mas recebeu o tipo '{arg.eval_type}'"
                )

    def validate_initializer(self, sym: Registo, fargs: List[ast.NamedArg]):
        # Check call arity

        if len(fargs) != len(sym.fields):
            self.error(
                f"número incorrecto de argumentos para o inicializador do registo '{sym.name}'. Esperava {len(sym.fields)} argumento(s), porém recebeu {len(fargs)}"
            )
        inited_args = set()
        for arg in fargs:
            self.ctx_node = arg
            # 1. All args must be named args
            if not arg.of_type(ast.NamedArg):
                self.error(
                    f"Todos os argumentos do inicializador de um registo devem ser nomeados"
                )
            arg_id = arg.name.lexeme
            self.visit(arg)
            # 2. No unknown named arg in args
            if arg_id not in sym.fields:
                self.error(
                    f"O registo '{sym.name}' não possui o atributo '{arg_id}'"
                )
            # 3. Args cannot be duplicated
            if arg_id in inited_args:
                self.error(f"O atributo '{arg_id}' já foi inicializado")
            # 4. Type of named arg must match type of the record field
            field_ty = sym.fields[arg_id].type
            arg.prom_type = arg.eval_type.promote_to(field_ty)
            if not self.types_match(field_ty, arg.eval_type):
                self.error(
                    f"argumento nomeado inválido. incompatibilidade de tipos entre o valor do argumento nomeado '{arg_id}' e o atributo do registo. '{arg.eval_type}' incompatível com '{field_ty}'"
                )
            inited_args.add(arg_id)
