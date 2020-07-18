import traceback
from amanda.types import Bool,Indef
from amanda.error import AmandaError,throw_error


#Runtime errors
DIVISION_BY_ZERO = "não pode dividir um número por zero"
INVALID_CONVERSION = "impossível realizar a conversão entre os tipos especificados"

#Exec filename
FILENAME = "<output>"
#Wrapper around print used during execution of
#amanda code
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

def converte(value,ama_type):
    if isinstance(value,Indef):
        value = value.value
    if ama_type == "int" or ama_type == "real":
        try:
            return int(value) if ama_type == "int" else float(value)
        except ValueError as e:
           raise AmandaError(INVALID_CONVERSION,-1)
        except TypeError as e:
           raise AmandaError(INVALID_CONVERSION,-1)
    elif ama_type == "bool":
        return bool(value)
    elif ama_type == "texto":
        return str(value)
    elif ama_type == "indef":
        return Indef(value)
    else:
        NotImplementedError("have not considered other types")

def load_ama_builtins():
    scope = {}
    #Define some builtin objects
    scope["verdadeiro"] = Bool.VERDADEIRO
    scope["falso"] = Bool.FALSO
    scope["printc"] = print_wrapper
    scope["Indef"] = Indef
    scope["converte"] = converte
    return scope

#Checks if exception type can be handled
def can_handle(exception):
    if isinstance(exception,ZeroDivisionError) or\
    isinstance(exception,AmandaError):
        return True
    return False

#TODO: Find a cleaner way to report errors
def get_info_from_tb(exception,error,pycode=None):
    ''' Get info from traceback object based
    on the kind of error it is '''
    tb = exception.__traceback__
    if error == DIVISION_BY_ZERO:
        #Get to the first tb object
        while tb.tb_next:
            tb = tb.tb_next
        return tb.tb_lineno
    elif error == INVALID_CONVERSION:
        for frame_obj,lineno in traceback.walk_tb(tb):
            filename = frame_obj.f_code.co_filename
            ama_lineno = pycode.get_ama_lineno(lineno)
            if ama_lineno is not None and filename == FILENAME:
                return lineno
        return tb.tb_lineno
    else:
        raise NotImplementedError("There should not be other error types")


def handle_exception(exception,pycode):
    ''' Method that gets info about exceptions that
    happens during execution of compiled source and 
    use info to raise an amanda exception'''
    #Get to the first tb object of the trace
    #TODO: Refactor this so that all exceptions thrown
    #equate to amanda errors
    if isinstance(exception,ZeroDivisionError):
        py_lineno = get_info_from_tb(exception,DIVISION_BY_ZERO)
        ama_lineno = pycode.get_ama_lineno(py_lineno)
        assert ama_lineno is not None
        return AmandaError.common_error(
            DIVISION_BY_ZERO,ama_lineno
        )

    elif isinstance(exception,AmandaError):
        msg = exception.message
        py_lineno = get_info_from_tb(exception,msg,pycode)
        ama_lineno = pycode.get_ama_lineno(py_lineno)
        assert ama_lineno is not None
        exception.line = ama_lineno
        return AmandaError.common_error(
            msg,ama_lineno
        )
        
def run_pycode(ama_src,pycode):
    pycode_obj = compile(str(pycode),FILENAME,"exec")
    try:
        exec(pycode_obj,load_ama_builtins())
    except Exception as e:
        if not can_handle(e):
            raise e
        throw_error(handle_exception(e,pycode),ama_src)

