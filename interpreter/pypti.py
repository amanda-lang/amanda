import ast
from interpreter.lexer import Lexer
from interpreter.tokens import TokenType as TT
from interpreter.tokens import Token
import interpreter.ast_nodes as AST
import interpreter.symtab as SYM
import interpreter.semantic as SEM
from interpreter.error import RunTimeError


class Enviroment:

    def __init__(self,name,previous=None):
        self.name = name
        self.previous = previous
        self.memory = SYM.SymbolTable() # initialize it's env with it's own global mem space


    def define(self,name,value):
        self.memory.define(name,value)

    def resolve(self,name):
        value = self.memory.resolve(name)
        if value is None and self.previous is not None:
            return self.previous.resolve(name)
        return value

    def __str__(self):
        return str(self.memory)


#Stack that will hold the currently executing Enviroment
class Stack:
    def __init__(self):
        self.stack = []

    def push(self,item):
        self.stack.append(item)

    def pop(self):
        self.stack.pop(-1)

    def peek(self):
        return self.stack[-1]


class Interpreter(AST.Visitor):
    GLOBAL_MEMORY = "GLOBAL"
    #something like null
    NONE_TYPE = "NONE"

    def __init__(self,program):

        self.program = program # Checked AST
        self.call_stack = Stack()
        self.call_stack.push(Enviroment(Interpreter.GLOBAL_MEMORY))

    def interpret(self):
        self.execute(self.program)


    def execute(self,node):
        node_class = type(node).__name__.lower()
        method_name = f"exec_{node_class}"
        visitor_method = getattr(self,method_name,self.generic_exec)
        return visitor_method(node)

    def resolve(self,node):
        node_class = type(node).__name__.lower()
        method_name = f"resolve_{node_class}"
        visitor_method = getattr(self,method_name,self.generic_exec)
        return visitor_method(node)

    def exec_block(self,node):
        for child in node.children:
            self.execute(child)


    def exec_vardeclnode(self,node):
        name = node.id.lexeme
        type = node.type.lexeme
        memory = self.call_stack.peek()
        if type == "int":
            memory.define(name,0)
        elif type == "real":
            memory.define(name,0.0)
        elif type == "texto":
            memory.define(name,"")
        else:
            memory.define(name,Interpreter.NONE_TYPE)
        if node.assign is not None:
            self.execute(node.assign)

    def exec_assignnode(self,node):
        value = self.execute(node.right)
        name = self.resolve(node.left)
        memory = self.call_stack.peek()
        memory.define(name,value)
        return value

    def resolve_expnode(self,node):
        return node.token.lexeme



    def exec_binopnode(self,node):
        left = self.execute(node.left)
        right = self.execute(node.right)
        op = node.token.token
        if op == TT.PLUS:
            return left + right
        elif op == TT.MINUS:
            return left - right
        elif op == TT.STAR:
            return left * right
        elif op == TT.SLASH:
            if node.eval_type == SEM.BUILT_IN["real"]:
                return left/right;
            else:
                return left//right;
        elif op == TT.MODULO:
            return left % right;

    def exec_unaryopnode(self,node):
        value = self.execute(node.operand)
        if node.token.token == TT.MINUS:
            return -value
        return value

    def exec_expnode(self,node):
        if node.token.token == TT.IDENTIFIER:
            return self.call_stack.peek().resolve(node.token.lexeme)
        else:
            type = node.eval_type
            if type == SEM.BUILT_IN["int"]:
                return int(node.token.lexeme)
            elif type == SEM.BUILT_IN["real"]:
                return float(node.token.lexeme)
            elif type == SEM.BUILT_IN["texto"]:
                #format the string lol
                return ast.literal_eval(node.token.lexeme)

    def exec_statement(self,node):
        expr = self.execute(node.exp)
        token = node.token.token
        if token == TT.MOSTRA:
            print(expr,end="\n\n")


    def generic_exec(self):
        pass
