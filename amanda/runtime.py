
from amanda.types import Bool,Indef
from amanda.error import AmandaError,throw_error

#Runtime errors
DIVISION_BY_ZERO = "não pode dividir um número por zero"

#Wrapper around print used during execution of
#amanda code
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

def load_ama_builtins():
    scope = {}
    #Define some builtin objects
    scope["verdadeiro"] = Bool.VERDADEIRO
    scope["falso"] = Bool.FALSO
    scope["printc"] = print_wrapper
    scope["Indef"] = Indef
    return scope

#Checks if exception type can be handled
def can_handle(exception):
    if isinstance(exception,ZeroDivisionError):
        return True
    return False

def handle_exception(exception,pycode):
    ''' Method that gets info about exceptions that
    happens during execution of compiled source and 
    use info to raise an amanda exception'''
    #Get to the first tb object of the trace
    tb = exception.__traceback__
    while tb.tb_next:
        tb = tb.tb_next
    ama_lineno = pycode.get_ama_lineno(tb.tb_lineno)
    # REMOVE: this assert here is just for debugging
    assert ama_lineno != None
    if isinstance(exception,ZeroDivisionError):
        return AmandaError.common_error(
            DIVISION_BY_ZERO,ama_lineno
        )

def run_pycode(ama_src,pycode):
    pycode_obj = compile(str(pycode),"<string>","exec")
    try:
        exec(pycode_obj,load_ama_builtins())
    except Exception as e:
        if not can_handle(e):
            raise e
        throw_error(handle_exception(e,pycode),ama_src)

