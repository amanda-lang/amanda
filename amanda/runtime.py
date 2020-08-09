import traceback
from amanda.types import Bool,Indef
from amanda.error import AmandaError,throw_error

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

def handle_exception(exception,src_map):
    ''' Method that gets info about exceptions that
    happens during execution of compiled source and 
    uses info to raise an amanda exception'''
    #Get to the first tb object of the trace
    py_lineno = get_info_from_tb(exception)
    ama_lineno = src_map[py_lineno]
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
        
