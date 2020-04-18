from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM
from interpreter.error import SemanticError

BUILT_IN ={
 "int" : "inteiro",
 "real": "real",
 "texto": "texto",
 "bool":"booleano",
 "vazio":"VAZIO"
}

arit_types ={
 "inteiro" : 0,
 "real": 1,
 "texto": 2,
 "booleano": 3,
 "VAZIO": 4,
 None:4
}

#result of static type computation
#None means illegal operation
type_results = [
    [BUILT_IN["int"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["real"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["texto"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["bool"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"]]
]


'''
Class that performs semantic analysis on a PTScript script
It does this in two passes:
* First it populates the symbol table, creates a scope tree, resolves references
and computes static expression types
*the second enforces type safety rules
'''

class Analyzer(AST.Visitor):

    GLOBAL = "GLOBAL_SCOPE"

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope(Analyzer.GLOBAL)
        self.init__builtins()

    def init__builtins(self):
        for type in BUILT_IN:
            self.current_scope.define(type,SYM.BuiltInType(BUILT_IN[type],type))


    def error(self,message,token):
        raise SemanticError(message,token.line)


    def eval_arit_op(self,opand1,op,opand2):
        return type_results[arit_types[opand1.eval_type]][arit_types[opand2.eval_type]]

    def load_symbols(self):
        self.visit(self.program)


    def visit_block(self,node):
        for child in node.children:
            self.visit(child)

    def visit_vardeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol)
        if node.assign != None:
            self.visit(node.assign)

    def visit_arraydeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        symbol = SYM.ArraySymbol(name,var_type,node.size)
        self.current_scope.define(name,symbol)


    def visit_functiondecl(self,node):
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if function_type == None:
            self.error(f"O tipo de dados '{node.type.lexeme}' não foi definido",node.type)
        name = node.id.lexeme
        if self.current_scope.resolve(name) is not None:
            self.error(f"A função '{name}' já foi definida neste escopo",node.id)
        #push_scope
        self.current_scope = SYM.Scope(name,self.current_scope)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(param_name) is not None:
                self.error(f"O parâmetro '{param_name}' já foi especificado nesta função",node.id)
            param_symbol = self.visit(param)
            params[param_name] = param_symbol

        symbol = SYM.FunctionSymbol(name,function_type,params)
        self.current_scope.enclosing_scope.define(name,symbol)
        self.visit(node.block)
        #leave_scope
        #print(self.current_scope)
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
            node.eval_type = sym.type.name
        elif node.token.token == TT.INTEGER:
            node.eval_type = BUILT_IN["int"]
        elif node.token.token == TT.REAL:
            node.eval_type = BUILT_IN["real"]
        elif node.token.token == TT.STRING:
            node.eval_type = BUILT_IN["texto"]

    def visit_binopnode(self,node):
        self.visit(node.left)
        self.visit(node.right)
        #Evaluate type of binary
        node.eval_type = self.eval_arit_op(node.left,node.token,node.right)

    def visit_unaryopnode(self,node):
        self.visit(node.operand)
        node.eval_type = node.operand.eval_type


    def visit_assignnode(self,node):
        self.visit(node.left)
        self.visit(node.right)
        if node.left.eval_type != node.right.eval_type:
            self.error(f"Atribuição inválida. incompatibilidade entre os operandos da atribuição [{node.left.eval_type} = {node.right.eval_type}]",node.token)
        self.eval_type = node.right.eval_type
        #Do stuff here

    def visit_statement(self,node):
        #self.visit(node.exp)
        self.visit(node.exp)
        token = node.token.token
        #check if return statement is inside a function
        if token == TT.RETORNA:
            if self.current_scope.name == Analyzer.GLOBAL:
                self.error(f"O comando 'retorna' só pode ser usado dentro de uma função",node.token)
            else:
                function = self.current_scope.enclosing_scope.resolve(self.current_scope.name)
                if function.type.name == BUILT_IN["vazio"]:
                    self.error(f"Expressão de retorno inválida. Procedimentos não podem retornar valores",node.token)
                elif function.type.name != node.exp.eval_type:
                    self.error(f"Expressão de retorno inválida. Esperava-se um retorno do tipo '{function.type.type}'",node.token)


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
        for i,param in enumerate(sym.params.values()):
            if param.type.name != node.fargs[i].eval_type:
                self.error(f"O argumento {i+1} da função {node.id.lexeme} deve ser do tipo '{param.type.type}'",node.id)
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
        if node.index.eval_type != BUILT_IN["int"]:
            self.error(f"O índice de um vector deve ser um inteiro",node.id)
        node.eval_type = sym.type.name
