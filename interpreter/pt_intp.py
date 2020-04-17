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


'''
*interpreter class contains everything needed
*to run a PTScript
*it is a high-level interpreter and it is
* not designed for powerful stuff
'''

class PTInterpreter(AST.Visitor):

    def __init__(self,parser):
        self.parser = parser
        self.program = self.parser.parse()
        self.current_scope = SYM.Scope("Global_scope")
        self.init__builtins()

    def init__builtins(self):
        for type in BUILT_IN:
            self.current_scope.define(type,SYM.BuiltInType(BUILT_IN[type]))

    def load_symbols(self):
        self.visit(self.program)


    def visit_block(self,node):
        print("in block")
        for child in node.children:
            self.visit(child)

    def visit_vardeclnode(self,node):
        print("in var_decl")
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
        name = node.id.lexeme
        if self.current_scope.resolve(name) is not None:
            raise Exception(f"SemanticError: the identifier '{name} has already been declared'")
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol)

    def visit_arraydeclnode(self,node):
        print("in array_decl")
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
        name = node.id.lexeme
        if self.current_scope.resolve(name) is not None:
            raise Exception(f"SemanticError: the identifier '{name}' has already been declared'")
        symbol = SYM.ArraySymbol(name,var_type,node.size)
        self.current_scope.define(name,symbol)


    def visit_functiondecl(self,node):
        print("in function_decl")
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
        self.current_scope = self.current_scope.enclosing_scope

    def visit_paramnode(self,node):
        print("visiting param_node")
        var_type = self.current_scope.resolve(node.type.lexeme)
        if var_type == None:
            raise Exception(f"SemanticError: could not resolve type '{node.type.lexeme}'")
        name = node.id.lexeme
        if node.is_array:
            return SYM.ArraySymbol(name,var_type)
        else:
            return SYM.VariableSymbol(name,var_type)
