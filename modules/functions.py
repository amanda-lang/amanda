''' Module that contains native functions written in python.
Contains functions for common operations like: input,
output and mathematical functions'''
from amanda.object import NativeFunction
from amanda.symbols import FunctionSymbol
from amanda.symbols import VariableSymbol



def get_func_sym(name,func_type,table,params=[]):
    ''' Creates a function symbol to be used during
    semantic analysis '''
    type_sym = table.resolve(func_type)
    if not type_sym:
        raise Exception("Error ocurred, type not found")
    function = FunctionSymbol(name,type_sym,params={})

    for name,type_sym in params:
        type_sym = table.resolve(type_sym)
        if not type_sym:
            raise Exception("Error ocurred, type not found")

        function.params[name] = VariableSymbol(name,type_sym) 
    return function


#Actual function


def leia(*args):
    ''' Calls the python input method using a prompt
    given by the amanda caller'''
    return input(args[0])

def leia_int(*args):
    ''' Same as 'leia' but converts the result into
    an int'''
    return int(input(args[0]))




functions = {

"leia" : {
     
    "type":"Texto",
    "function":leia,
    "params":[("msg","Texto")]
    },

"leia_int" : {
     
    "type":"int",
    "function":leia_int,
    "params":[("msg","Texto")]
    },
}

