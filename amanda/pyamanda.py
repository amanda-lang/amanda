import ast
import sys
from amanda.tokens import TokenType as TT
import amanda.ast_nodes as AST
import amanda.semantic as SEM
from amanda.symbols import Tag
import amanda.error as error
from amanda.parser import Parser
from amanda.object import *


class Interpreter:
    GLOBAL_MEMORY = "GLOBAL"
    LOCAL_MEMORY = "LOCAL"

    def __init__(self,src,debug=False):
        self.src = src
        self.memory = Environment(Interpreter.GLOBAL_MEMORY)
        self.debug = debug

    def run(self):
        program = Parser(self.src).parse()
        valid_program = SEM.Analyzer(self.src).check_program(program)
        valid_program.accept(self)
        
    def error(self,message,token):
        raise error.RunTime(message,token.line)

    def exec_program(self,node):
        children = node.children
        for child in children:
            child.accept(self)

    def exec_block(self,node):
        self.run_block(node)

    def run_block(self,node,env=None):
        #Create new env for local scope
        if not env:
            env = Environment(Interpreter.LOCAL_MEMORY,self.memory)
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
        if node.superclass:
            pass
        #Get blueprint for class
        env = Environment(name,self.memory)
        members = self.exec_classbody(node.body,env)
        self.memory.define(name,AmaClass(name,members))
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
        #Check if type conversion is needed
        if not const_type:
            const_type = node.eval_type.tag
            if const_type == Tag.INT:
                return int(node.token.lexeme)
            elif const_type == Tag.REAL:
                return float(node.token.lexeme)
            elif const_type == Tag.BOOL:
                return True if node.token.token == TT.VERDADEIRO else False
        else:
            if const_type.tag == Tag.REAL:
                return float(node.token.lexeme)
            else:
                raise Exception("No other casts should occur")

    def exec_variable(self,node):
        return self.memory.resolve(node.token.lexeme)

    def exec_get(self,node):
        obj = self.evaluate(node.target)
        
        #Null reference (Not implemented yet)
        if isinstance(obj,AmandaNull):
            raise NotImplementedError("Null pointer exception not handled yet")

        member = obj.members.resolve(node.member.lexeme)

        if isinstance(member,RTFunction):
            return AmandaMethod(obj,member)
        return member



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
        env = Environment(Interpreter.LOCAL_MEMORY,self.memory)
        while bool(condition.accept(self)):
            self.run_block(body,env)


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
            if start > end:
                inc = -1
            else:
                inc = 1
        else:
            inc = inc.accept(self)
        #Create local mem space for the loop
        env = Environment(Interpreter.LOCAL_MEMORY,self.memory)
        body = node.statement
        for control in range(start,end,inc):
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
        print(expr)


