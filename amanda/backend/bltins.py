from amanda.backend.types import Bool,Indef,Lista
import amanda.frontend.symbols as symbols
from amanda.frontend.symbols import Type
from amanda.error import AmandaError,throw_error

#Symbols for builtin functions
#used during sem analysis
bltin_symbols = {}
#builtin objects used during 
#code execution
bltin_objs={}

#Runtime errors
INVALID_CONVERSION = "impossível realizar a conversão entre os tipos especificados"


def add_bltin_func(name,obj,return_type,*params):
    ''' Helper that creates a function_symbol and adds it
    to the dict of bltin symbols'''
    return_type = return_type if return_type else Type.VAZIO
    formal_params = {}
    for pname,ptype in params:
        formal_params[pname] = symbols.VariableSymbol(pname,ptype)
    bltin_symbols[name] = symbols.FunctionSymbol(
        name,return_type,
        formal_params
    )
    bltin_objs[name] = obj

    
def print_wrapper(obj,**kwargs):
    if str(obj) == "True":
        print(Bool.VERDADEIRO,**kwargs)
    elif str(obj) == "False":
        print(Bool.FALSO,**kwargs)
    else:
        print(obj,**kwargs)

# Input functions
def leia(prompt):
    ''' Calls the python input method using a prompt
    given by the amanda caller'''
    return input(prompt)

def leia_int(prompt):
    ''' Same as 'leia' but converts the result into
    an int'''
    try:
        return int(input(prompt))
    except ValueError:
        raise AmandaError(INVALID_CONVERSION,-1)

def leia_real(prompt):
    ''' Same as 'leia' but converts the result into
    a float'''
    try:
        return float(input(prompt))
    except ValueError:
        raise AmandaError(INVALID_CONVERSION,-1)

# Type functions
def converte(value,ama_type):
    if isinstance(value,Indef):
        value = value.value
    if ama_type == Type.INT or ama_type == Type.REAL:
        try:
            return int(value) if ama_type == Type.INT else float(value)
        except ValueError as e:
           raise AmandaError(INVALID_CONVERSION,-1)
        except TypeError as e:
           raise AmandaError(INVALID_CONVERSION,-1)
    elif ama_type == Type.BOOL:
        return bool(value)
    elif ama_type == Type.TEXTO:
        return str(value)
    elif ama_type == Type.INDEF:
        return Indef(value)
    else:
        raise NotImplementedError("have not considered other types")

def lista(subtype,size):
    #Returns a list of the desired size
    if size < 0:
        raise AmandaError(
            "O tamanho de uma lista não pode ser um inteiro negativo",
            -1
        )
    inits = {
        "int":0,
        "real":0.0,
        "texto":"",
        "bool":Bool.FALSO,
        "indef":None,
    }
    default = inits.get(str(subtype))
    return Lista(subtype,[default for i in range(size)])

def anexe(list_obj,value):
    list_obj.elements.append(value)

def tipo(indef_obj):
    ''' Returns the type of a 
    value. Useful for 'unwrapping' 
    indef type values'''
    value = indef_obj.value # unwrap value
    if type(value) == Lista:
        return f"[]{value.subtype}"
    types = {
        int : "int",
        float : "real",
        bool : "bool",
        Bool : "bool",
        str : "texto",
    }
    return types.get(type(value))

def tamanho(indef_obj):
    value = indef_obj.value # unwrap value 
    if type(value) == Lista:
        return len(value.elements)
    elif type(value) == str:
        return len(value)
    else:
        return -1
    

#Adding builtins
bltin_objs["verdadeiro"] = Bool.VERDADEIRO
bltin_objs["falso"] = Bool.FALSO
bltin_objs["printc"] = print_wrapper
bltin_objs["Indef"] = Indef
bltin_objs["converte"] = converte
bltin_objs["Type"] = Type

add_bltin_func(
    "leia",leia,
    Type.TEXTO,("mensagem",Type.TEXTO)
)

add_bltin_func(
    "leia_int",leia_int,
    Type.INT,("mensagem",Type.TEXTO)
)

add_bltin_func(
    "leia_real",leia_real,
    Type.REAL,("mensagem",Type.TEXTO)
)

add_bltin_func(
    "tipo",tipo,
    Type.TEXTO,("valor",Type.INDEF)
)

add_bltin_func(
    "tamanho",tamanho,
    Type.INT,("objecto",Type.INDEF)
)

add_bltin_func(
    "lista",lista,
    None
)

add_bltin_func(
    "anexe",anexe,
    None
)
