from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM

BUILT_IN ={
 "int" : "INTEGER",
 "real": "REAL",
 "string": "STRING"
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

    def init__builtins(self):
        self.current_scope.define("int",SYM.BuiltInType(BUILT_IN["int"]))
        self.current_scope.define("real",SYM.BuiltInType(BUILT_IN["real"]))
        self.current_scope.define("string",SYM.BuiltInType(BUILT_IN["string"]))


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
        if self.current_scope.resolve(name) is not None:
            raise Exception(f"SemanticError: the identifier '{name} has already been declared'")
        symbol = SYM.VariableSymbol(name,var_type)
        self.current_scope.define(name,symbol)

    def visit_arraydeclnode(self,node):
        
