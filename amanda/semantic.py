from enum import Enum
from amanda.lexer import Lexer
from amanda.tokens import TokenType as TT
from amanda.tokens import Token
import amanda.ast_nodes as ast
import amanda.symbols as SYM
import amanda.error as error
import amanda.natives as natives
import modules.functions as bltins_funcs




'''
Class that performs semantic analysis on a syntatically valid
amanda program.
'''

class Analyzer(ast.Visitor):

    def __init__(self):

        #Just to have quick access to things like types and e.t.c
        self.global_scope = SYM.Scope(SYM.Scope.GLOBAL)
        self.current_scope = self.global_scope
        self.current_node = None
        #Used to check if we are in a class
        self.current_class = None
        #Used to check if we are in a function
        self.current_function = None
        self.init_builtins()

    def init_builtins(self):
        self.global_scope.define("int",SYM.BuiltInType("int",SYM.Tag.INT))
        self.global_scope.define("real",SYM.BuiltInType("real",SYM.Tag.REAL))
        self.global_scope.define("bool",SYM.BuiltInType("bool",SYM.Tag.BOOL))
        self.global_scope.define("vazio",SYM.BuiltInType("vazio",SYM.Tag.VAZIO))
        
        #Initialize builtin types
        builtins = natives.builtin_types.values()
        for builtin in builtins:
            builtin.load_symbol(self.global_scope)
        for builtin in builtins:
            builtin.define_symbol(self.global_scope)


        #Initialize builtin functions
        for name,data in bltins_funcs.functions.items():
            function = bltins_funcs.get_func_sym(name,
                      data["type"],self.global_scope,data["params"])
            self.global_scope.define(name,function)

        

    def has_return(self,node):
        node_class = type(node).__name__.lower()
        method_name = f"has_return_{node_class}"
        visitor_method = getattr(self,method_name,self.general_check)
        #update ast node

        #Previous node is used for nodes that call visit on
        #other nodes
        self.current_node = node
        return visitor_method(node)

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

    def error(self,code,**kwargs):
        message = code.format(**kwargs)
        raise error.Analysis(
          message,self.current_node.token.line,
          self.current_node.token.col)


    def check_program(self,program):
        self.visit(program)
        return program

    def visit_program(self,node):
        for child in node.children:
            self.visit(child)

    def visit_vardecl(self,node):
        klass = self.current_class
        name = node.name.lexeme

        #If declaration has already been resolved,
        #define the member in current scope and exit declaration
        #Only skip declarations in the class scope not in local
        #scope
        if klass and klass.resolved and not \
        self.current_function:
            self.current_scope.define(name,klass.get_member(name))
            return
        var_type = self.current_scope.resolve(node.var_type.lexeme)
        if not var_type or not var_type.is_type():
            self.error(
                error.Analysis.UNDEFINED_TYPE,
                type=node.var_type.lexeme
            )

        if self.current_scope.get(name):
            self.error(error.Analysis.ID_IN_USE,name=name)
        symbol = SYM.VariableSymbol(name,var_type)
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
        #If current class has been resolved
        #just execute the body
        klass = self.current_class
        if klass and klass.resolved:
            function = klass.get_member(name)
            self.check_function(name,function,node)
            return
        if self.current_scope.get(name):
            self.error(error.Analysis.ID_IN_USE,name=name)
        #Check if return types exists
        if not node.func_type:
            self.validate_void_func(name,node)
            return
        decl_type = node.func_type.lexeme
        function_type =  self.current_scope.resolve(decl_type)
        #TODO: fix this hack
        if not function_type or not function_type.is_type():
            self.error(error.Analysis.UNDEFINED_TYPE,type=decl_type)
        has_return = self.has_return(node.block)
        if not has_return:
            #TODO: fix this hack
            self.current_node = node
            self.error(error.Analysis.NO_RETURN_STMT,name=name)
        symbol = SYM.FunctionSymbol(name,function_type)
        self.check_function(name,symbol,node)

    def validate_void_func(self,name,node):

        #Checks if this is a class constructor 
        #If it's not, just consider it a normal
        #plain void function
        klass = self.current_class
        if name == "constructor" and klass:
            symbol = SYM.FunctionSymbol(name,self.current_class)
            symbol.is_constructor = True
            if klass.superclass and \
            not self.check_super(name,klass.superclass,node.block):
                self.error("O constructor da superclasse deve ser invocado")
        else:
            symbol = SYM.FunctionSymbol(name,self.current_scope.get("vazio"))
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
        params_dict = {}
        for param in params:
            param_name = param.name.lexeme
            if params_dict.get(param_name):
                self.error(error.Analysis.REPEAT_PARAM,name=param_name)
            param_symbol = self.visit(param)
            params_dict[param_name] = param_symbol
            #Add params o current_scope
        scope = SYM.Scope(name,self.current_scope)
        for param_name,param in params_dict.items():
            scope.define(param_name,param)
        return (scope,params_dict)



    def visit_classdecl(self,node):
        name = node.name.lexeme
        if self.current_scope.get(name):
            self.error(error.Analysis.ID_IN_USE,name=name)
        #Check if class has a valid superclass
        superclass = node.superclass
        if superclass:
            super_name = superclass.lexeme
            superclass = self.current_scope.resolve(super_name)
            if not superclass:
                self.error(error.Analysis.UNDECLARED_ID,name=super_name)
        klass = SYM.ClassSymbol(name,superclass=superclass)
        self.current_scope.define(name,klass)
        res_scope = SYM.Scope(name,self.current_scope)
        prev_class = self.current_class
        self.current_class = klass
        #Resolve class
        klass.members = self.visit_classbody(node.body,res_scope)
        klass.resolved = True
        #Revisit class
        self.visit_classbody(node.body,SYM.Scope(name,self.current_scope))
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
        return SYM.VariableSymbol('eu',self.current_class)

    def visit_super(self,node):
        klass = self.current_class
        if not klass:
            self.error("a palavra reservada 'super' só pode ser usada dentro de uma classe")
        if not klass.superclass:
            self.error("Esta classe não possui uma superclasse")
        klass = klass.superclass
        node.eval_type = klass
        return SYM.VariableSymbol('super',klass)


    def visit_block(self,node,scope=None):
        if not scope:
            scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
        self.current_scope = scope
        for child in node.children:
            self.visit(child)
        self.current_scope = self.current_scope.enclosing_scope


    def visit_param(self,node):
        param_type = node.param_type.lexeme
        var_type = self.current_scope.resolve(param_type)
        if not var_type or not var_type.is_type():
            self.error(
                        error.Analysis.UNDEFINED_TYPE,
                        type=param_type
                    )
        name = node.name.lexeme
        return SYM.VariableSymbol(name,var_type)


    def visit_constant(self,node):

        constant = node.token.token
        if constant == TT.INTEGER:
            node.eval_type = self.global_scope.resolve("int")
        elif constant == TT.REAL:
            node.eval_type = self.global_scope.resolve("real")
        elif constant == TT.STRING:
            node.eval_type = self.global_scope.resolve("Texto")
        elif constant in (TT.VERDADEIRO,TT.FALSO):
            node.eval_type = self.global_scope.resolve("bool")


    def visit_variable(self,node):
        name = node.token.lexeme
        sym = self.current_scope.resolve(name)
        if not sym:
            self.error(error.Analysis.UNDECLARED_ID,name=name)
        #Referencing array by name 
        elif not sym.can_evaluate():
            self.error(error.Analysis.INVALID_REF,name=name)
        node.eval_type = sym.type
        return sym

    def validate_get(self,node,sym):
        ''' Method to validate get expressions'''
        if isinstance(node,ast.Get) and not sym.can_evaluate():
            self.error(error.Analysis.INVALID_REF,name=sym.name)

    def visit_get(self,node):
        ''' Method that processes getter expressions.
        Returns the resolved symbol of the get expression.'''
        target = self.visit(node.target)

        #Check for literal that are converted to object
        if (target and target.type.tag != SYM.Tag.REF) or \
            (node.target.eval_type.tag != SYM.Tag.REF):
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
        expr.prom_type = expr.eval_type.promote_to(target.eval_type,self.current_scope)
        if target.eval_type != expr.eval_type and not expr.prom_type:
            self.current_node = node
            self.error(f"atribuição inválida. incompatibilidade entre os operandos da atribuição: '{target.eval_type.name}' e '{expr.eval_type.name}'")
        node.eval_type = target.eval_type


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
        result = lhs.eval_type.validate_op(operator.token,rhs.eval_type,self.current_scope)
        if not result:
            self.current_node = node
            self.error(
                error.Analysis.INVALID_OP,
                t1=lhs.eval_type,
                t2=rhs.eval_type,
                operator=operator.lexeme)
            
        node.eval_type = result
        lhs.prom_type = lhs.eval_type.promote_to(rhs.eval_type,self.current_scope)
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type,self.current_scope)


    def visit_unaryop(self,node):
        operand = self.visit(node.operand)
        #Check if operand is a get node that can not be evaluated
        self.validate_get(node.operand,operand)

        operator = node.token.token
        lexeme = node.token.lexeme
        op_type = node.operand.eval_type
        if operator in (TT.PLUS,TT.MINUS):
            if op_type.tag != SYM.Tag.INT and op_type.tag != SYM.Tag.REAL:
                self.current_node = node
                self.error(error.Analysis.INVALID_UOP,operator=lexeme,op_type=op_type)
        elif operator == TT.NAO:
            if op_type.tag != SYM.Tag.BOOL:
                self.error(error.Analysis.INVALID_UOP,operator=lexeme,type=op_type)
        node.eval_type = op_type


    def visit_assign(self,node):
        lhs = node.left
        rhs = node.right

        rs = self.visit(rhs)
        #Check rhs of assignment
        #is expression
        self.validate_get(rhs,rs)
        self.visit(lhs)
        #Check rhs is call to super constructor

        #Set node types
        node.eval_type = lhs.eval_type
        node.prom_type = None
        #Set promotion type for right side
        rhs.prom_type = rhs.eval_type.promote_to(lhs.eval_type,self.current_scope)
        if lhs.eval_type != rhs.eval_type and not rhs.prom_type:
            self.current_node = node
            self.error(f"atribuição inválida. incompatibilidade entre os operandos da atribuição")


    def visit_mostra(self,node):
        sym = self.visit(node.exp)
        #Check if it is trying to reference method
        self.validate_get(node.exp,sym)

    def visit_retorna(self,node):
        expr = node.exp
        self.visit(expr)
        if not self.current_function:
            self.current_node = node
            self.error(f"A directiva 'retorna' só pode ser usada dentro de uma função")
        if self.current_function.is_constructor:
            self.error("Não pode usar a directiva 'retorna' dentro de um constructor")
        func_type = self.current_function.type
        #TODO: Allow empty return from void functions
        if self.current_function.type.name == "vazio":
            self.error("Não pode usar a directiva 'retorna' em uma função vazia")
        expr.prom_type = expr.eval_type.promote_to(func_type,self.current_scope)
        if func_type.tag != expr.eval_type.tag and not expr.prom_type:
            self.error(f"expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função")


    def visit_se(self,node):
        self.visit(node.condition)
        if node.condition.eval_type.tag != SYM.Tag.BOOL:
            self.error(f"a condição da instrução 'se' deve ser um valor lógico")
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_enquanto(self,node):
        self.visit(node.condition)
        if node.condition.eval_type.tag != SYM.Tag.BOOL:
            self.current_node = node
            self.error(f"a condição da instrução 'enquanto' deve ser um valor lógico")
        self.visit(node.statement)

    def visit_para(self,node):
        self.visit(node.expression)
        #Define control variable for loop
        name = node.expression.name.lexeme
        sym = SYM.VariableSymbol(name,self.current_scope.resolve("int"))
        scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
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
            if node.eval_type.tag != SYM.Tag.INT:
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
            #TODO: Remove this later
            assert sym != None
        else:
            self.error(f"o símbolo '{node.callee.token.lexeme}' não é invocável")
        if isinstance(sym,SYM.ClassSymbol):
            self.validate_constructor(sym,node.fargs)
            if isinstance(callee,ast.Super):
                node.eval_type = self.global_scope.get("vazio")  
            else:
                node.eval_type = sym
        else:
            self.validate_call(sym,node.fargs)
            node.eval_type = sym.type        
        return sym

    def validate_constructor(self,sym,fargs):
        ''' Helper method to validate function
        instantiation'''
        constructor = sym.get_member("constructor")
        if not constructor or not constructor.is_constructor:
            #Use an empty constructor if no constructor or
            #user defined constructor violated rules of
            #valid constructors
            #If class being instatiated has a superclass,
            #Check if it has an empty constructor and throw
            #error in case not
            superclass = sym.superclass
            super_constructor = superclass.get_member("constructor") if superclass else None
            if superclass and super_constructor and \
            super_constructor.arity() > 0:
                self.error(f"A classe '{sym.name}' deve implementar um constructor para satisfazer o constructor da superclasse")

            constructor = SYM.FunctionSymbol(sym.name,sym,{})
            constructor.is_constructor = True
        self.validate_call(constructor,fargs)



    def validate_call(self,sym,fargs):
        ''' Helper method that enforces a host of semantic 
        checks on a call operation. '''
        name = sym.name
        if not sym.is_callable():
            self.error(f"identificador '{name}' não é invocável")
        for arg in fargs:
            self.visit(arg)
        arg_len = len(fargs)
        param_len = sym.arity()
        if arg_len != param_len:
            self.error(
                f"número incorrecto de argumentos para a função {name}. Esperava {param_len} argumento(s), porém recebeu {arg_len}")
        #Type promotion for parameter
        for arg,param in zip(fargs,sym.params.values()):
            arg.prom_type = arg.eval_type.promote_to(param.type,self.current_scope)
            if param.type.tag != arg.eval_type.tag and not arg.prom_type:
                self.error(
                   f"argumento inválido. Esperava-se um argumento do tipo '{param.type.name}' mas recebeu o tipo '{arg.eval_type.name}'")
        
    
        
