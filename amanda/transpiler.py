'''
Module responsible for generating python code
from an AST
'''
from io import StringIO
import sys
import keyword
import amanda.symbols as symbols
import amanda.ast_nodes as ast
import amanda.semantic as sem
from amanda.error import AmandaError,throw_error
from amanda.parser import Parser
import amanda.codeobj as codeobj
from amanda.types import Bool


#TODO: Find a cleaner way to run tests on classes that execute code
#TODO: Make line tracking cleaner

#This is a big hack
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

    
class Transpiler:
    #Var types
    VAR = "VAR"
    FUNC = "FUNC"

    #Scope names
    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"

    #Error messages
    DIVISION_BY_ZERO = "não pode dividir um número por zero"

    def __init__(self,src,debug=False):
        self.src = StringIO(src.read())
        self.py_lineno = 0  # tracks lineno in compiled python src
        self.ama_lineno = 1 # tracks lineno in input amanda src
        self.compiled_program = None
        self.depth = -1 # current indent level
        self.debug = debug 
        self.global_scope = symbols.Scope(self.GLOBAL)
        self.current_scope = self.global_scope
        self.func_depth = 0 # current func nesting level
        self.scope_depth = 0 # scope nesting level
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
            self.compiled_program = self.gen(valid_program)
        except AmandaError as e:
            if self.debug:
                self.test_buffer.write(str(e).strip())
                sys.exit()
            throw_error(e,self.src)
        return str(self.compiled_program)

    def exec(self):
        if not self.compiled_program:
            self.compile()
        py_codeobj = compile(str(self.compiled_program),"<string>","exec")
        scope = {}
        if self.debug:
        #Add buffer to local dict
            scope[codeobj.TEST_BUFFER] = self.test_buffer
        #Set verdadeiro e falso
        scope["verdadeiro"] = Bool.VERDADEIRO
        scope["falso"] = Bool.FALSO
        scope["printc"] = print_wrapper
        try:
            exec(py_codeobj,scope)
        except Exception as e:
            ama_error = self.handle_error(e)
            if self.debug:
                self.test_buffer.write(str(ama_error).strip())
                sys.exit()
            throw_error(ama_error,self.src)

    def handle_error(self,e):
        ''' Method that gets info about exceptions that
        happens during execution of compiled source and 
        use info to raise an amanda exception'''
        #Get to the first tb object of the trace
        tb = e.__traceback__
        while tb.tb_next:
            tb = tb.tb_next
        py_lineno = tb.tb_lineno
        ama_lineno = self.compiled_program.get_ama_lineno(py_lineno)
        # REMOVE: this assert here is just for debugging
        assert ama_lineno != None
            #Throw error
        if isinstance(e,ZeroDivisionError):
            ama_error = AmandaError.common_error(self.DIVISION_BY_ZERO,ama_lineno)
            return ama_error
        else:
            raise error


    def bad_gen(self,node):
        raise NotImplementedError(f"Cannot generate code for this node type yet: (TYPE) {type(node)}")

    def gen(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self,method_name,self.bad_gen)
        #Update line only if node type has line attribute
        self.ama_lineno = getattr(getattr(node,"token",None),"line",self.ama_lineno)
        if node_class == "block":
            return gen_method(node,args)
        return gen_method(node)


    def gen_program(self,node):
        return self.compile_block(node,[],self.global_scope)
            
    
    def compile_block(self,node,stmts,scope=None):
        #stmts param is a list of stmts
        #node defined here because caller may want
        #to add custom statement to the beginning of
        #a block
        self.depth += 1
        if scope:
            self.current_scope = scope
        else:
            self.current_scope = symbols.Scope(self.LOCAL,self.current_scope)
        #Break for block header
        py_lineno = self.py_lineno
        self.py_lineno += 1
        for child in node.children:
            instr = self.gen(child)
            #Increase line count
            self.py_lineno += 1
            stmts.append(instr)
        level = self.depth
        self.depth -= 1
        self.current_scope = self.current_scope.enclosing_scope
        if len(stmts) == 0:
            stmts.append(codeobj.Pass(self.py_lineno,self.ama_lineno))
            self.py_lineno += 1
        return codeobj.Block(py_lineno,self.ama_lineno,stmts,level)

    def is_valid_name(self,name):
        ''' Checks whether name is a python keyword, reserved var or
        python builtin method'''
        return not (keyword.iskeyword(name) or 
             (name.startswith("_") and name.endswith("_")) or
             name in globals().get("__builtins__")
        )
        

    def define_local(self,name,scope,sym_type):
        ''' Defines a new local variable
        for the current_scope. Gives it a
        generic name based on the number of 
        defined local.'''
        reg_name = f"_r{self.scope_depth-1}{scope.count()}_"
        scope.define(name,(reg_name,sym_type))
        return reg_name

    def define_global(self,name,name_type):
        ''' Defines a new global variable. Variable id is changed
        in case of invalid identifiers'''
        real_id = name
        if not self.is_valid_name(name):
            real_id = f"_g{self.global_scope.count()}_"
        self.global_scope.define(name,(real_id,name_type))
        return real_id

    #TODO: Add check for names that use python keywords
    # and reserved transpiler identifiers
    def gen_vardecl(self,node):
        assign = node.assign
        name = node.name.lexeme
        if self.scope_depth >= 1:
            #Defines a new local
            name = self.define_local(name,self.current_scope,self.VAR)
        else:
            #In global scope
            name = self.define_global(name,self.VAR)
        if assign:
            return self.gen(assign)
        return codeobj.VarDecl(self.py_lineno,self.ama_lineno,name,node.var_type)

    def gen_functiondecl(self,node):
        name = node.name.lexeme
        if self.scope_depth >= 1:
            #Nested function
            name = self.define_local(name,self.current_scope,self.FUNC)
        else:
            name = self.define_global(name,self.FUNC)
        self.scope_depth += 1
        self.func_depth += 1
        params = []
        scope = symbols.Scope(name,self.current_scope)
        for param in node.params:
            param_name = self.define_local(param.name.lexeme,scope,self.VAR)
            params.append(param_name)
        gen = codeobj.FunctionDecl(
            self.py_lineno,self.ama_lineno,name,
            self.get_func_block(node.block,scope),
            params
        )
        self.scope_depth -= 1
        self.func_depth -= 1
        return gen

    #1.Any functions declared inside another
    #should also be regarded as a local
    #2. After inner function local params are declared,
    # use the non local stmt to get nonlocal names
    #3. Local names are depth dependent
    #e.g at nesting level 1 __r0__,__r1__
    #at level 2 __r10__,__r11__
    def get_func_block(self,block,scope):
        #Add global and nonlocal statements
        #to beginning of a function
        stmts=[]
        if self.func_depth >= 1:
            global_stmt = self.gen_global_stmt()
            if global_stmt:
                stmts.append(global_stmt)
        if self.func_depth > 1:
            non_local = self.gen_nonlocal_stmt(scope)
            if non_local:
                stmts.append(non_local)
        return self.compile_block(block,stmts,scope)

    def get_names(self,scope):
        names = []
        for name,info in scope.symbols.items():
            if info[1] == self.VAR:
                names.append(info[0])
        return names

    def get_all_names(self,scope):
        names = []
        for name,info in scope.symbols.items():
            #Lol don't know why i have to do it
            if info[0] in names:
                continue
            names.append(info[0])
        return names

    def gen_global_stmt(self):
        ''' Adds global statements to
        the beginning of a function'''
        names = self.get_names(self.global_scope)
        if len(names)==0:
            return None
        py_lineno = self.py_lineno
        self.py_lineno += 1
        return codeobj.Global(py_lineno,self.ama_lineno,names)

    def gen_nonlocal_stmt(self,scope):
        ''' Adds nonlocal statements to
        the beginning of a function'''
        names = []
        scope = scope.enclosing_scope
        while scope and scope != self.global_scope:
            names += self.get_names(scope) 
            scope = scope.enclosing_scope
        if len(names)==0:
            return None
        py_lineno = self.py_lineno
        self.py_lineno += 1
        return codeobj.NonLocal(py_lineno,self.ama_lineno,names)

    def gen_call(self,node):
        args = [self.gen(arg) for arg in node.fargs]
        return codeobj.Call(self.py_lineno,self.ama_lineno,self.gen(node.callee),args)

    def gen_assign(self,node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        return codeobj.Assign(self.py_lineno,self.ama_lineno,lhs,rhs)

    def gen_constant(self,node):
        prom_type = node.prom_type
        if prom_type:
            if prom_type == symbols.Type.REAL:
                return float(node.token.lexeme)
        return node.token.lexeme

    def gen_variable(self,node):
        name = node.token.lexeme
        #If in a function scope
        #and name is defined, return local var name
        info = self.current_scope.get(name)
        if self.depth > 0 and info:
            return info[0]
        return self.current_scope.resolve(name)[0]

    def gen_binop(self,node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        operator = node.token
        #Workaround for int division
        if operator.lexeme == "/":
            if node.prom_type == None and node.left.eval_type == symbols.Type.INT:
                operator.lexeme = "//"
        return codeobj.BinOp(self.py_lineno,self.ama_lineno,operator.lexeme,lhs,rhs)

    def gen_unaryop(self,node):
        return codeobj.UnaryOp(
            self.py_lineno,self.ama_lineno,
            node.token.lexeme,
            self.gen(node.operand)
        )

    
    def gen_se(self,node):

        self.scope_depth += 1
        scope = symbols.Scope(self.LOCAL,self.current_scope)
        gen = codeobj.Se(
            self.py_lineno,self.ama_lineno,
            self.gen(node.condition),
            self.compile_block(node.then_branch,[],scope)
        )
        self.scope_depth -=1
        names = self.get_all_names(scope)
        if len(names) > 0:
            self.unbind_locals(scope,gen.then_branch,names)

        if node.else_branch:
            self.scope_depth += 1
            else_scope = symbols.Scope(self.LOCAL,self.current_scope)
            gen.else_branch = codeobj.Senao(
                self.py_lineno,self.ama_lineno,
                self.compile_block(node.else_branch,[],else_scope),
                self.depth
            )
            self.scope_depth -= 1
            names = self.get_all_names(else_scope)
            if len(names) > 0:
                self.unbind_locals(else_scope,gen.else_branch.then_branch,names)

        return gen
    
    def unbind_locals(self,scope,body,names):
        py_lineno = self.py_lineno
        self.py_lineno += 1
        body.instructions.append(codeobj.Del(py_lineno,self.ama_lineno,names))


    def gen_enquanto(self,node):
        self.scope_depth += 1
        scope = symbols.Scope(self.LOCAL,self.current_scope)
        gen = codeobj.Enquanto(
            self.py_lineno,self.ama_lineno,
            self.gen(node.condition),
            self.compile_block(node.statement,[],scope)
        )
        names = self.get_all_names(scope)
        if len(names) > 0:
            self.unbind_loop_locals(gen.body,names)
        self.scope_depth -=1
        return gen



    def gen_para(self,node):
        self.scope_depth += 1
        #Define control var
        scope = symbols.Scope(self.LOCAL,self.current_scope)
        para_expr = node.expression
        control_var = para_expr.name.lexeme
        #Change control var name to local name
        para_expr.name.lexeme = self.define_local(control_var,scope,self.VAR)
        gen = codeobj.Para(
            self.py_lineno,self.ama_lineno,
            self.gen(para_expr),
            self.compile_block(node.statement,[],scope)
        )
        #Delete names
        names = self.get_all_names(scope)
        if len(names) > 0:
            self.unbind_loop_locals(gen.body,names)
        self.scope_depth -=1
        return gen
    
    def unbind_loop_locals(self,body,names):
        py_lineno = self.py_lineno
        self.py_lineno += 1
        body.del_stmt = codeobj.Del(py_lineno,self.ama_lineno,names)
        

    def gen_paraexpr(self,node):
        range_expr = node.range_expr
        name = node.name.lexeme
        gen = codeobj.ParaExpr(
            self.py_lineno,self.ama_lineno,name,
            self.gen(range_expr.start),
            self.gen(range_expr.end),
        )
        if range_expr.inc:
            gen.inc = self.gen(range_expr.inc)
        return gen
            

    def gen_retorna(self,node):
        return codeobj.Retorna(
            self.py_lineno,self.ama_lineno,
            self.gen(node.exp)
        )

    def gen_mostra(self,node):
        expression = self.gen(node.exp)
        return codeobj.Mostra(self.py_lineno,self.ama_lineno,expression,self.debug)






