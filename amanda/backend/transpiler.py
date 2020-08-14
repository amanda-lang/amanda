import sys
import pdb
import keyword
from io import StringIO
import amanda.frontend.symbols as symbols
from amanda.frontend.symbols import Type
import amanda.frontend.ast as ast
import amanda.frontend.semantic as sem
from amanda.error import AmandaError,throw_error
from amanda.frontend.parser import Parser
from amanda.backend.bltins import bltin_symbols



class Transpiler:
    #Var types
    VAR = "VAR"
    FUNC = "FUNC"
    TYPE = "TYPE"

    #Scope names
    GLOBAL = "GLOBAL"
    LOCAL = "LOCAL"

    #Indentation string
    INDENT = "    "

    def __init__(self):
        self.py_lineno = 0  # tracks lineno in compiled python src
        self.ama_lineno = 1 # tracks lineno in input amanda src
        self.depth = -1 # current indent level
        self.global_scope = symbols.Scope(self.GLOBAL)
        self.current_scope = self.global_scope
        self.func_depth = 0 # current func nesting level
        self.scope_depth = 0 # scope nesting level
        self.line_info = {} #Maps py_fileno to ama_fileno
        self.load_builtins()

    def load_builtins(self):
        for name,symbol in bltin_symbols.items():
            if type(symbol) == symbols.VariableSymbol:
                s_info = (name,self.VAR)
            elif type(symbol) == symbols.FunctionSymbol:
                s_info = (name,self.FUNC)
            self.global_scope.define(name,s_info)
        #Add type identifiers
        self.global_scope.define("int",("Type.INT",self.TYPE))
        self.global_scope.define("real",("Type.REAL",self.TYPE))
        self.global_scope.define("bool",("Type.BOOL",self.TYPE))
        self.global_scope.define("texto",("Type.TEXTO",self.TYPE))
        self.global_scope.define("indef",("Type.INDEF",self.TYPE))

    def compile(self,src):
        ''' Method that begins compilation of amanda source.'''
        self.line_info = {} #Reset line info
        try:
            program = Parser(src).parse()
            valid_program = sem.Analyzer().check_program(program)
            compiled_src = self.gen(valid_program)
        except AmandaError as e:
            throw_error(e,src)
        return (compiled_src,self.line_info)

    def bad_gen(self,node):
        raise NotImplementedError(f"Cannot generate code for this node type yet: (TYPE) {type(node)}")

    def gen(self,node,args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self,method_name,self.bad_gen)
        #Update line only if node type has line attribute
        self.ama_lineno =getattr(
            node,"lineno",self.ama_lineno
        )
        if node_class == "block":
            return gen_method(node,args)
        return gen_method(node)

    def gen_program(self,node):
        return self.compile_block(node,[],self.global_scope)
                
    def update_line_info(self):
        self.line_info[self.py_lineno] = self.ama_lineno
        self.py_lineno += 1

    def build_str(self,str_buffer):
        string = str_buffer.getvalue()
        str_buffer.close()
        return string


    def compile_block(self,node,stmts,scope=None):
        #stmts param is a list of stmts
        #node defined here because caller may want
        #to add custom statement to the beginning of
        #a block
        self.depth += 1
        indent_level = self.INDENT * self.depth
        if scope:
            self.current_scope = scope
        else:
            self.current_scope = symbols.Scope(
                self.LOCAL,self.current_scope
            )
        #Newline for header
        self.update_line_info()
        block = StringIO()
        #Add caller stmts to buffer
        for stmt in stmts:
            block.write(indent_level + stmt)
            block.write("\n")
            self.update_line_info()

        for child in node.children:
            block.write(indent_level + self.gen(child))
            block.write("\n")
            self.update_line_info()
        level = self.depth
        self.depth -= 1
        self.current_scope = self.current_scope.enclosing_scope
        #Add pass statement
        if len(block.getvalue()) == 0:
            block.write(f"{indent_level}pass")
            block.write("\n")
            self.update_line_info()
        return self.build_str(block)

    def is_valid_name(self,name):
        ''' Checks whether name is a python keyword, reserved var or
        python builtin object'''
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

    def gen_vardecl(self,node):
        assign = node.assign
        name = node.name.lexeme

        if self.scope_depth >= 1:
            #Defines a new local
            name = self.define_local(
                name,self.current_scope,self.VAR
            )
        else:
            #In global scope
            name = self.define_global(name,self.VAR)

        if assign:
            value = self.gen(assign.right)
        else:
            #Check for initializer
            init_values = {
                "int"  : 0,
                "real" : 0.0,
                "bool" : "falso",
                "texto": '''""'''

            }
            value = init_values.get(str(node.var_type))
        return f"{name} = {value}"

    def gen_functiondecl(self,node):
        name = node.name.lexeme
        func_def = StringIO()
        if self.scope_depth >= 1:
            #Nested function
            name = self.define_local(
                name,self.current_scope,self.FUNC
            )
        else:
            name = self.define_global(name,self.FUNC)
        self.scope_depth += 1
        self.func_depth += 1
        params = []
        scope = symbols.Scope(name,self.current_scope)
        for param in node.params:
            param_name = self.define_local(
                param.name.lexeme,scope,self.VAR
            )
            params.append(param_name)
        params = ",".join(params)
        #Add function signature
        func_def.write(
            f"def {name}({params}):\n"
        )
        #Add function block
        func_def.write(
            self.get_func_block(node.block,scope),
        )
        self.scope_depth -= 1
        self.func_depth -= 1
        return self.build_str(func_def)

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
        names = ",".join(names)
        return f"global {names}"

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
        names = ",".join(names)
        return f"nonlocal {names}"

    def gen_call(self,node):
        args = ",".join([
            str(self.gen(arg)) for arg in node.fargs
        ])
        callee = self.gen(node.callee)
        func_call = f"{callee}({args})"
        return self.gen_expression(func_call,node.prom_type)
    
    def gen_index(self,node):
        target = self.gen(node.target)
        index = self.gen(node.index)
        return f"{target}[{index}]"

    def gen_assign(self,node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        return f"{lhs} = {rhs}"

    def gen_constant(self,node):
        prom_type = node.prom_type
        literal = str(node.token.lexeme)
        return self.gen_expression(literal,prom_type)

    def gen_variable(self,node):
        name = node.token.lexeme
        #If in a function scope
        #and name is defined, return local var name
        info = self.current_scope.get(name)
        if self.depth > 0 and info:
            name = info[0]
        else:
            name = self.current_scope.resolve(name)[0]
        prom_type = node.prom_type
        return self.gen_expression(name,prom_type)

    def gen_binop(self,node):
        lhs = self.gen(node.left)
        rhs = self.gen(node.right)
        operator = node.token.lexeme
        if operator == "e":
            operator = "and"
        elif operator == "ou":
            operator = "or"
        binop  = f"({lhs} {operator} {rhs})"
        # Promote node
        return self.gen_expression(
            binop,node.prom_type
        )

    def gen_unaryop(self,node):
        operator = node.token.lexeme
        operand = self.gen(node.operand)
        if operator == "nao":
            operator = "not"
        unaryop = f"({operator} {operand})"
        return self.gen_expression(
            unaryop,node.prom_type
        )

    
    def gen_converte(self,node):
        expr = self.gen(node.expression)
        new_type = self.current_scope.resolve(
            node.new_type.lexeme
        )[0]
        return f"converte({expr},{new_type})"

    def gen_expression(self,expression,prom_type):
        if prom_type == None:
            return expression
        elif prom_type == Type.INDEF:
            return f"Indef({expression})"
        elif prom_type == Type.REAL:
            return f"float({expression})"
        else:
            raise NotImplementedError("Unexpected prom_type")
    
    def gen_se(self,node):
        if_stmt = StringIO()
        condition = self.gen(node.condition)
        then_branch = self.compile_branch(node.then_branch)
        if_stmt.write(f"if {condition}:\n{then_branch}")
        if node.else_branch:
            indent_level = self.INDENT * self.depth
            else_branch = self.compile_branch(node.else_branch) 
            if_stmt.write(f"\n{indent_level}else:\n{else_branch}")
        return self.build_str(if_stmt)

    def compile_branch(self,block,scope=None):
        self.scope_depth += 1
        if scope is None:
            scope = symbols.Scope(self.LOCAL,self.current_scope)
        branch = self.compile_block(
            block,[],scope
        )
        names = self.get_all_names(scope)
        if len(names) > 0:
            self.update_line_info()
            names = ",".join(names)
            #Add del stmt to end of block
            indent_level = self.INDENT * (self.depth + 1)
            branch += f"{indent_level}del {names}"
        self.scope_depth -= 1
        return branch

    def gen_enquanto(self,node):
        condition = self.gen(node.condition)
        body = self.compile_branch(node.statement)
        return f"while {condition}:\n{body}"

    def gen_para(self,node):
        para_expr = node.expression
        scope = symbols.Scope(self.LOCAL,self.current_scope)
        #Change control var name to local name
        self.scope_depth += 1
        para_expr.name.lexeme = self.define_local(
            para_expr.name.lexeme,
            scope,self.VAR
        )
        self.scope_depth -= 1
        body = self.compile_branch(node.statement,scope)
        expression = self.gen(para_expr)
        return f"for {expression}:\n{body}"
    
    def gen_paraexpr(self,node):
        range_expr = node.range_expr
        name = node.name.lexeme
        start = self.gen(range_expr.start)
        stop = self.gen(range_expr.end)
        inc = f"-1 if {start} > {stop} else 1"
        if range_expr.inc:
            inc = self.gen(range_expr.inc)
        return f"{name} in range({start},{stop},{inc})"
            
    def gen_retorna(self,node):
        expression = self.gen(node.exp)
        return f"return {expression}"

    def gen_mostra(self,node):
        expression = self.gen(node.exp)
        if node.exp.eval_type == Type.VAZIO:
            expression = "vazio"
        return f"printc({expression})"
