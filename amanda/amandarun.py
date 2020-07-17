#Some stuff that happens during runtime
from amanda.transpiler import Transpiler
from amanda.types import Bool,Indef



#Runtime errors
DIVISION_BY_ZERO = "não pode dividir um número por zero"


#Wrapper around print function used in generated programs
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

def get_builtins():
    scope = {}
    #Set verdadeiro e falso
    scope["verdadeiro"] = Bool.VERDADEIRO
    scope["falso"] = Bool.FALSO
    scope["printc"] = print_wrapper
    scope["Indef"] = Indef
    return scope

def handle_exception(exception,program):
    ''' Method that gets info about exceptions that
    happens during execution of compiled source and 
    use info to raise an amanda exception'''
    #Get to the first tb object of the trace
    tb = exception.__traceback__
    while tb.tb_next:
        tb = tb.tb_next
    py_lineno = tb.tb_lineno
    ama_lineno = program.get_ama_lineno(py_lineno)
    # Make sure that error lineno is not None
    assert ama_lineno != None
    #Throw error
    if isinstance(exception,ZeroDivisionError):
        return AmandaError.common_error(
            Transpiler.DIVISION_BY_ZERO,ama_lineno
        )

    else:
        raise error

def run_amanda_src(src_file):
    transpiler = Transpiler(src_file)
    pycode = transpiler.compile()
    py_codeobj = compile(pycode,"<string>","exec")
    exec(py_codeobj,get_builtins())
    try:
        exec(py_codeobj,get_builtins())
    except Exception as e:
        ama_error = handle_exception(e,transpiler.compiled_program) 
        throw_error(ama_error,self.src)

