import traceback
from amanda.types import Bool,Indef
from amanda.error import AmandaError,throw_error
from amanda.bltins import bltin_objs

#Exec filename
FILENAME = "<output>"

def get_info_from_tb(exception):
    ''' Get info from traceback object based
    on the kind of error it is '''
    tb = exception.__traceback__
    #Return line number of traceback object
    # that is in compiled file
    while True:
        next_tb = tb.tb_next
        if not next_tb or (
            tb.tb_frame.f_code.co_filename == FILENAME and
            next_tb.tb_frame.f_code.co_filename != FILENAME
        ):
            break
        tb = tb.tb_next
    return tb.tb_lineno

def handle_exception(exception,pycode):
    ''' Method that gets info about exceptions that
    happens during execution of compiled source and 
    uses info to raise an amanda exception'''
    #Get to the first tb object of the trace
    py_lineno = get_info_from_tb(exception)
    ama_lineno = pycode.get_ama_lineno(py_lineno)
    assert ama_lineno is not None
    if type(exception) == ZeroDivisionError:
        return AmandaError.common_error(
            "não pode dividir um número por zero",ama_lineno
        )
    elif type(exception) == AmandaError:
        return AmandaError.common_error(
            exception.message,ama_lineno
        )
    return None
        
def run_pycode(ama_src,pycode):
    pycode_obj = compile(str(pycode),FILENAME,"exec")
    try:
        exec(pycode_obj,bltin_objs)
    except Exception as e:
        ama_error = handle_exception(e,pycode)
        if not ama_error:
            raise e
        throw_error(ama_error,ama_src)

