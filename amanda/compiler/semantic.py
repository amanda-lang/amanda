import keyword
from os import path
from typing import Iterable, NoReturn, Optional, List, cast, Tuple
from amanda.compiler.module import Module
from amanda.compiler.parse import parse
from amanda.compiler.symbols.base import TypeVar, Typed
from amanda.compiler.tokens import TokenType as TT, Token
import amanda.compiler.ast as ast
import amanda.compiler.symbols.core as symbols
from amanda.compiler.types.builtins import (
    SrcBuiltins,
    builtin_types,
    Builtins,
    builtin_module,
)
from amanda.compiler.types.core import (
    ModuleTy,
    Primitive,
    Type,
    Types,
    Vector,
    Registo,
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

    def __init__(self, filename: str, import_paths: list[str], module: Module):
        # Relative path to the file being run
        self.filename = filename
        # Dirs to be used when resolving relative imports
        self.import_paths = [STD_LIB, *import_paths]
        # Just to have quick access to things like types and e.t.c
        self.global_scope: symbols.Scope = symbols.Scope()
        self.scope_depth = 0
        self.ctx_scope: symbols.Scope = self.global_scope
        self.ctx_node: Optional[ast.ASTNode] = None
        self.ctx_reg = None
        self.ctx_func = None
        self.in_loop = False
        self.imports = {}
        # Module currently being executed
        self.ctx_module: Module = module
        # Scope used primarily to store generic types
        self.ty_ctx: symbols.Scope = symbols.Scope()

        # Initialize builtin types
        for type_id, sym in builtin_types:
            self.global_scope.define(type_id, sym)

        # Validate dirs
        for dir_path in self.import_paths:
            assert path.isdir(
                dir_path
            ), f"Invalid import path provided:  '{dir_path}'"

        # Load builtin module
        self.load_module(builtin_module, ast.UsaMode.Global)
        SrcBuiltins.init_embutidos(self.global_scope)

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

    def error(self, code, **kwargs) -> NoReturn:
        message = code.format(**kwargs)
        raise AmandaError.common_error(
            self.ctx_module.fpath, message, self.ctx_node.token.line
        )

    def error_with_loc(self, loc_tok: Token, code, **kwargs) -> NoReturn:
        message = code.format(**kwargs)
        raise AmandaError.common_error(
            self.ctx_module.fpath, message, loc_tok.line
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

    def get_type_sym_or_err(self, type_id: str) -> Type:
        type_symbol = self.ctx_scope.resolve(type_id)
        # Attempt to get from ty_ctx
        if not type_symbol:
            type_symbol = self.ty_ctx.resolve(type_id)

        if not type_symbol or not type_symbol.is_type():
            self.error(f"o tipo '{type_id}' não foi declarado")
        return type_symbol  # type: ignore

    def get_type_variable(self, ty_node: ast.Variable) -> Type:
        type_id = ty_node.token.lexeme
        type_symbol = self.get_type_sym_or_err(type_id)
        return cast(Type, type_symbol)

    def get_generic_args(
        self, args: Iterable[tuple[TypeVar, ast.GenericArg]]
    ) -> dict[str, Type]:
        return {t_var.name: self.get_type(t_arg.arg) for t_var, t_arg in args}

    def get_mod_or_err(self, scope: symbols.Scope, mod_id: str) -> ModuleTy:
        mod = scope.resolve_typed(mod_id)
        if not mod or not isinstance(mod.type, ModuleTy):
            self.error(
                f"Especificação de tipo inválida. O identificador '{mod_id}' não foi reconhecido como um módulo"
            )
        return mod.type

    def construct_ty(self, type_node: ast.Type, type_symbol: Type) -> Type:
        if type_node.maybe_ty:
            return SrcBuiltins.Opcao.bind(T=type_symbol)
        if type_node.generic_args and len(type_node.generic_args):
            generic_args = type_node.generic_args
            # Sort out generics
            if not type_symbol.is_generic():
                self.error(
                    f"O tipo '{type_symbol}' não espera receber nenhum argumento de tipo genérico."
                )
            reg = cast(Registo, type_symbol)
            if len(reg.ty_params) != len(generic_args):
                self.error(
                    f"O tipo '{type_symbol}' esperava receber {len(reg.ty_params)} argumento de tipo, mas recebeu {len(generic_args)}"
                )
            generic_args = self.get_generic_args(
                zip(reg.ty_params, generic_args)
            )
            # If all type arguments are type vars, return the generic type.
            if all(
                map(
                    lambda x: isinstance(x, TypeVar),
                    generic_args.values(),
                )
            ):
                return reg
            return reg.bind(**generic_args)
        return cast(Type, type_symbol)

    def get_type(self, type_node: ast.Type) -> Type:
        if not type_node:
            return cast(Type, self.ctx_scope.resolve("vazio"))
        match type_node:
            case ast.Variable():
                return self.get_type_variable(type_node)  # type: ignore
            case ast.ArrayType():
                vec_ty = Vector(
                    self.ctx_module, self.get_type(type_node.element_type)
                )
                return (
                    SrcBuiltins.Opcao.bind(T=vec_ty)
                    if type_node.maybe_ty
                    else vec_ty
                )
            case ast.TypePath(components=components):
                head = components[0]
                mod = self.get_mod_or_err(self.ctx_scope, head)
                for component in components[1:-1]:
                    mod = self.get_mod_or_err(mod.get_symbols(), component)

                ty_id = components[-1]
                sym = mod.get_property(ty_id)
                if not isinstance(sym, Type):
                    self.error(
                        f"O módulo '{mod.module.fpath}' não possui o tipo '{ty_id}'"
                    )
                return self.construct_ty(type_node, sym)
            case ast.Type():
                type_id = type_node.name.lexeme
                type_symbol = self.get_type_sym_or_err(type_id)
                return self.construct_ty(type_node, type_symbol)
            case _:
                raise NotImplementedError("Unknown type node.")

    def types_match(self, expected: Type, received: Type):
        return expected == received or received.promote_to(expected)

    def enter_scope(self, scope: Optional[symbols.Scope] = None):
        self.scope_depth += 1
        if not scope:
            scope = symbols.Scope(self.ctx_scope)
        self.ctx_scope = scope

    def enter_ty_ctx(self, scope: symbols.Scope):
        self.ty_ctx = scope

    def leave_scope(self):
        self.ctx_scope = cast(symbols.Scope, self.ctx_scope).enclosing_scope
        self.scope_depth -= 1

    def leave_ty_ctx(self):
        self.ty_ctx = self.ty_ctx.enclosing_scope

    # Visitor methods
    def visit(self, node: ast.ASTNode, args=None):
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

    def validate_builtin_module(self, annotations: list[ast.Annotation]):
        builtin_annotation = list(
            filter(lambda s: s.name == "embutido", annotations)
        )
        if not builtin_annotation:
            return
        if path.dirname(self.ctx_module.fpath) != STD_LIB:
            self.error_with_loc(
                builtin_annotation[0].location_tok,
                "Anotação inválida. Apenas módulos nativos podem conter a anotação 'embutido'",
            )
        self.ctx_module.builtin = True

    def visit_module(self, node: ast.Module) -> tuple[Module, dict]:
        self.validate_builtin_module(node.annotations)
        # Since each function has it's own local scope,
        # The top level global scope will have it's own "locals"
        self.visit_children(node.children)
        node.symbols = self.global_scope
        transformed = transform(node, self.ctx_module)
        self.ctx_module.ast = transformed

        return self.ctx_module, self.imports

    def load_module_scoped(self, module: Module) -> tuple[Module, dict]:
        analyzer = Analyzer(module.fpath, self.import_paths, module)
        analyzer.imports = self.imports
        return analyzer.visit_module(parse(module.fpath))

    def define_module_alias(self, module: Module, alias: str):
        if not alias:
            raise TypeError("Arg 'alias' should not be None")
        self.assert_can_use_ident(self.ctx_node, alias)
        self.global_scope.define(
            alias,
            symbols.VariableSymbol(
                alias,
                ModuleTy(module=module, importing_mod=self.ctx_module),
                module,
            ),
        )

    def define_module_items(
        self, *, imported_mod: Module, prev_module: Module, usa_items: list[str]
    ):
        if not usa_items:
            raise TypeError("Arg 'usa_items' should not be None")
        mod_symtab: symbols.Scope = imported_mod.ast.symbols
        for item in usa_items:
            sym = mod_symtab.resolve(item)
            if not sym:
                self.ctx_module = prev_module
                self.error(
                    f"Erro ao importar módulo. O item '{item}' não foi declarado no módulo '{imported_mod.fpath}'"
                )
            self.ctx_module = prev_module
            self.assert_can_use_ident(self.ctx_node, item)
            self.global_scope.define(item, sym)

    def load_module(
        self,
        module: Module,
        mode: ast.UsaMode,
        *,
        alias: str | None = None,
        usa_items: list[str] | None = None,
    ):
        existing_mod = self.imports.get(module.fpath)
        # Module has already been loaded
        if existing_mod and existing_mod.loaded:
            match mode:
                case ast.UsaMode.Scoped:
                    self.define_module_alias(module, alias)
                case ast.UsaMode.Item:
                    self.define_module_items(
                        imported_mod=existing_mod,
                        prev_module=self.ctx_module,
                        usa_items=usa_items,
                    )

        # Check for a cycle
        # A cycle occurs when a previously seen module
        # is seen again, but it is not loaded yet
        if existing_mod and not existing_mod.loaded:
            self.error(
                f"Erro ao importar o módulo '{module.fpath}'. Inclusão cíclica detectada"
            )

        prev_module = self.ctx_module
        self.ctx_module = module
        self.imports[module.fpath] = module
        # TODO: Handle errors while loading another module
        match mode:
            case ast.UsaMode.Global:
                self.visit_module(parse(module.fpath))
            case ast.UsaMode.Scoped:
                if not alias:
                    raise TypeError("Arg 'alias' should not be None")
                self.load_module_scoped(module)
                self.define_module_alias(module, alias)

            case ast.UsaMode.Item:
                if not usa_items:
                    raise TypeError("Arg 'usa_items' should not be None")
                imported_mod, _ = self.load_module_scoped(module)
                self.define_module_items(
                    imported_mod=imported_mod,
                    prev_module=prev_module,
                    usa_items=usa_items,
                )

        module.loaded = True
        self.ctx_module = prev_module

    def resolve_import(self, fpath: str) -> str | None:
        # Try to resolve path using cwd
        if path.isfile(fpath):
            return path.abspath(fpath)
        # Attempt to resolve using the import_paths
        for dir_path in self.import_paths:
            mod_path = path.join(dir_path, fpath)
            if path.isfile(path.join(dir_path, fpath)):
                return path.abspath(mod_path)
        return None

    def visit_usa(self, node: ast.Usa):
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

        mod_path = self.resolve_import(fpath)
        if not mod_path:
            self.error(err_msg)

        module = Module(mod_path)
        self.load_module(
            module,
            node.usa_mode,
            alias=node.alias.lexeme if node.alias else None,
            usa_items=node.items,
        )

    def assert_can_use_ident(self, node: ast.ASTNode, name: str):
        in_use = self.ctx_scope.get(name)
        if in_use and not self.ctx_reg:
            self.error(self.ID_IN_USE, name=name)
        elif in_use and self.ctx_reg:
            self.ctx_node = node
            self.error(f"O atributo '{name}' já foi declarado neste registo")

    def visit_vardecl(self, node: ast.VarDecl):
        name = node.name.lexeme
        self.assert_can_use_ident(node, name)
        var_type = self.get_type(node.var_type)
        symbol = symbols.VariableSymbol(name, var_type, self.ctx_module)
        self.define_symbol(symbol, self.scope_depth, self.ctx_scope)
        node.var_type = var_type  # type: ignore
        assign = node.assign
        if not assign:
            # If we are not analyzing a registo declaration, all non primitive types must be initialized
            if self.ctx_reg is None and not var_type.zero_initialized:
                self.error(
                    "Erro de inicialização. Variáveis de tipos não primitivos devem ser inicializadas"
                )
        else:
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
    ) -> tuple[symbols.Scope, dict[str, symbols.VariableSymbol]]:
        function_type = self.get_type(node.func_type)
        if node.of_type(ast.MethodDecl):
            symbol.is_property = True
        symbol.is_global = True
        self.define_symbol(symbol, self.scope_depth, self.ctx_scope)
        scope, params = self.define_func_scope(name, node.params)
        symbol.params = params
        return (scope, params)

    def validate_return(
        self, node: ast.FunctionDecl, function_type: Type, no_return_err: str
    ):
        # Check if non void function has return
        has_return = self.has_return(node.block)
        if not has_return and function_type != Builtins.Vazio:
            self.ctx_node = node
            self.error(no_return_err)

    def check_function_body(
        self,
        node: ast.FunctionDecl,
        symbol: symbols.FunctionSymbol,
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
        symbol = symbols.FunctionSymbol(
            name, function_type, module=self.ctx_module
        )
        symbol.set_annotations(node.annotations)
        scope, _ = self.make_func_symbol(name, node, symbol)
        # Native functions don't have a body, so there's nothing to visit
        node.symbol = symbol
        if symbol.is_builtin():
            return
        if node.is_native:
            return
        self.validate_return(
            node,
            function_type,
            f"a função '{name}' não possui a instrução 'retorna'",
        )

        self.check_function_body(node, symbol, scope)

    def define_func_scope(self, name: str, params: list[ast.Param]):
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
        # TODO: Remove hack of pushing generic scope onto the scope stack!
        # Create generic scope if needed
        generic_params = self.get_generic_params(node)
        ty_ctx = self.get_generic_ty_ctx(generic_params)
        self.enter_ty_ctx(ty_ctx)

        # Checking target type
        target_ty = self.get_type(node.target_ty)
        method_name = node.name.lexeme
        method_id = target_ty.full_field_path(method_name)
        method_desc = f"O método '{method_name}' do tipo '{target_ty}'"

        # Check if field exists on target type
        method_sym = target_ty.get_property(method_name)
        if method_sym:
            self.error(
                f"{method_desc} já foi declarado anteriormente"
                if method_sym.is_callable()
                else f"A propriedade '{method_name}' já foi definida no tipo '{target_ty}'"
            )

        self.validate_decl_in_scope(
            method_id,
            f"Métodos só podem ser declarados no escopo global",
            f"{method_desc} já foi declarado anteriormente",
        )
        # Checking return type
        return_ty = self.get_type(node.return_ty)
        symbol = symbols.MethodSym(
            method_name,
            target_ty=target_ty,
            return_ty=return_ty,
            module=self.ctx_module,
        )
        symbol.set_annotations(node.annotations)

        scope, params = self.make_func_symbol(method_id, node, symbol)
        symbol.params = params

        # add alvo param
        self.define_symbol(
            symbols.VariableSymbol("alvo", target_ty, self.ctx_module),
            self.scope_depth + 1,
            scope,
        )
        for param in generic_params:
            scope.define(
                param.name,
                param,
            )
        # Body of builtin methods are not checked
        if not symbol.is_builtin():
            self.validate_return(
                node,
                return_ty,
                f"{method_desc} não possui a instrução 'retorna'",
            )
            self.check_function_body(node, symbol, scope)
        # TODO: Refactor method definitions to not rely on the underlying type
        node.symbol = symbol
        target_ty.define_method(symbol)
        self.leave_ty_ctx()

    def get_generic_params(
        self, node: ast.Registo | ast.MethodDecl
    ) -> set[TypeVar]:
        # TODO: Notify in case of duplicate generic param
        # TODO: Make sure to throw an error for unused generic params
        return (
            set(
                map(
                    lambda t: TypeVar(t.name.lexeme, self.ctx_module),
                    node.generic_params,
                )
            )
            if node.generic_params
            else set()
        )

    def get_generic_ty_ctx(self, params: set[TypeVar]) -> symbols.Scope:
        ctx = symbols.Scope(self.ty_ctx)
        for param in params:
            ctx.define(param.name, param)
        return ctx

    def visit_registo(self, node: ast.Registo):
        name = node.name.lexeme
        reg_scope = symbols.Scope(self.ctx_scope)
        if cast(symbols.Scope, self.ctx_scope).get(name):
            self.error(self.ID_IN_USE, name=name)

        generic_params = self.get_generic_params(node)
        self.enter_ty_ctx(self.get_generic_ty_ctx(generic_params))

        registo = Registo(
            name,
            self.ctx_module,
            cast(dict[str, symbols.VariableSymbol], reg_scope.symbols),
            ty_params=generic_params,
        )
        self.define_symbol(registo, self.scope_depth, self.ctx_scope)
        self.ctx_reg = registo
        self.enter_scope(reg_scope)

        for field in node.fields:
            self.visit_vardecl(field)

        for symbol in cast(symbols.Scope, self.ctx_scope).symbols.values():
            symbol.is_property = True

        self.leave_scope()
        self.define_symbol(registo, self.scope_depth, self.ctx_scope)
        self.leave_ty_ctx()
        self.ctx_reg = None

    def visit_alvo(self, node: ast.Alvo):
        if type(self.ctx_func) is not symbols.MethodSym:
            self.error(
                "a palavra reservada 'alvo' só pode ser usada dentro de um método"
            )
        method_sym = cast(symbols.MethodSym, self.ctx_func)

        node.eval_type = method_sym.target_ty
        symbol = symbols.VariableSymbol("alvo", node.eval_type, self.ctx_module)
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
        return symbols.VariableSymbol(name, var_type, self.ctx_module)

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
            node.eval_type = Builtins.Real
        elif constant == TT.STRING:
            node.eval_type = Builtins.Texto
        elif constant in (TT.VERDADEIRO, TT.FALSO):
            node.eval_type = Builtins.Bool
        elif constant == TT.NULO:
            node.eval_type = Builtins.Nulo

    def visit_listliteral(self, node):
        elements = node.elements
        list_type = self.get_type(node.list_type)
        node.eval_type = Vector(self.ctx_module, list_type)
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
        sym = cast(
            symbols.Typed,
            cast(symbols.Scope, self.ctx_scope).resolve_typed(name),
        )
        if not sym:
            self.error(f"o identificador '{name}' não foi declarado")
        elif not sym.can_evaluate():
            self.ctx_node = node
            self.error(self.INVALID_REF, name=name)
        node.eval_type = sym.type
        node.var_symbol = sym
        assert node.var_symbol
        return sym

    def _bad_prop_err(self, ty: Type, field: str):
        # TODO: Add context to bad prop error on Option types
        if not ty.is_primitive():
            self.error(
                f"O objecto do tipo '{ty}' não possui o atributo '{field}'"
            )
        elif isinstance(ty, ModuleTy):
            self.error(
                f"O módulo '{ty.module.fpath}' não possui o item '{field}'"
            )
        self.error(f"O tipo '{ty}' não possui o método '{field}'")

    def visit_get(self, node: ast.Get):
        target = node.target
        ty_sym = target.eval_type  # type: ignore
        self.visit(target)
        if (
            not target.eval_type.supports_fields()
            and not target.eval_type.supports_methods()
        ):
            self.error("O Tipo '{ty_sym.name}' nenhum atributo ou método")
        ty_sym = target.eval_type  # type: ignore
        field = node.member.lexeme
        field_sym = cast(Typed, ty_sym.get_property(field))

        if field_sym is None:
            self._bad_prop_err(ty_sym, field)
            return
        # TODO: Add specific node for method call
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
        node.eval_type = (
            field_sym if isinstance(field_sym, Type) else field_sym.type
        )
        return field_sym

    def visit_set(self, node):
        target = node.target
        expr = node.expr
        # evaluate sides
        self.visit(target)
        if target.target.eval_type.is_module():
            self.error(
                f"Atribuição inválida. As variáveis globais de um módulo importado não podem ser modificadas externamente"
            )
        self.visit(expr)
        expr.prom_type = expr.eval_type.promote_to(target.eval_type)
        if not self.types_match(target.eval_type, expr.eval_type):
            self.ctx_node = node
            self.error(
                f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{target.eval_type}' e '{expr.eval_type}'"
            )
        node.eval_type = target.eval_type

    def visit_indexget(self, node: ast.IndexGet):
        # Check if index is int
        target = node.target
        self.visit(target)
        t_type: Type = target.eval_type

        index = node.index
        self.visit(index)

        if not t_type.supports_index_get():
            self.error(f"O valor do tipo '{t_type}' não contém índices")

        index_ty = t_type.index_ty()
        if t_type.index_ty() != index.eval_type:
            self.error(
                f"Índices para valores do tipo '{t_type}' devem ser do tipo '{index_ty}'"
            )

        node.eval_type = t_type.index_item_ty()

    def visit_indexset(self, node):
        index = node.index
        value = node.value
        self.visit(index)
        idx_ty = index.eval_type
        if not idx_ty.supports_index_set():
            if idx_ty.tag == Types.TTEXTO:
                self.error(
                    f"As strings não podem ser modificadas por meio de índices"
                    if idx_ty.tag == Types.TTEXTO
                    else f"Itens do tipo '{idx_ty}' não podem ser modificadas por meio de índices"
                )
        self.visit(value)
        if not self.types_match(index.eval_type, value.eval_type):
            self.ctx_node = node
            self.error(
                f"Atribuição inválida. incompatibilidade entre os operandos da atribuição: '{index.eval_type}' e '{value.eval_type}'"
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

    def visit_binop(self, node: ast.BinOp):
        ls = self.visit(node.left)
        rs = self.visit(node.right)
        lhs = node.left
        rhs = node.right
        # Evaluate type of binary
        # arithmetic operation
        operator = node.token
        lhs_ty = lhs.eval_type
        rhs_ty = rhs.eval_type

        result = lhs_ty.binop(operator.token, rhs_ty)
        if not result:
            self.ctx_node = node
            self.error(
                f"os tipos '{lhs.eval_type}' e '{rhs.eval_type}' não suportam operações com o operador '{operator.lexeme}'"
            )
        node.eval_type = result
        lhs.prom_type = lhs.eval_type.promote_to(rhs.eval_type)
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type)

    def visit_unaryop(self, node: ast.UnaryOp):
        operand = self.visit(node.operand)
        # Check if operand is a get node that can not be evaluated
        operator = node.token.token
        lexeme = node.token.lexeme
        op_type = node.operand.eval_type
        bad_uop = f"o operador unário {lexeme} não pode ser usado com o tipo '{op_type}' "
        uop_result = op_type.unaryop(operator)
        if not uop_result:
            self.ctx_node = node
            self.error(bad_uop)
        node.eval_type = uop_result

    def visit_assign(self, node: ast.Assign):
        lhs = node.left
        rhs = node.right
        rs = self.visit(rhs)
        # Check rhs of assignment
        # is expression
        self.visit(lhs)
        # Set node types
        if isinstance(lhs.eval_type, ModuleTy):
            self.error(
                f"Atribuição inválida. Não pode atribuir valores a um módulo"
            )
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

    def visit_retorna(self, node: ast.Retorna):
        if not self.ctx_func:
            self.ctx_node = node
            self.error(
                f"A directiva 'retorna' só pode ser usada dentro de uma função"
            )
        func_type: Type = self.ctx_func.type
        expr = node.exp
        if func_type == Builtins.Vazio and expr != None:
            self.error("Não pode retornar um valor de uma função vazia")
        elif func_type != Builtins.Vazio and expr is None:
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

    def visit_senaose(self, node: ast.SenaoSe):
        self.visit(node.condition)
        if node.condition.eval_type != Builtins.Bool:
            self.error(
                f"a condição da instrução 'senaose' deve ser um valor lógico"
            )
        self.visit(node.then_branch)

    def visit_se(self, node: ast.Se):
        self.visit(node.condition)
        if node.condition.eval_type.tag != Types.TBOOL:
            self.error(f"a condição da instrução 'se' deve ser um valor lógico")
        self.visit(node.then_branch)
        elsif_branches = node.elsif_branches
        for branch in elsif_branches:
            self.visit(branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_escolha(self, node: ast.Escolha):
        expr = node.expression
        self.visit(expr)
        expr_type = expr.eval_type
        if expr_type.tag not in (Types.TINT, Types.TTEXTO):
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

    def visit_enquanto(self, node: ast.Enquanto):
        self.visit(node.condition)
        if node.condition.eval_type.tag != Types.TBOOL:
            self.ctx_node = node
            self.error(
                f"a condição da instrução 'enquanto' deve ser um valor lógico"
            )

        in_loop_state = self.in_loop
        self.in_loop = True

        self.visit(node.statement)

        self.in_loop = in_loop_state

    # TODO: Figure out what to do with this guy
    def visit_para(self, node: ast.Para):
        self.visit(node.expression)
        # Define control variable for loop
        name = node.expression.name.lexeme
        sym = symbols.VariableSymbol(
            name, self.ctx_scope.resolve("int"), self.ctx_module
        )
        scope = symbols.Scope(self.ctx_scope)
        self.define_symbol(sym, self.scope_depth + 1, scope)
        self.visit(node.statement, scope)

    def visit_paraexpr(self, node: ast.ParaExpr):
        # self.visit(node.name)
        self.visit(node.range_expr)

    def visit_rangeexpr(self, node: ast.RangeExpr):
        self.visit(node.start)
        self.visit(node.end)
        if node.inc is not None:
            self.visit(node.inc)
        for enode in (node.start, node.end, node.inc):
            # Skip inc node in case it's empty lool
            if not enode:
                continue
            if enode.eval_type != Builtins.Int:
                self.error("os parâmetros de uma série devem ser do tipo 'int'")

    def visit_namedarg(self, node: ast.NamedArg):
        self.visit(node.arg)
        node.eval_type = node.arg.eval_type

    def visit_call(self, node: ast.Call):
        callee = node.callee
        calle_type = type(callee)
        sym: Typed
        if calle_type == ast.Variable:
            name = callee.token.lexeme
            sym = self.ctx_scope.resolve_typed(name)
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
            return
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
        if not isinstance(vec_t, Vector):
            self.error(f"O argumento 1 da função '{fn}' deve ser um vector")

    # Validates call to builtin functions
    def builtin_call(self, fn: BuiltinFn, node: ast.Call):
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
                if arg.eval_type.tag != Types.TINT:
                    self.error(
                        "Os tamanhos de um vector devem ser representado por inteiros"
                    )

            type_node = cast(ast.Type, node.fargs[0])
            el_type = self.get_type(type_node)  # Attempt to get type
            # Is arg 1 a vector type?
            if type(el_type) == Vector:
                self.error(f"O tipo de um vector deve ser um tipo simples")
            # Set type based on dimensions
            vec_type = Vector(self.ctx_module, el_type)
            for i in range(len(node.fargs[1:]) - 1):
                vec_type = Vector(self.ctx_module, vec_type)
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
            node.eval_type = cast(Type, self.global_scope.resolve("vazio"))
        elif fn == BuiltinFn.REMOVA:
            vec_expr = node.fargs[0]
            index = node.fargs[1]
            self.check_vec_op(fn, node)
            if index.eval_type != Builtins.Int:
                self.error(
                    "O argumento 2 da função 'remova' deve ser um número inteiro"
                )
            node.eval_type = vec_expr.eval_type.element_type

        elif fn == BuiltinFn.TAM:
            self.check_arity(len(node.fargs), fn, 1, False)
            seq = node.fargs[0]
            self.visit(seq)

            if not seq.eval_type.supports_tam():
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

    def check_arity(
        self,
        arg_len: int,
        name: str,
        arity: int,
        is_method: bool,
        symbol: symbols.FunctionSymbol | None = None,
    ):
        if arg_len != arity:
            if isinstance(symbol, symbols.MethodSym):
                name = symbol.target_ty.full_field_path(symbol.name)
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
        self.check_arity(
            len(fargs), name, sym.arity(), sym.is_property, symbol=sym
        )
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
