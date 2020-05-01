from enum import Enum
from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM
from interpreter.error import SemanticError


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



    def error(self,message,token):
        raise SemanticError(message,token.line)


    def check_program(self):
        self.visit(self.program)


    def visit_program(self,node):
        for child in node.children:
            self.visit(child)

    def visit_vardeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        if self.current_scope.symbols.get(name) is not None:
            self.error(f"O identificador '{name}' já foi declarado neste escopo",node.id)
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol,node.id)
        if node.assign is not None:
            if node.assign.right.token.lexeme == name:
                self.error(f"Erro ao inicializar variável. Não pode referenciar uma variável durante a sua declaração",node.id)
            self.visit(node.assign)

    def visit_arraydeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        if self.current_scope.symbols.get(name) is not None:
            self.error(f"O identificador '{name}' já foi declarado neste escopo",node.id)
        #print("SEM ANALYSIS: ",node.size)
        self.visit(node.size)
        symbol = SYM.ArraySymbol(name,var_type,node.size.token.lexeme)
        self.current_scope.define(name,symbol,node.id)


    def visit_functiondecl(self,node):
        #Check if id is already in use
        name = node.id.lexeme
        if self.current_scope.resolve(name):
            self.error(f"A função '{name}' já foi definida neste escopo",node.id)
        #Check if return types exists
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if function_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        #Check if function has return statement
        if function_type.name != Type.VAZIO:
            has_return = self.has_return(node.block)
            if not has_return:
                self.error(f"A função {node.id.lexeme} não possui a instrução 'retorna'",node.id)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(param_name):
                self.error(f"O parâmetro '{param_name}' já foi especificado nesta função",node.id)
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
        if var_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        if node.is_array:
            return SYM.ArraySymbol(name,var_type)
        else:
            return SYM.VariableSymbol(name,var_type)


    def visit_expnode(self,node):
        if node.token.token == TT.IDENTIFIER:
            name = node.token.lexeme
            sym = self.current_scope.resolve(name)
            if not sym:
                self.error(f"O identificador '{name}' não foi declarado",node.token)
            #Referencing array by name loool
            elif not sym.is_valid_var():
                self.error(f"O identificador '{name}' não é uma referência válida",node.token)
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
        if node.token.token in (TT.PLUS,TT.MINUS,TT.STAR,TT.SLASH,TT.MODULO):
            node.eval_type = aritop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif node.token.token in (TT.GREATER,TT.LESS,TT.GREATEREQ,TT.LESSEQ):
            node.eval_type = relop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif node.token.token in (TT.DOUBLEEQUAL,TT.NOTEQUAL):
            node.eval_type = eqop_results[node.left.eval_type.value][node.right.eval_type.value]
        elif node.token.token in (TT.AND,TT.OR):
            node.eval_type = logop_results[node.left.eval_type.value][node.right.eval_type.value]
        #Validate binary ops
        if node.eval_type == Type.VAZIO:
            self.error(f"Operação inválida. Os operandos possuem tipos incompatíveis: {node.left.eval_type} '{node.token.lexeme}' {node.right.eval_type}",node.token)

        elif node.eval_type == Type.TEXTO:
            if node.token.token != TT.PLUS:
                self.error(f"Operação inválida. O tipo 'texto' não suporta a operações com o operador '{node.token.lexeme}'",node.token)
        node.left.prom_type = type_promotion[node.left.eval_type.value][node.right.eval_type.value]
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

    def visit_unaryopnode(self,node):
        self.visit(node.operand)
        if node.token.token in (TT.PLUS,TT.MINUS):
            if node.operand.eval_type != Type.INT and node.operand.eval_type != Type.REAL:
                self.error(f"Operação inválida. O Operador unário '{node.token.lexeme}' só pode ser usado com tipos numéricos",node.token)
            node.eval_type = node.operand.eval_type
        elif node.token.token == TT.NOT:
            node.operand.prom_type = logop_results[node.operand.eval_type.value][Type.BOOL.value]
            if node.operand.eval_type != Type.BOOL and node.operand.prom_type == Type.VAZIO:
                self.error(f"Operação inválida. O Operador unário '{node.token.lexeme}' só pode ser usado com valores lógicos",node.token)
            node.eval_type = node.operand.prom_type


    def visit_assignnode(self,node):
        self.visit(node.right)
        self.visit(node.left)

        #Set node types
        node.eval_type = node.left.eval_type
        node.prom_type = Type.VAZIO
        #Set promotion type for right side
        node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

        if node.left.eval_type != node.right.eval_type and node.right.prom_type == Type.VAZIO:
            self.error(f"Atribuição inválida. incompatibilidade entre os operandos da atribuição [{node.left.eval_type} = {node.right.eval_type}]",node.token)

    def visit_statement(self,node):
        #self.visit(node.exp)
        self.visit(node.exp)
        token = node.token.token
        #check if return statement is inside a function
        if token == TT.RETORNA:
            function = self.current_scope.get_enclosing_func()
            #TODO: Fix return bug inside local scope
            if not function:
                self.error(f"O comando 'retorna' só pode ser usado dentro de uma função",node.token)
            function = self.current_scope.resolve(function.name)
            node.exp.prom_type = type_promotion[node.exp.eval_type.value][function.type.name.value]
            if function.type.name == Type.VAZIO:
                self.error(f"Expressão de retorno inválida. Procedimentos não podem retornar valores",node.token)
            elif function.type.name != node.exp.eval_type and node.exp.prom_type == Type.VAZIO:
                self.error(f"Expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função",node.token)



    def visit_sestatement(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(f"A condição da instrução 'if' deve ser um valor lógico",node.token)
        self.visit(node.then_branch)
        if node.else_branch:
            self.visit(node.else_branch)

    def visit_whilestatement(self,node):
        self.visit(node.condition)
        if node.condition.eval_type != Type.BOOL:
            self.error(f"A condição da instrução 'while' deve ser um valor lógico",node.token)
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
                self.error("Erro de tipo. Os parâmetros de uma série devem ser do tipo 'int'",node.token)




    def visit_functioncall(self,node):
        for arg in node.fargs:
            self.visit(arg)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        if sym == None:
            self.error(f"Função '{id}' não foi definida",node.id)
        elif not isinstance(sym,SYM.FunctionSymbol):
            self.error(f"Identificador '{id}' não é uma função",node.id)
        elif len(node.fargs) != len(sym.params):
            self.error(f"Número incorrecto de argumentos para a função {node.id.lexeme}. Esperava {len(sym.params)} argumentos, porém recebeu {len(node.fargs)}",node.id)
        #Type promotion for parameter
        func_decl = ",".join(["{} {}".format(param.type,param.name) for param in sym.params.values()]) #Get function signature
        for arg,param in zip(node.fargs,sym.params.values()):
            arg.prom_type = type_promotion[arg.eval_type.value][param.type.name.value]
            if param.type.name != arg.eval_type and arg.prom_type == Type.VAZIO:
                self.error(f"Argumento inválido. Esperava-se um argumento do tipo '{param.type.name}' mas recebeu o tipo '{arg.eval_type}'.\nassinatura: {id}({func_decl})",node.id)
        node.eval_type = sym.type.name


    def visit_arrayref(self,node):
        self.visit(node.index)
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        #Semantic checks start here
        if sym == None:
            self.error(f"O identificador '{id}' não foi declarado",node.id)
        elif not isinstance(sym,SYM.ArraySymbol):
            self.error(f"O identificador '{id}' não é um vector",node.id)
        #index = node.in
        if node.index.eval_type != Type.INT:
            self.error(f"O índice de um vector deve ser um inteiro",node.id)
        node.eval_type = sym.type.name
