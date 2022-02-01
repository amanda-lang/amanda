import sys
from os import path


class AmandaError(Exception):
    # error types
    SYNTAX_ERR = 0
    OTHER_ERR = 1

    def __init__(self, err_type, fpath, message, line, col=0):
        self.err_type = err_type
        self.fpath = fpath
        self.message = message
        self.line = line
        self.col = col

    @classmethod
    def syntax_error(cls, fpath, message, line, col):
        return cls(cls.SYNTAX_ERR, fpath, message, line, col)

    @classmethod
    def common_error(cls, fpath, message, line):
        return cls(cls.OTHER_ERR, fpath, message, line)

    def __str__(self):
        return self.message


def fmt_error(context: str, error: AmandaError):
    """
    Formats the error message using the error
    object and the context.

    Ex:

    Ficheiro './exemplo.py', linha 5
    Erro sintático: alguma mensagem aqui
        var cao : Animal func
    """
    filepath = path.relpath(error.fpath)
    err_loc = f"linha {error.line}"
    # Show column in case of syntax errors
    if error.err_type == AmandaError.SYNTAX_ERR:
        err_loc += f":coluna {error.col}"

    err_header = f"""Ficheiro "{filepath}", {header}"""
    err_msg = (
        f"Erro sintático: {error.message}"
        if error.err_type == AmandaError.SYNTAX_ERR
        else "Erro: {error.message}"
    )

    return f"\n{err_header}\n{err_msg}\n    {context}\n"


def throw_error(err: AmandaError):
    # Attempt to get error line from file
    filename = path.abspath(err.fpath)
    assert path.isfile(filename), "Invalid filename supplied to error"
    context = None
    with open(filename, "r", encoding="utf8") as f:
        for lineno, line in enumerate(f):
            if lineno == err.line - 1:
                context = line
                break
    # Line should always be valid because it came from file
    assert context is not None, "Context should always be a line from the file"

    sys.stderr.write(fmt_error(context, error))
    sys.exit()


def get_info_from_tb(exception, filename):
    """Get info from traceback object based
    on the kind of error it is"""
    tb = exception.__traceback__
    # Return line number of traceback object
    # that is in compiled file
    while True:
        next_tb = tb.tb_next
        if not next_tb or (
            tb.tb_frame.f_code.co_filename == filename
            and next_tb.tb_frame.f_code.co_filename != filename
        ):
            break
        tb = tb.tb_next
    return tb.tb_lineno


def handle_exception(exception, filename, src_map):
    """Method that gets info about exceptions that
    happens during execution of compiled source and
    uses info to raise an amanda exception"""
    # Get to the first tb object of the trace
    py_lineno = get_info_from_tb(exception, filename)
    ama_lineno = src_map[py_lineno]
    assert ama_lineno is not None
    if type(exception) == ZeroDivisionError:
        return AmandaError.common_error(
            "não pode dividir um número por zero", ama_lineno
        )
    elif type(exception) == AmandaError:
        return AmandaError.common_error(exception.message, ama_lineno)
    return None
