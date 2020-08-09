from io import StringIO
import sys
from amanda.error import handle_exception
from amanda.bltins import bltin_objs
from amanda.codeobj import CodeObj
from amanda.transpiler import Transpiler
import amanda.semantic as sem
from amanda.error import AmandaError
from amanda.parser import Parser 
import pdb
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
        out_file = "testfile.py"
        py_codeobj = compile(
            self.compiled_program,
            out_file,"exec"
        )
        with open("output.py","w") as output:
            output.write(self.compiled_program)
        #Define runtime scope
        scope = bltin_objs 
        scope["_buffer_"] = self.test_buffer
        try:
            exec(py_codeobj,scope)
        except Exception as e:
            ama_error = handle_exception(e,out_file,self.src_map)
            if not ama_error:
                raise e
            self.test_buffer.write(str(ama_error).strip())
            sys.exit()

    #Generates code to print output to buffer
    def gen_mostra(self,node):
        expression = self.gen(node.exp)
        return f"printc({expression},end=' ',file=_buffer_)"
