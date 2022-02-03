from amanda.objects import Indef, Lista, BaseClass, Nulo
import amanda.symbols as symbols
from amanda.type import OType, Type
from amanda.error import AmandaError

# Symbols for builtin functions
# used during sem analysis
bltin_symbols = {}
# builtin objects used during
# code execution
bltin_objs = {}

# Runtime errors
INVALID_CONVERSION = (
    "impossível realizar a conversão entre os tipos especificados"
)


def ama_builtin(*params, returns=None):
    """Decorator that adds a function as an ama_builtin"""

    def decorator(func):
        """Helper that creates a function_symbol and adds it
        to the dict of bltin symbols"""
        name = func.__name__
        return_type = returns if returns else Type(OType.TVAZIO)
        formal_params = {}
        for pname, ptype in params:
            formal_params[pname] = symbols.VariableSymbol(pname, ptype)
        bltin_symbols[name] = symbols.FunctionSymbol(
            name, return_type, formal_params
        )
        bltin_objs[name] = func
        return func

    return decorator


# Input functions
@ama_builtin(("mensagem", Type(OType.TTEXTO)), returns=Type(OType.TTEXTO))
def leia(prompt):
    """Calls the python input method using a prompt
    given by the amanda caller"""
    return input(prompt)


@ama_builtin(("mensagem", Type(OType.TTEXTO)), returns=Type(OType.TINT))
def leia_int(prompt):
    """Same as 'leia' but converts the result into
    an int"""
    try:
        return int(input(prompt))
    except ValueError:
        raise AmandaError.runtime_err(INVALID_CONVERSION)


@ama_builtin(("mensagem", Type(OType.TTEXTO)), returns=Type(OType.TREAL))
def leia_real(prompt):
    """Same as 'leia' but converts the result into
    a float"""
    try:
        return float(input(prompt))
    except ValueError:
        raise AmandaError.runtime_err(INVALID_CONVERSION)


def converte(value, type_class):
    if isinstance(value, Indef):
        value = value.value
    if type(type_class) == Lista:
        if type(value) != Lista or value.subtype != type_class.subtype:
            raise AmandaError.runtime_err(INVALID_CONVERSION)
        return value
    try:
        if type_class == int and type(value) == bool:
            raise ValueError
        return type_class(value)
    except ValueError as e:
        raise AmandaError.runtime_err(INVALID_CONVERSION)
    except TypeError as e:
        raise AmandaError.runtime_err(INVALID_CONVERSION)


@ama_builtin()
def lista(subtype, size):
    # Returns a list of the desired size
    if size < 0:
        raise AmandaError.runtime_err(
            "O tamanho de uma lista não pode ser um inteiro negativo"
        )
    inits = {int: 0, float: 0.0, str: "", bool: False}
    default = inits.get(subtype)
    return Lista(subtype, [default for i in range(size)])


@ama_builtin()
def matriz(subtype, rows, cols):
    # Returns a list of the desired size
    return Lista(subtype, [lista(subtype, cols) for i in range(rows)])


@ama_builtin()
def anexe(list_obj, value):
    list_obj.elements.append(value)


# TODO: Test this for user defined types
@ama_builtin(("valor", Type(OType.TINDEF)), returns=Type(OType.TTEXTO))
def tipo(indef_obj):
    """Returns the type of a
    value as a string. Useful for 'unwrapping'
    indef type values"""
    value = indef_obj.value  # unwrap value
    if type(value) == Lista:
        return f"[]{value.subtype}"
    types = {
        int: "int",
        float: "real",
        bool: "bool",
        str: "texto",
    }
    return types.get(type(value))


@ama_builtin(("objecto", Type(OType.TINDEF)), returns=Type(OType.TINT))
def tamanho(indef_obj):
    value = indef_obj.value  # unwrap value
    if type(value) == Lista:
        return len(value.elements)
    elif type(value) == str:
        return len(value)
    else:
        return -1


def print_wrapper(obj, **kwargs):
    if str(obj) == "True":
        print("verdadeiro", **kwargs)
    elif str(obj) == "False":
        print("falso", **kwargs)
    else:
        print(obj, **kwargs)


@ama_builtin(("objecto", Type(OType.TINDEF)), returns=None)
def escreva(indef_obj):
    obj = str(indef_obj.value)
    print_wrapper(obj, end="")


@ama_builtin(("objecto", Type(OType.TINDEF)), returns=None)
def escrevaln(indef_obj):
    obj = str(indef_obj.value)
    print_wrapper(obj)


# Aliases for objects
bltin_objs["verdadeiro"] = True
bltin_objs["falso"] = False
bltin_objs["printc"] = print_wrapper
bltin_objs["converte"] = converte
bltin_objs["real"] = float
bltin_objs["texto"] = str
bltin_objs["indef"] = Indef
bltin_objs["Lista"] = Lista
bltin_objs["nulo"] = Nulo()
bltin_objs["_BaseClass_"] = BaseClass
