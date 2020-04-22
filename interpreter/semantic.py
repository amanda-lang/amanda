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
    [Type.BOOL,Type.BOOL,Type.BOOL,Type.BOOL,Type.VAZIO],
    [Type.BOOL,Type.BOOL,Type.BOOL,Type.BOOL,Type.VAZIO],
    [Type.BOOL,Type.BOOL,Type.BOOL,Type.BOOL,Type.VAZIO],
    [Type.BOOL,Type.BOOL,Type.BOOL,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]



# table for type promotions
# None means should not be promoted
type_promotion= [
#       int       real       texto     bool      vazio
    [Type.VAZIO,Type.REAL,Type.VAZIO,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.BOOL,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO],
    [Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO,Type.VAZIO]
]


'''
Class that performs semantic analysis on a PTScript script
Enforces type safety and annotates nodes that need promotion
'''

class Analyzer(AST.Visitor):

    GLOBAL = "GLOBAL_SCOPE"
    LOCAL = "LOCAL_SCOPE"#For blocks
    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope(Analyzer.GLOBAL)
        self.init__builtins()

    def init__builtins(self):
        self.current_scope.define("int",SYM.BuiltInType(Type.INT))
        self.current_scope.define("real",SYM.BuiltInType(Type.REAL))
        self.current_scope.define("texto",SYM.BuiltInType(Type.TEXTO))
        self.current_scope.define("bool",SYM.BuiltInType(Type.BOOL))
        self.current_scope.define("vazio",SYM.BuiltInType(Type.VAZIO))



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
        symbol = SYM.ArraySymbol(name,var_type,node.size)
        self.current_scope.define(name,symbol,node.id)


    def visit_functiondecl(self,node):
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if function_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        if self.current_scope.resolve(name) is not None:
            self.error(f"A função '{name}' já foi definida neste escopo",node.id)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(param_name) is not None:
                self.error(f"O parâmetro '{param_name}' já foi especificado nesta função",node.id)
            param_symbol = self.visit(param)
            params[param_name] = param_symbol
            #Add params o current_scope
        symbol = SYM.FunctionSymbol(name,function_type,params)
        self.current_scope.define(name,symbol)
        self.visit(node.block,symbol)
        #leave_scope
        #print(self.current_scope)

    def visit_block(self,node,function=None):
        self.current_scope = SYM.Scope(Analyzer.LOCAL,self.current_scope)
        if function is not None:
            self.current_scope.name = function.name
            for param in function.params:
                self.current_scope.define(param,function.params[param])
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
            if sym == None:
                self.error(f"O identificador '{name}' não foi declarado",node.token)
            #Referencing array by name loool
            elif isinstance(sym,SYM.ArraySymbol):
                self.error(f"Não pode aceder vectores sem especificar um índice",node.token)
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

        else:
            if node.eval_type == Type.TEXTO:
                if node.token.token != TT.PLUS:
                    self.error(f"Operação inválida. O tipo 'texto' não suporta a operações com o operador '{node.token.lexeme}'",node.token)
            if node.token.token in (TT.AND,TT.OR):
                node.left.prom_type = type_promotion[node.left.eval_type.value][Type.BOOL.value]
                node.right.prom_type = type_promotion[node.right.eval_type.value][Type.BOOL.value]
            else:
                node.left.prom_type = type_promotion[node.left.eval_type.value][node.right.eval_type.value]
                node.right.prom_type = type_promotion[node.right.eval_type.value][node.left.eval_type.value]

    def visit_unaryopnode(self,node):
        self.visit(node.operand)
        if node.token.token in (TT.PLUS,TT.MINUS):
            if node.operand.eval_type != Type.INT and node.operand.eval_type != Type.REAL:
                self.error(f"Operação inválida. O Operador unário '{node.token.lexeme}' só pode ser usado com tipos numéricos",node.token)
            node.eval_type = node.operand.eval_type
        elif node.token.token == TT.NOT:
            node.operand.prom_type = logop_results[node.operand.eval_type.value][Type.BOOL]
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
        if isinstance(node.exp,AST.AssignNode):
            self.error(f"instrução inválida. A instrução '{node.token.lexeme}' não pode ser usada com uma expressão de atribuição",node.token)
        if token == TT.RETORNA:
            if self.current_scope.name == Analyzer.GLOBAL:
                self.error(f"O comando 'retorna' só pode ser usado dentro de uma função",node.token)
            sym = self.current_scope.resolve(self.current_scope.name)
            if not isinstance(sym,SYM.FunctionSymbol):
                self.error(f"O comando 'retorna' só pode ser usado dentro de uma função",node.token)
            function = sym
            node.exp.prom_type = type_promotion[node.exp.eval_type.value][function.type.name.value]
            if function.type.name == Type.VAZIO:
                self.error(f"Expressão de retorno inválida. Procedimentos não podem retornar valores",node.token)
            elif function.type.name != node.exp.eval_type and node.exp.prom_type == Type.VAZIO:
                self.error(f"Expressão de retorno inválida. O tipo do valor de retorno é incompatível com o tipo de retorno da função",node.token)


    def visit_sestatement(self,node):
        self.visit(node.condition)
        self.visit(node.then_branch)
        if node.else_branch is not None:
            self.visit(node.else_branch)

    def visit_whilestatement(self,node):
        self.visit(node.condition)
        self.visit(node.statement)


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
        for i,param in enumerate(sym.params.values()):
            node.fargs[i].prom_type = type_promotion[node.fargs[i].eval_type.value][param.type.name.value]
            if param.type.name != node.fargs[i].eval_type and node.fargs[i].prom_type == Type.VAZIO:
                self.error(f"O argumento {i+1} da função {node.id.lexeme} deve ser do tipo '{param.type.name}'",node.id)
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
