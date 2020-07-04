'''
Module responsible for generating python code
from an AST
'''
from io import StringIO
import amanda.symbols as symbols
import amanda.ast_nodes as ast
import amanda.semantic as sem
import amanda.error as error
import sys
from amanda.parser import Parser
import backend.generators as generators
from backend.types import Bool



#This is a big hack
#Put this somewhere else
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

    
class Transpiler:

    VAR = "VAR"
    FUNC = "FUNC"

    def __init__(self,src,debug=False):
        self.src = src
        self.handler = error.ErrorHandler.get_handler()
        self.compiled_src = None
        #used to set indentation in blocks
        self.depth = 0
        self.debug = debug
        self.test_buffer = None
        self.global_scope = symbols.Scope("Main")
        self.current_scope = self.global_scope
        self.func_depth = 0 # Current func nesting level
        if self.debug:
            #If debug is enabled, redirect output to
            #an in memory buffer
            self.test_buffer = StringIO()


    def compile(self):
        ''' Method that runs an Amanda script. Errors raised by the
        frontend are handled by an error handler instance'''
        try:
            program = Parser(self.src).parse()
            valid_program = sem.Analyzer().check_program(program)
            code_objs = self.gen(valid_program)
        except error.AmandaError as e:
            if self.debug:
                self.test_buffer.write(str(e).strip())
                sys.exit()
            self.handler.throw_error(e,self.src)

        str_buffer = StringIO()

        for obj in code_objs:
            print(obj,end="\n\n",file=str_buffer)

        self.compiled_src = str_buffer.getvalue()
        return self.compiled_src

    def exec(self):
        if not self.compiled_src:
            self.compile()
        code = compile(self.compiled_src,"<string>","exec")
        scope = {}
        if self.debug:
        #Add buffer to local dict
            scope["__buffer__"] = self.test_buffer
        #Set verdadeiro e falso
        scope["verdadeiro"] = Bool.VERDADEIRO
        scope["falso"] = Bool.FALSO
        scope["printc"] = print_wrapper
        exec(code,scope)



    def bad_gen(self,node):
        raise NotImplementedError(f"Cannot generate code for this node type yet: (TYPE) {type(node)}")

    def gen(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self,method_name,self.bad_gen)
        if node_class == "block":
            return gen_method(node,args)
        return gen_method(node)


    def gen_program(self,node):
        code_objs = []
        for child in node.children:
            code_objs.append(self.gen(child))
        return code_objs
            
    
    def gen_block(self,node,scope=None):
        self.depth += 1
        gens = []
        #Add global and nonlocal statements
        #to beginning of a function
        if self.func_depth >= 1:
            global_stmt = self.add_globals()
            if global_stmt:
                gens.append(global_stmt)
        if scope:
            self.current_scope = scope
        else:
            self.current_scope = symbols.Scope("local",self.current_scope)
        if self.func_depth > 1:
            non_local = self.add_non_locals()
            if non_local:
                gens.append(non_local)
        for child in node.children:
            gens.append(self.gen(child))
        level = self.depth
        self.depth -= 1
        self.current_scope = self.current_scope.enclosing_scope
        return generators.Block(gens,level)

    def get_names(self,scope):
        names = []
        for name,info in scope.symbols.items():
            if info[1] == self.VAR:
                names.append(info[0])
        return names


    def add_globals(self):
        ''' Adds global statements to
        the beginning of a function'''
        names = self.get_names(self.global_scope)
        if len(names)==0:
            return None
        return generators.Global(names)

    def add_non_locals(self):
        ''' Adds nonlocal statements to
        the beginning of a function'''
        names = []
        scope = self.current_scope.enclosing_scope
        while scope and scope != self.global_scope:
            names = [*names,*self.get_names(scope)]
            scope = scope.enclosing_scope
        if len(names)==0:
            return None
        return generators.NonLocal(names)


    def define_local(self,name,scope,sym_type):
        ''' Defines a new local variable
        for the current_scope. Gives it a
        generic name based on the number of 
        defined local.'''
        num_locals = scope.count()
        reg_name = f"__r{self.func_depth-1}{num_locals}__"
        scope.define(name,(reg_name,sym_type))
        return reg_name


    def gen_vardecl(self,node):
        assign = node.assign
        name = node.name.lexeme
        #Do scope stuff
        if self.func_depth >= 1:
            #Defines a new local
            name = self.define_local(name,self.current_scope,self.VAR)
        else:
            self.current_scope.define(name,(name,self.VAR))
        if assign:
            return self.gen(assign)
        return generators.VarDecl(name,node.var_type.tag)

    #1.Any functions declared inside another
    #should alsob be regarded as a local
    #2. After inner function local params are declared,
    # use the non local stmt to get nonlocal names
    #3. Local names are depth dependent
    #e.g at nesting level 1 __r0__,__r1__
    #at level 2 __r10__,__r11__
    def gen_functiondecl(self,node):
        name = node.name.lexeme
        if self.func_depth >= 1:
            #Nested function
            name = self.define_local(name,self.current_scope,self.FUNC)
        self.func_depth += 1
        self.current_scope.define(name,(name,self.FUNC))
        params = []
        scope = symbols.Scope(name,self.current_scope)
        for param in node.params:
            param_name = self.define_local(param.name.lexeme,scope,self.VAR)
            params.append(param_name)
        gen = generators.FunctionDecl(
            name,
            self.gen(node.block,scope),
            params
        )
        self.func_depth -= 1
        return gen

    def gen_call(self,node) :
        args = [self.gen(arg) for arg in node.fargs]
        return generators.Call(self.gen(node.callee),args)


    def gen_assign(self,node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        return generators.Assign(lhs,rhs)

    
    def gen_constant(self,node):
        prom_type = node.prom_type
        if prom_type:
            if prom_type.tag == symbols.Tag.REAL:
                return float(node.token.lexeme)
        return node.token.lexeme

    def gen_variable(self,node):
        name = node.token.lexeme
        #If in a function scope
        #and name is defined, return local var name
        info = self.current_scope.get(name)
        if self.func_depth > 0 and info:
            return info[0]
        return self.current_scope.resolve(name)[0]

    def gen_binop(self,node):

        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        operator = node.token
        #Workaround for int division
        if operator.lexeme == "/":
            if node.prom_type == None and node.left.eval_type.tag == symbols.Tag.INT:
                operator.lexeme = "//"
        return generators.BinOp(operator.lexeme,lhs,rhs)

    def gen_unaryop(self,node):
        return generators.UnaryOp(
            node.token.lexeme,
            self.gen(node.operand)
        )

    
    def gen_se(self,node):

        gen = generators.Se(
            self.gen(node.condition),
            self.gen(node.then_branch)
        )

        if node.else_branch:
            gen.else_branch = generators.Senao(
                self.gen(node.else_branch),
                self.depth
            )
        return gen

    def gen_enquanto(self,node):
        return generators.Enquanto(
            self.gen(node.condition),
            self.gen(node.statement)
        )


    def gen_para(self,node):
        return generators.Para(
            self.gen(node.expression),
            self.gen(node.statement)
        )

    def gen_paraexpr(self,node):
        range_expr = node.range_expr
        gen = generators.ParaExpr(
            node.name.lexeme,
            self.gen(range_expr.start),
            self.gen(range_expr.end),
        )
        if range_expr.inc:
            gen.inc = self.gen(range_expr.inc)
        return gen
            

    def gen_retorna(self,node):
        return generators.Retorna(self.gen(node.exp))

    def gen_mostra(self,node):
        expression = self.gen(node.exp)
        return generators.Mostra(expression,self.debug)






