from amanda.tokens import TokenType as TT
import amanda.ast as ast
import amanda.symbols as symbols
from amanda.symbols import Type,Lista
from amanda.error import AmandaError
from amanda.bltins import bltin_symbols



class Analyzer(ast.Visitor):

    #Semnatic analysis errors
    UNDEFINED_TYPE = "o tipo '{type}' não foi declarado"
    ID_IN_USE = "O identificador '{name}' já foi declarado neste escopo"
    NO_RETURN_STMT = "a função '{name}' não possui a instrução 'retorna'"
    REPEAT_PARAM = "o parâmetro '{name}' já foi especificado nesta função"
    UNDECLARED_ID ="o identificador '{name}' não foi declarado"
    INVALID_REF = "o identificador '{name}' não é uma referência válida"
    INVALID_OP = "os tipos '{t1}' e '{t2}' não suportam operações com o operador '{operator}'"
    INVALID_UOP = "o operador unário {operator} não pode ser usado com o tipo '{type}' "
    BAD_STR_OP = "o tipo 'texto' não suporta operações com o operador '{operator}'"

    #Special builtin function
    BUILTIN_OPS = (
        "lista",

    )


    def __init__(self):
        #Just to have quick access to things like types and e.t.c
        self.global_scope = symbols.Scope(symbols.Scope.GLOBAL)
        self.current_scope = self.global_scope
        self.current_node = None
        self.current_class = None
        self.current_function = None
        self.init_builtins()

    def init_builtins(self):
        #Initialize builtin types
        self.global_scope.define(Type.INT.name,Type.INT)
        self.global_scope.define(Type.REAL.name,Type.REAL)
        self.global_scope.define(Type.BOOL.name,Type.BOOL)
        self.global_scope.define(Type.TEXTO.name,Type.TEXTO)
        self.global_scope.define(Type.VAZIO.name,Type.VAZIO)
        self.global_scope.define(Type.INDEF.name,Type.INDEF)
        #load builtin symbols
        for sname,symbol in bltin_symbols.items():
            self.global_scope.define(sname,symbol)


    def has_return(self,node):
        ''' Method that checks if function non void 
        function has return statement'''
        node_class = type(node).__name__.lower()
        method_name = f"has_return_{node_class}"
        visitor_method = getattr(self,method_name,self.general_check)
        self.current_node = node
        return visitor_method(node)

    def has_return_block(self,node):
        for child in node.children:
            has_return = self.has_return(child)
            if has_return:
                return True
        return False

    def has_return_se(self,node):
        ''' Method checks for return within
            'se' statements'''
        # If there is no else branch return None immediately
        return False if not node.else_branch else self.has_return(node.else_branch)

    def has_return_enquanto(self,node):
        return self.has_return(node.statement)

    def has_return_para(self,node):
        return self.has_return(node.statement)


    def has_return_retorna(self,node):
        return True

    def general_check(self,node):
        return False

    def visit(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"visit_{node_class}"
        visitor_method = getattr(self,method_name,self.general_visit)
        self.current_node = node
        if node_class == "block":
            return visitor_method(node,args)
        return visitor_method(node)

    def general_visit(self,node):
        raise NotImplementedError(f"Have not defined method for this node type: {type(node)} {node.__dict__}")

    def error(self,code,**kwargs):
        message = code.format(**kwargs)
        raise AmandaError.common_error(
            message,self.current_node.token.line
        )

    def check_program(self,program):
        self.visit(program)
        return program

    def visit_program(self,node):
        for child in node.children:
            self.visit(child)
    
    def get_type(self,type_node):
        if not type_node:
            return Type.VAZIO
    
        if type(type_node) == ast.ArraySpec:
            type_name = type_node.decl_type.lexeme
            type_symbol = self.current_scope.resolve(type_name)
            ama_type = Lista(type_symbol)
        else:
            type_name = type_node.lexeme
            type_symbol = self.current_scope.resolve(type_name)
            ama_type = type_symbol

        if not type_symbol or not type_symbol.is_type():
            self.error(
                self.UNDEFINED_TYPE,
                type=type_name
            )

        return ama_type

    def types_match(self,expected,received):
        return expected == received or received.promote_to(expected)


    def visit_vardecl(self,node):
        klass = self.current_class
        name = node.name.lexeme
        #If declaration has already been resolved,
        #define the member in current scope and exit declaration
        #Only skip declarations in the class scope not in local
        #scope
        #REMOVE: This piece of bad code 
        if klass and klass.resolved and not \
        self.current_function:
            self.current_scope.define(name,klass.get_member(name))
            return

        if self.current_scope.get(name):
            self.error(self.ID_IN_USE,name=name)

        var_type = self.get_type(node.var_type)
        symbol = symbols.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol)
        node.var_type = var_type
        assign = node.assign
        if assign is not None:
            if assign.right.token.lexeme == name:
                self.error(f"Erro ao inicializar variável. Não pode referenciar uma variável durante a sua declaração")
            self.visit(assign)

    def visit_functiondecl(self,node):
        #Check if id is already in use
        name = node.name.lexeme
        if self.current_scope.get(name):
            self.error(self.ID_IN_USE,name=name)

        function_type = self.get_type(node.func_type)

        #Check if non void function has return
        has_return = self.has_return(node.block)
        if not has_return and function_type != Type.VAZIO:
            self.current_node = node
            self.error(self.NO_RETURN_STMT,name=name)
        symbol = symbols.FunctionSymbol(name,function_type)
        self.check_function(name,symbol,node)

    def check_super(self,name,superclass,body):
        ''' Checks if the constructor calls superclass
        constructor with arguments'''
        super_constructor = superclass.get_member("constructor")
        if not super_constructor:
            return True
        if super_constructor.arity() == 0:
            return True
        for child in body.children:
            if isinstance(child,ast.Call):
                if isinstance(child.callee,ast.Super):
                    return True
        return False

    def check_function(self,name,symbol,node):
        self.current_scope.define(name,symbol)
        #If in class and this is resolution phase,
        #do not visit body
        klass = self.current_class
        if klass and not klass.resolved:
            return
        scope,symbol.params = self.define_func_scope(name,node.params)
        prev_function = self.current_function
        self.current_function = symbol
        self.visit(node.block,scope)
        self.current_function = prev_function
        
    def define_func_scope(self,name,params):
        #TODO: Check if i can immplements params as list
        #Instead of dict
        params_dict = {}
        for param in params:
            param_name = param.name.lexeme
            if params_dict.get(param_name):
                self.error(self.REPEAT_PARAM,name=param_name)
            param_symbol = self.visit(param)
            params_dict[param_name] = param_symbol
            #Add params o current_scope
        scope = symbols.Scope(name,self.current_scope)
        for param_name,param in params_dict.items():
            scope.define(param_name,param)
        return (scope,params_dict)

    def visit_classdecl(self,node):
        name = node.name.lexeme
        if self.current_scope.get(name):
            self.error(self.ID_IN_USE,name=name)
        #Check if class has a valid superclass
        superclass = node.superclass
        if superclass:
            super_name = superclass.lexeme
            superclass = self.current_scope.resolve(super_name)
            if not superclass:
                self.error(self.UNDECLARED_ID,name=super_name)
        klass = symbols.ClassSymbol(name,superclass=superclass)
        self.current_scope.define(name,klass)
        res_scope = symbols.Scope(name,self.current_scope)
        prev_class = self.current_class
        self.current_class = klass
        #Resolve class
        klass.members = self.visit_classbody(node.body,res_scope)
        klass.resolved = True
        #Revisit class
        self.visit_classbody(node.body,symbols.Scope(name,self.current_scope))
        self.current_class = prev_class

    def visit_classbody(self,node,scope):
        self.current_scope = scope
        for child in node.children:
            self.visit(child)
        self.current_scope = self.current_scope.enclosing_scope
        return scope.symbols

    def visit_eu(self,node):
        #Validate the use of 'eu'
        if not self.current_class or not self.current_function:
            self.error("a palavra reservada 'eu' só pode ser usada dentro de um método")
        node.eval_type = self.current_class
        return symbols.VariableSymbol('eu',self.current_class)

    def visit_super(self,node):
        klass = self.current_class
        if not klass:
            self.error("a palavra reservada 'super' só pode ser usada dentro de uma classe")
        if not klass.superclass:
            self.error("Esta classe não possui uma superclasse")
        klass = klass.superclass
        node.eval_type = klass
        return symbols.VariableSymbol('super',klass)

    def visit_block(self,node,scope=None):
        if not scope:
            scope = symbols.Scope(symbols.Scope.LOCAL,self.current_scope)
        self.current_scope = scope
        for child in node.children:
            self.visit(child)
        self.current_scope = self.current_scope.enclosing_scope

    def visit_param(self,node):
        name = node.name.lexeme
        var_type = self.get_type(node.param_type)
        return symbols.VariableSymbol(name,var_type)

    def visit_constant(self,node):
        constant = node.token.token
        if constant == TT.INTEGER:
            node.eval_type = Type.INT
        elif constant == TT.REAL:
            node.eval_type = Type.REAL
        elif constant == TT.STRING:
            node.eval_type = Type.TEXTO
        elif constant in (TT.VERDADEIRO,TT.FALSO):
            node.eval_type = Type.BOOL

    def visit_variable(self,node):
        name = node.token.lexeme
        sym = self.current_scope.resolve(name)
        if not sym:
            self.error(self.UNDECLARED_ID,name=name)
        #Referencing array by name 
        #TODO: Remove this in favour of creating
        #a separate table just for the function symbols.
        elif not sym.can_evaluate():
            self.error(self.INVALID_REF,name=name)
        node.eval_type = sym.type
        return sym

    def validate_get(self,node,sym):
        ''' Method to validate get expressions'''
        if isinstance(node,ast.Get) and not sym.can_evaluate():
            self.error(self.INVALID_REF,name=sym.name)

    def visit_get(self,node):
        ''' Method that processes getter expressions.
        Returns the resolved symbol of the get expression.'''
        target = self.visit(node.target)
        #Check for literal that are converted to object
        if node.target.eval_type != Type.REF:
            self.error("Tipos primitivos não possuem atributos")
        #Get the class symbol
        #This hack is for objects that can be created via a literal
        obj_type = target.type if target else node.target.eval_type
        #check if member exists
        member = node.member.lexeme
        member_obj = obj_type.resolve_member(member)
        if not member_obj:
            self.error(f"O objecto do tipo '{obj_type.name}' não possui o atributo {member}")
        if member_obj.name == "constructor":
            self.error(f"constructor de uma classe não pode ser invocado a partir de um objecto")
        node.eval_type = member_obj.type
        return member_obj

    def visit_set(self,node):
        ''' Method that processes setter expressions.
        Returns the resolved symbol of the set expression.'''
        target = node.target
        expr = node.expr
        #evaluate sides
        ts = self.visit(target)
        es = self.visit(expr)
        #Check both sides for get expression
        self.validate_get(target,ts)
        self.validate_get(expr,es)
        expr.prom_type = expr.eval_type.promote_to(target.eval_type)
        if target.eval_type != expr.eval_type and not expr.prom_type:
            self.current_node = node
            self.error(f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{target.eval_type.name}' e '{expr.eval_type.name}'")
        node.eval_type = target.eval_type

    def visit_index(self,node):
        #Check if index is int
        index = node.index
        self.visit(index)
        if index.eval_type != Type.INT:
            self.error("Os índices de uma lista devem ser inteiros")

        #Check if target supports indexing
        target = node.target
        self.visit(target)
        t_type = target.eval_type 
        if type(t_type) != Lista:
            self.error(f"O valor do tipo '{t_type}' não é indexável")

        node.eval_type = t_type.subtype

    def visit_converte(self,node):
        #check expression
        self.visit(node.expression)
        type_name = node.new_type.lexeme
        type_symbol = self.current_scope.resolve(type_name)
        if type_symbol is None:
            self.error(self.UNDEFINED_TYPE.format(type=type_name))
        elif not type_symbol.is_type():
            self.error(f"o identificador '{type_name}' não é um tipo")
        #Update eval_type
        node.eval_type = type_symbol
       
    def visit_binop(self,node):
        ls = self.visit(node.left)
        rs = self.visit(node.right)
        lhs = node.left
        rhs = node.right
        #Validate in case of get nodes
        self.validate_get(lhs,ls)
        self.validate_get(rhs,rs)
        #Evaluate type of binary
        #arithmetic operation
        operator = node.token
        result = self.get_binop_result(lhs.eval_type,operator.token,rhs.eval_type)
        if not result:
            self.current_node = node
            self.error(
                self.INVALID_OP,
                t1=lhs.eval_type,
                t2=rhs.eval_type,
                operator=operator.lexeme
            )
        node.eval_type = result
        lhs.prom_type = lhs.eval_type.promote_to(rhs.eval_type)
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type)

    def get_binop_result(self,lhs_type,op,rhs_type):
        #Get result type of a binary operation based on
        # on operator and operand type
        if not lhs_type.is_operable() or not rhs_type.is_operable():
            return None

        if op in (TT.PLUS,TT.MINUS,TT.STAR,TT.SLASH,TT.DOUBLESLASH,TT.MODULO):
            if lhs_type.is_numeric() and rhs_type.is_numeric(): 
                return Type.INT if lhs_type == Type.INT and rhs_type == Type.INT and\
                op != TT.SLASH else Type.REAL

            elif lhs_type == Type.TEXTO and rhs_type == Type.TEXTO:
                #For strings only plus operator works
                return Type.TEXTO if op == TT.PLUS else None

        elif op in (TT.GREATER,TT.LESS,TT.GREATEREQ,TT.LESSEQ):
            if lhs_type.is_numeric() and rhs_type.is_numeric(): 
                return Type.BOOL

        elif op in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            if (lhs_type.is_numeric() and rhs_type.is_numeric()) or \
            lhs_type == rhs_type:
                return Type.BOOL

        elif op in (TT.E,TT.OU):
            if lhs_type == Type.BOOL and rhs_type == Type.BOOL:
                return Type.BOOL
        return None

    def visit_unaryop(self,node):
        operand = self.visit(node.operand)
        #Check if operand is a get node that can not be evaluated
        self.validate_get(node.operand,operand)
        operator = node.token.token
        lexeme = node.token.lexeme
        op_type = node.operand.eval_type
        if operator in (TT.PLUS,TT.MINUS):
            if op_type != Type.INT and op_type != Type.REAL:
                self.current_node = node
                self.error(self.INVALID_UOP,operator=lexeme,type=op_type)
        elif operator == TT.NAO:
            if op_type != Type.BOOL:
                self.error(self.INVALID_UOP,operator=lexeme,type=op_type)
        node.eval_type = op_type

    def visit_assign(self,node):
        lhs = node.left
        rhs = node.right
        rs = self.visit(rhs)
        #Check rhs of assignment
        #is expression
        self.validate_get(rhs,rs)
        self.visit(lhs)
        #Set node types
        node.eval_type = lhs.eval_type
        node.prom_type = None
        #Set promotion type for right side
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type)
        if not self.types_match(lhs.eval_type,rhs.eval_type):
            self.current_node = node
            self.error(f"atribuição inválida. incompatibilidade entre os operandos da atribuição")

    def visit_mostra(self,node):
        sym = self.visit(node.exp)
        #Check if it is trying to reference method
        self.validate_get(node.exp,sym)

    def visit_retorna(self,node):
        if not self.current_function:
            self.current_node = node
            self.error(f"A directiva 'retorna' só pode ser usada dentro de uma função")

        #REMOVE: Old and unused constructor logic
        if self.current_function.is_constructor:
            self.error("Não pode usar a directiva 'retorna' dentro de um constructor")
        func_type = self.current_function.type

        #TODO: Allow empty return from void functions
        if self.current_function.type == Type.VAZIO:
            self.error("Não pode usar a directiva 'retorna' em uma função vazia")

        expr = node.exp
        self.visit(expr)
        expr.prom_type = expr.eval_type.promote_to(func_type)
        if not self.types_match(func_type,expr.eval_type):
            self.error(f"expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função")

    def visit_se(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(f"a condição da instrução 'se' deve ser um valor lógico")
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_enquanto(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.current_node = node
            self.error(f"a condição da instrução 'enquanto' deve ser um valor lógico")
        self.visit(node.statement)

    def visit_para(self,node):
        self.visit(node.expression)
        #Define control variable for loop
        name = node.expression.name.lexeme
        sym = symbols.VariableSymbol(name,self.current_scope.resolve("int"))
        scope = symbols.Scope(symbols.Scope.LOCAL,self.current_scope)
        scope.define(name,sym)
        self.visit(node.statement,scope)

    def visit_paraexpr(self,node):
        #self.visit(node.name)
        self.visit(node.range_expr)

    def visit_rangeexpr(self,node):
        self.visit(node.start)
        self.visit(node.end)
        if node.inc:
            self.visit(node.inc)
        for node in (node.start,node.end,node.inc):
            #Skip inc node in case it's empty lool
            if not node:
                continue
            if node.eval_type != Type.INT:
                self.error("os parâmetros de uma série devem ser do tipo 'int'")

    def visit_call(self,node):
        callee = node.callee
        #Call is made on a variable
        if isinstance(callee,ast.Variable):
            name = callee.token.lexeme
            sym = self.current_scope.resolve(name)
            if not sym:
                self.error(f"o identificador '{name}' não foi definido neste escopo")
        #Call is made on another call
        elif isinstance(callee,ast.Call):
            # Since amanda doesn't have first class functions,
            # calling a call is always illegal
            self.error(f"Não pode invocar o resultado de uma invocação")
        elif isinstance(callee,ast.Get):
            sym = self.visit(callee)
        elif isinstance(callee,ast.Super):
            self.visit(callee)
            if not self.current_function.is_constructor:
                self.error(f"O constructor da superclasse só pode ser invocado no constructor da subclasse")
            sym = self.current_class.superclass
            #Just to be cautious
            #REMOVE: Remove this assert, was just here for testing
            assert sym != None
        else:
            self.error(f"o símbolo '{node.callee.token.lexeme}' não é invocável")
        if isinstance(sym,symbols.ClassSymbol):
            self.validate_constructor(sym,node.fargs)
            if isinstance(callee,ast.Super):
                node.eval_type = self.global_scope.get("vazio")  
            else:
                node.eval_type = sym
        else:
            if sym.name in self.BUILTIN_OPS:
                self.builtin_call(sym.name,node)
                return sym
            self.validate_call(sym,node.fargs)
            node.eval_type = sym.type        
        return sym
    
    # Handles calls to special builtin operation
    def builtin_call(self,name,node):
        if name == "lista":
            self.check_arity(node.fargs,name,2)
            list_type = node.fargs[0]
            if type(list_type) != ast.Variable:
                self.error(
                    "O argumento 1 da função 'lista' deve ser um tipo"
                )

            list_type = self.get_type(list_type.token) 
            if list_type == Type.INDEF:
                self.error("Não pode criar uma lista do tipo 'indef'")

            size = node.fargs[1]
            self.visit(size)
            if size.eval_type != Type.INT:
                self.error(
                    "O tamanho de uma lista deve ser representado por um inteiro"
                )

            node.eval_type = Lista(list_type)

    def check_arity(self,fargs,name,param_len):
        arg_len = len(fargs)
        if arg_len != param_len:
            self.error(
                f"número incorrecto de argumentos para a função {name}. Esperava {param_len} argumento(s), porém recebeu {arg_len}"
            )
            
    def validate_call(self,sym,fargs):
        ''' Helper method that enforces a host of semantic 
        checks on a call operation. '''
        name = sym.name
        if not sym.is_callable():
            self.error(f"identificador '{name}' não é invocável")
        for arg in fargs:
            self.visit(arg)
        self.check_arity(fargs,name,sym.arity())
        #Type promotion for parameter
        for arg,param in zip(fargs,sym.params.values()):
            arg.prom_type = arg.eval_type.promote_to(param.type)
            if not self.types_match(param.type,arg.eval_type):
                self.error(
                   f"argumento inválido. Esperava-se um argumento do tipo '{param.type}' mas recebeu o tipo '{arg.eval_type}'")
        
