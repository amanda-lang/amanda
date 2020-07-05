import ast
import sys
from io import StringIO
from amanda.tokens import TokenType as TT
import amanda.ast_nodes as AST
import amanda.semantic as SEM
from amanda.symbols import Tag
import amanda.natives as natives
import amanda.error as error
import modules.functions as bltins_funcs
from amanda.parser import Parser
from amanda.object import *


class Interpreter:

    def __init__(self,src,debug=False):
        self.src = src
        self.memory = Environment()
        self.debug = debug
        #Error handler
        self.handler = error.ErrorHandler.get_handler()
        #If debug is enabled, redirect output to
        #an in memory buffer
        if self.debug:
            self.test_buffer = StringIO()

    def exec(self):
        ''' Method that runs an Amanda script. Errors raised by the
        frontend are handled by an error handler instance'''
        try:
            program = Parser(self.src).parse()
            valid_program = SEM.Analyzer().check_program(program)
            self.init_builtins()
            valid_program.accept(self)
        except error.AmandaError as e:
            if self.debug:
                self.test_buffer.write(str(e).strip())
                sys.exit()
            else:
                self.handler.throw_error(e,self.src)

    def init_builtins(self):
        #Load builtin classes
        for name,builtin in natives.builtin_types.items():
            self.memory.define(name,builtin.get_object())

        #Load builtin functions
        for name,data in bltins_funcs.functions.items():
            self.memory.define(name,NativeFunction(data["function"]))

    #TODO: Track line and col numbers using current node
    def error(self,message,line,col):
        self.handler.throw_error(
            error.RunTime(message,token.line),self.src)

    def exec_program(self,node):
        children = node.children
        for child in children:
            child.accept(self)

    def exec_block(self,node):
        self.run_block(node)

    def run_block(self,node,env=None):
        #Create new env for local scope
        if not env:
            env = Environment(self.memory)
        self.memory = env
        children = node.children
        for child in children:
            child.accept(self)
        self.memory = env.previous


    def exec_vardecl(self,node):
        name = node.name.lexeme
        var_type = node.var_type.tag
        if var_type == Tag.INT:
            self.memory.define(name,0)
        elif var_type == Tag.REAL:
            self.memory.define(name,0.0)
        #TODO: Create real boolean object lol
        elif var_type == Tag.BOOL:
            self.memory.define(name,False)
        elif var_type == Tag.REF:
            self.memory.define(name,AmandaNull())
        else:
            raise NotImplementedError("Object/ref types cannot be used yet")
        assign = node.assign
        if assign:
            assign.accept(self)


    def exec_functiondecl(self,node):
        name = node.name.lexeme
        self.memory.define(name,RTFunction(name,node)) 


    def exec_classdecl(self,node):
        name = node.name.lexeme
        superclass = node.superclass
        if node.superclass:
            superclass = self.memory.resolve(superclass.lexeme)
        #Get blueprint for class
        env = Environment(self.memory)
        members = self.exec_classbody(node.body,env)
        self.memory.define(name,AmaClass(name,members,superclass))
        #print(members)


    def exec_classbody(self,body,env):
        self.memory = env
        for child in body.children:
            child.accept(self)
        self.memory = env.previous
        return env



    def exec_assign(self,node):
        value = node.right.accept(self)
        name = node.left.token.lexeme
        memory = self.memory.resolve_space(name)
        memory.define(name,value)
        return value


    #Helper for evaluating expressions
    def evaluate(self,expr):
        return expr.accept(self)

    def exec_call(self,node):
        args = [self.evaluate(arg) for arg in node.fargs]
        callee = self.evaluate(node.callee) 
        return callee.call(self,args=args)


    def exec_binop(self,node):
        left = node.left.accept(self)
        right = node.right.accept(self)
        op = node.token.token
        if op == TT.PLUS:
            return left + right
        elif op == TT.MINUS:
            return left - right
        elif op == TT.STAR:
            return left * right
        elif op == TT.SLASH:
            if node.eval_type.tag == Tag.REAL:
                return left/right;
            else:
                return left//right;
        elif op == TT.MODULO:
            return left % right;
        elif op == TT.GREATER:
            return left > right
        elif op == TT.LESS:
            return left < right
        elif op == TT.GREATEREQ:
            return left >= right
        elif op == TT.LESSEQ:
            return left <= right
        elif op == TT.NOTEQUAL:
            return left != right
        elif op == TT.DOUBLEEQUAL:
            return left == right
        elif op == TT.E:
            return left and right
        elif op == TT.OU:
            return left or right


    def exec_unaryop(self,node):
        value = node.operand.accept(self)
        if node.token.token == TT.MINUS:
            return -value
        elif node.token.token == TT.NAO:
            return not value
        return value

    def exec_constant(self,node):
        const_type = node.prom_type
        value = node.token.lexeme
        #Check if type conversion is needed
        if not const_type:
            const_type = node.eval_type
            if const_type.tag == Tag.INT:
                return int(value)
            elif const_type.tag == Tag.REAL:
                return float(value)
            elif const_type.tag == Tag.BOOL:
                return True if node.token.token == TT.VERDADEIRO else False
            elif const_type.name == "Texto":
                #Instantiate 'Texto' class
                klass = self.memory.resolve("Texto")
                original = ast.literal_eval(value)
                return klass.call(self,args=[original]) 
            else:
                raise Exception("Undefined constant")
        else:
            if const_type.tag == Tag.REAL:
                return float(node.token.lexeme)
            else:
                raise Exception("No other casts should occur")

    def exec_variable(self,node):
        return self.memory.resolve(node.token.lexeme)

    def exec_set(self,node):
        target = node.target
        obj = self.get_object(target)
        value = self.evaluate(node.expr)
        obj.set(target.member.lexeme,value)
        return value

    def get_object(self,node):
        if isinstance(node,AST.Get):
            obj = self.get_object(node.target)
        else:
            obj = self.evaluate(node)
        #have not implemented NPE yet
        if isinstance(obj,AmandaNull):
            raise NotImplementedError("Null pointer exception not handled yet")
        return obj

    def exec_get(self,node):
        obj = self.get_object(node.target)
        member = obj.get(node.member.lexeme)
        #Use an amanda method to wrap the function
        if isinstance(member,RTFunction):
            return AmandaMethod(obj,member)
        return member


    def exec_eu(self,node):
        return self.memory.resolve("eu")

    def exec_super(self,node):
        return AmandaSuper(
            self.memory.resolve("eu")
        )



    def exec_se(self,node):
        condition = node.condition.accept(self)
        if bool(condition):
            node.then_branch.accept(self)
        else:
            else_branch = node.else_branch
            if else_branch:
                else_branch.accept(self)

    def exec_enquanto(self,node):
        condition = node.condition
        body = node.statement
        while bool(condition.accept(self)):
            self.run_block(body,Environment(self.memory))


    def exec_para(self,node):
        expr = node.expression
        #Get control variable
        var = expr.name.lexeme
        range_exp = expr.range_expr
        #Get range parameters
        start,end= (
                    range_exp.start.accept(self),
                    range_exp.end.accept(self)
                )
        #If there is  no inc
        inc = range_exp.inc
        if not inc:
            inc = -1 if start > end else 1
        else:
            inc = inc.accept(self)
        #Create local mem space for the loop
        body = node.statement
        for control in range(start,end,inc):
            env = Environment(self.memory)
            env.define(var,control)
            self.run_block(body,env)

    def exec_retorna(self,node):
        expr = node.exp
        expr = expr.accept(self) 
        raise ReturnValue(expr)


    def exec_mostra(self,node):
        expr = node.exp
        expr = expr.accept(self) 
        #TODO: Refactor this hack
        if node.exp.eval_type.tag == Tag.BOOL:
            expr = "verdadeiro" if expr else "falso"
        if self.debug:
            print(expr,end=" ",file=self.test_buffer)
        else:
            print(expr)



