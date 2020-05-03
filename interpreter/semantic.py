from enum import Enum
from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM
import interpreter.error as error


''' Class to represent built in types '''
class Type(Enum):
    INT = 0
    REAL = 1
    TEXTO = 2
    BOOL = 3
    VAZIO = 4

    def __str__(self):
        return self.name.lower()

# result of static type computation
# Vazio means illegal operation
aritop_results = [
#       int       real       texto     bool      vazio
    [Type.INT,Type.REAL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.REAL,Type.REAL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.TEXTO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]

#Table for  type for >,<,>=,<=
relop_results = [
#       int       real       texto     bool      vazio
    [Type.BOOL,Type.BOOL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.BOOL,Type.BOOL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]

#table for type results for == !=
eqop_results = [
#       int       real       texto     bool      vazio
    [Type.BOOL,Type.BOOL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.BOOL,Type.BOOL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.BOOL,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]

#table for type results for e ou !
logop_results = [
#       int       real       texto     bool      vazio
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]



# table for type promotions
# VAZIO means should not be promoted
type_promotion= [
#       int       real       texto     bool      vazio
    [Type.VAZIO,Type.REAL,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]


'''
Class that performs semantic analysis on a PTScript script
Enforces type safety and annotates nodes that need promotion
'''

class Analyzer(AST.Visitor):

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope(SYM.Scope.GLOBAL)
        self.init__builtins()

    def init__builtins(self):
        self.current_scope.define("int",SYM.BuiltInType(Type.INT))
        self.current_scope.define("real",SYM.BuiltInType(Type.REAL))
        self.current_scope.define("texto",SYM.BuiltInType(Type.TEXTO))
        self.current_scope.define("bool",SYM.BuiltInType(Type.BOOL))
        self.current_scope.define("vazio",SYM.BuiltInType(Type.VAZIO))


    def has_return(self,node):
        node_class = type(node).__name__.lower()
        method_name = f"has_return_{node_class}"
        visitor_method = getattr(self,method_name,self.general_check)
        return visitor_method(node)

    def general_check(self,node):
        return False

    def has_return_block(self,node):
        for child in node.children:
            has_return = self.has_return(child)
            if has_return:
                return True
        return False

    def has_return_sestatement(self,node):
        # If there is no else branch return None immediately
        return False if not node.else_branch else self.has_return(node.else_branch)


    def has_return_statement(self,node):
        return True if node.token.token == TT.RETORNA else False



    def error(self,line,code,**kwargs):
        message = code.format(**kwargs)
        raise error.Analysis(message,line)


    def check_program(self):
        self.visit(self.program)


    def visit_program(self,node):
        for child in node.children:
            self.visit(child)

    def visit_vardeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if not var_type or not var_type.is_type():
            self.error(node.type.line,error.Analysis.UNDEFINED_TYPE,type=node.type.lexeme)
        name = node.id.lexeme
        if self.current_scope.symbols.get(name) is not None:
            self.error(node.id.line,error.Analysis.ID_IN_USE,name=name)
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol,node.id)
        if node.assign is not None:
            if node.assign.right.token.lexeme == name:
                self.error(f"Erro ao inicializar variável. Não pode referenciar uma variável durante a sua declaração",node.id)
            self.visit(node.assign)

    def visit_arraydeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        line = node.id.line
        if not var_type or not var_type.is_type():
            self.error(line,error.Analysis.UNDEFINED_TYPE,type=node.type.lexeme)
        name = node.id.lexeme
        if self.current_scope.symbols.get(name) is not None:
            self.error(line,error.Analysis.ID_IN_USE,name=name)
        #print("SEM ANALYSIS: ",node.size)
        self.visit(node.size)
        symbol = SYM.ArraySymbol(name,var_type,node.size.token.lexeme)
        self.current_scope.define(name,symbol,node.id)


    def visit_functiondecl(self,node):
        #Check if id is already in use
        name = node.id.lexeme
        line = node.id.line
        if self.current_scope.resolve(name):
            self.error(line,error.Analysis.ID_IN_USE,name=name)
        #Check if return types exists
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if not function_type or not function_type.is_type():
            self.error(line,error.Analysis.UNDEFINED_TYPE,type=node.type.lexeme)
        #Check if function has return statement
        if function_type.name != Type.VAZIO:
            has_return = self.has_return(node.block)
            if not has_return:
                self.error(line,error.Analysis.NO_RETURN_STMT,name=name)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(param_name):
                self.error(line,error.Analysis.REPEAT_PARAM,name=name)
            param_symbol = self.visit(param)
            params[param_name] = param_symbol
            #Add params o current_scope
        symbol = SYM.FunctionSymbol(name,function_type,params)
        self.current_scope.define(name,symbol)
        scope = SYM.Scope(name,self.current_scope)
        for name,param in symbol.params.items():
            scope.define(name,param)
        self.visit(node.block,scope)
        #leave_scope
        #print(self.current_scope)

    def visit_block(self,node,scope=None):
        if scope:
            self.current_scope = scope
        else:
            self.current_scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
        for child in node.children:
            self.visit(child)
        #Pop scope
        self.current_scope = self.current_scope.enclosing_scope


    def visit_paramnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if not var_type or not var_type.is_type():
            self.error(node.type.line,error.Analysis.UNDEFINED_TYPE,type=node.type.lexeme)
        name = node.id.lexeme
        if node.is_array:
            return SYM.ArraySymbol(name,var_type)
        else:
            return SYM.VariableSymbol(name,var_type)


    def visit_expnode(self,node):
        if node.token.token == TT.IDENTIFIER:
            name = node.token.lexeme
            line = node.token.line
            sym = self.current_scope.resolve(name)
            if not sym:
                self.error(line,error.Analysis.UNDECLARED_ID,name=name)
            #Referencing array by name loool
            elif not sym.is_valid_var():
                self.error(line,error.Analysis.INVALID_REF,name=name)
            node.eval_type = sym.type.name
        elif node.token.token == TT.INTEGER:
            node.eval_type = Type.INT
        elif node.token.token == TT.REAL:
            node.eval_type = Type.REAL
        elif node.token.token == TT.STRING:
            node.eval_type = Type.TEXTO
        elif node.token.token in (TT.VERDADEIRO,TT.FALSO):
            node.eval_type = Type.BOOL

    def visit_binopnode(self,node):
        self.visit(node.left)
        self.visit(node.right)
        #Evaluate type of binary
        #arithmetic operation
        operator = node.token.token
        if operator in (TT.PLUS,TT.MINUS,TT.STAR,TT.SLASH,TT.MODULO):
            node.eval_type = aritop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.GREATER,TT.LESS,TT.GREATEREQ,TT.LESSEQ):
            node.eval_type = relop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            node.eval_type = eqop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif operator in (TT.AND,TT.OR):
            node.eval_type = logop_results[node.left.eval_type.value][node.right.eval_type.value]
        #Validate binary ops
        line = node.token.line
        lexeme = node.token.lexeme
        if node.eval_type == Type.VAZIO:
            self.error(line,error.Analysis.INVALID_OP,
            t1=node.left.eval_type, t2=node.right.eval_type,
            operator=lexeme)

        elif node.eval_type == Type.TEXTO:
            if operator != TT.PLUS:
                self.error(line,error.Analysis.BAD_STR_OP,operator=lexeme)
        node.left.prom_type = type_promotion[node.left.eval_type.value][node.right.eval_type.value]
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

    def visit_unaryopnode(self,node):
        self.visit(node.operand)
        operator = node.token.token
        lexeme = node.token.lexeme
        line = node.token.line
        type = node.operand.eval_type
        if operator in (TT.PLUS,TT.MINUS):
            if type != Type.INT and type != Type.REAL:
                self.error(line,error.Analysis.INVALID_UOP,operator=lexeme,type=type)
            node.eval_type = type
        elif operator == TT.NOT:
            node.operand.prom_type = logop_results[type.value][Type.BOOL.value]
            if type != Type.BOOL and node.operand.prom_type == Type.VAZIO:
                self.error(line,error.Analysis.INVALID_UOP,operator=lexeme,type=type)
            node.eval_type = node.operand.prom_type


    def visit_assignnode(self,node):
        self.visit(node.right)
        self.visit(node.left)

        #Set node types
        node.eval_type = node.left.eval_type
        node.prom_type = Type.VAZIO
        #Set promotion type for right side
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

        line = node.token.line
        if node.left.eval_type != node.right.eval_type and node.right.prom_type == Type.VAZIO:
            self.error(line,f"atribuição inválida. incompatibilidade entre os operandos da atribuição [{node.left.eval_type} = {node.right.eval_type}]")

    def visit_statement(self,node):
        #self.visit(node.exp)
        self.visit(node.exp)
        token = node.token.token
        line = node.token.line
        #check if return statement is inside a function
        if token == TT.RETORNA:
            function = self.current_scope.get_enclosing_func()
            #TODO: Fix return bug inside local scope
            if not function:
                self.error(line,f"O comando 'retorna' só pode ser usado dentro de uma função")
            function = self.current_scope.resolve(function.name)
            node.exp.prom_type = type_promotion[node.exp.eval_type.value][function.type.name.value]
            if function.type.name == Type.VAZIO:
                self.error(line,f"expressão de retorno inválida. Procedimentos não podem retornar valores")
            elif function.type.name != node.exp.eval_type and node.exp.prom_type == Type.VAZIO:
                self.error(line,f"expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função")



    def visit_sestatement(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(node.token.line,f"a condição da instrução 'if' deve ser um valor lógico")
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_whilestatement(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(node.token.line,f"a condição da instrução 'while' deve ser um valor lógico")
        self.visit(node.statement)

    def visit_forstatement(self,node):
        self.visit(node.expression)
        id = node.expression.id.lexeme
        sym = SYM.VariableSymbol(id,self.current_scope.resolve("int"))
        scope = SYM.Scope(SYM.Scope.LOCAL,self.current_scope)
        scope.define(id,sym)
        if isinstance(node.statement,AST.Block):
            self.visit(node.statement,scope)
        else:
            self.current_scope = scope
            self.visit(node.statement)
            #pop scope
            self.current_scope = self.current_scope.enclosing_scope

    def visit_forexpr(self,node):
        self.visit(node.id)
        self.visit(node.range)

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
                self.error(node.token.line,"os parâmetros de uma série devem ser do tipo 'int'")

    def visit_functioncall(self,node):
        for arg in node.fargs:
            self.visit(arg)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        line = node.id.line
        arg_len = len(node.fargs)
        param_len = len(sym.params)
        if sym == None:
            self.error(line,f"função '{id}' não foi definida")
        elif not isinstance(sym,SYM.FunctionSymbol):
            self.error(line,f"identificador '{id}' não é uma função")
        elif arg_len != param_len:
            self.error(line,f"número incorrecto de argumentos para a função {node.id.lexeme}. Esperava {param_len} argumentos, porém recebeu {arg_len}")
        #Type promotion for parameter
        func_decl = ",".join(["{} {}".format(param.type,param.name) for param in sym.params.values()]) #Get function signature
        for arg,param in zip(node.fargs,sym.params.values()):
            arg.prom_type = type_promotion[arg.eval_type.value][param.type.name.value]
            if param.type.name != arg.eval_type and arg.prom_type == Type.VAZIO:
                self.error(line,f"argumento inválido. Esperava-se um argumento do tipo '{param.type.name}' mas recebeu o tipo '{arg.eval_type}'.\nassinatura: {id}({func_decl})")
        node.eval_type = sym.type.name


    def visit_arrayref(self,node):
        self.visit(node.index)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        line = node.id.line
        #Semantic checks start here
        if not sym:
            self.error(line,error.Analysis.UNDECLARED_ID,name=id)
        elif not isinstance(sym,SYM.ArraySymbol):
            self.error(line,f"o identificador '{id}' não é um vector")
        #index = node.in
        if node.index.eval_type != Type.INT:
            self.error(line,f"o índice de um vector deve ser um inteiro")
        node.eval_type = sym.type.name
