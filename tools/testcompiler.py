from io import StringIO
import sys
from amanda.__main__ import load_ama_builtins,handle_exception
from amanda.codeobj import CodeObj
from amanda.transpiler import Transpiler
import amanda.semantic as sem
from amanda.error import AmandaError
from amanda.parser import Parser

#Generates code to print output to buffer
class TestMostra(CodeObj):

    def __init__(self,py_lineno,ama_lineno,expression,buffer):
        super().__init__(py_lineno,ama_lineno)
        self.expression = expression
        self.buffer = buffer

    def __str__(self):
        #Redirect output to test buffer of compiler
        return f"printc({str(self.expression)},end=' ',file={self.buffer})"

#Subclass of the transpiler made for running tests 
class TestCompiler(Transpiler):

    def __init__(self,src):
        super().__init__(src)
        self.test_buffer = StringIO() #Test output goes here
 
    def compile(self):
        try:
            program = Parser(self.src).parse()
            valid_program = sem.Analyzer().check_program(program)
            self.compiled_program = self.gen(valid_program)
        except AmandaError as e:
            self.test_buffer.write(str(e).strip())
            sys.exit()
        return self.compiled_program

    def exec(self):
        #Run compiled source
        if not self.compiled_program:
            self.compile()
        py_codeobj = compile(str(self.compiled_program),"<string>","exec")
        #Define runtime scope
        scope = load_ama_builtins()
        scope["_buffer_"] = self.test_buffer
        try:
            exec(py_codeobj,scope)
        except Exception as e:
            ama_error = handle_exception(e,self.compiled_program)
            self.test_buffer.write(str(ama_error).strip())
            sys.exit()

    def gen_mostra(self,node):
        expression = self.gen(node.exp)
        return TestMostra(
            self.py_lineno,self.ama_lineno,
            expression,"_buffer_"
        )
