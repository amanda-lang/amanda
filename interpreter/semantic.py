from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM

BUILT_IN ={
 "int" : "INTEGER",
 "real": "REAL",
 "string": "STRING",
 "bool":"BOOLEAN",
 "vazio":"VAZIO"
}

arit_types ={
 "INTEGER" : 0,
 "REAL": 1,
 "STRING": 2,
 "BOOLEAN": 3,
 "VAZIO": 4,
 None:4
}

#result of static type computation
#None means illegal operation
type_results = [
    [BUILT_IN["int"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["real"],BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
    [BUILT_IN["vazio"],BUILT_IN["vazio"],BUILT_IN["string"],BUILT_IN["vazio"],BUILT_IN["vazio"]],
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

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope("Global_scope")
        self.init__builtins()

    def init__builtins(self):
        for type in BUILT_IN:
            self.current_scope.define(type,SYM.BuiltInType(BUILT_IN[type]))


    def eval_arit_op(self,opand1,op,opand2):
        print(opand1.token)
        print(opand2.token)
        return type_results[arit_types[opand1.eval_type]][arit_types[opand2.eval_type]]

    def load_symbols(self):
        self.visit(self.program)


    def visit_block(self,node):
        for child in node.children:
            self.visit(child)

    def visit_vardeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
        name = node.id.lexeme
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol)

    def visit_arraydeclnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
        name = node.id.lexeme
        symbol = SYM.ArraySymbol(name,var_type,node.size)
        self.current_scope.define(name,symbol)


    def visit_functiondecl(self,node):
        function_type =  self.current_scope.resolve(node.type.lexeme)
        if function_type == None:
            raise Exception(f"SemanticError: could not resolve function return type '{node.type.lexeme}'")
        name = node.id.lexeme
        if self.current_scope.resolve(name) is not None:
            raise Exception(f"SemanticError: the function '{name}' has already been declared'")
        #push_scope
        self.current_scope = SYM.Scope(name,self.current_scope)
        params = {}
        for param in node.params:
            param_name = param.id.lexeme
            if params.get(name) is not None:
                raise Exception(f"SemanticError: Parameter {param_name} has already been specified")
            param_symbol = self.visit(param)
            params[param_name] = param_symbol

        symbol = SYM.FunctionSymbol(name,function_type,params)
        self.current_scope.enclosing_scope.define(name,symbol)
        self.visit(node.block)
        #leave_scope
        print(self.current_scope)
        self.current_scope = self.current_scope.enclosing_scope

    def visit_paramnode(self,node):
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
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
                raise Exception(f"SemanticError: reference to undeclared identifier '{name}'")
            node.eval_type = sym.type.name
        elif node.token.token == TT.INTEGER:
            node.eval_type = BUILT_IN["int"]
        elif node.token.token == TT.REAL:
            node.eval_type = BUILT_IN["real"]
        elif node.token.token == TT.STRING:
            node.eval_type = BUILT_IN["string"]

        print(f"{node.eval_type} {node.token.lexeme}")


    def visit_binopnode(self,node):
        self.visit(node.left)
        self.visit(node.right)
        #Evaluate type of binary
        node.eval_type = self.eval_arit_op(node.left,node.token,node.right)
        print(f"{node.eval_type} {node.token.lexeme}")

    def visit_unaryopnode(self,node):
        self.visit(node.operand)
        node.eval_type = node.operand.eval_type
        print(f"{node.eval_type} {node.token.lexeme}")



    def visit_assignnode(self,node):
        self.visit(node.left)
        self.visit(node.right)
        #Do stuff here

    def visit_statement(self,node):
        self.visit(node.exp)


    def visit_functioncall(self,node):
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        if sym == None:
            raise Exception(f"SemanticError: reference to undeclared function '{id}'")
        elif not isinstance(sym,SYM.FunctionSymbol):
            raise Exception(f"Trying to call non function '{id}' as function")
        node.eval_type = sym.type.name
        print(f"function: {node.eval_type} {id}")


    def visit_arrayref(self,node):
        id = node.id.lexeme
        sym = self.current_scope.resolve(id)
        if sym == None:
            raise Exception(f"SemanticError: reference to undeclared function '{id}'")
        elif not isinstance(sym,SYM.ArraySymbol):
            raise Exception(f"SemanticError: trying to reference non array '{id}' with index")
        node.eval_type = sym.type.name