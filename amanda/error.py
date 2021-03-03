import sys


class AmandaError(Exception):
    def __init__(self, message, line, col=0):
        self.message = message
        self.line = line
        self.col = col

    @classmethod
    def syntax_error(cls, message, line, col):
        instance = cls(message, line)
        instance.message = f"\nErro sintático na linha {line}: {message}.\n"
        return instance

    @classmethod
    def common_error(cls, message, line):
        instance = cls(message, line)
        instance.message = f"\nErro na linha {line}: {message}.\n"
        return instance

    def __str__(self):
        return self.message


def get_context(error, source):
    """
    Gets the context of an error. the context
    is just just an array with a certain number of lines
    from the source file.
    """
    context = []
    source.seek(0)
    # number of lines to use as context
    n_lines = 2
    # range to get
    lower_bound = error.line - n_lines
    upper_bound = error.line

    for count, line in enumerate(source):
        # get lines that are within context range
        if count + 1 >= lower_bound:
            fmt_line = "| ".join([str(count + 1), line.strip()])
            context.append(fmt_line)
            if count + 1 == upper_bound:
                source.close()
                break
    return context


def fmt_error(context, error):
    """
    Formats the error message using the error
    object and the context.

    Ex:

    Erro sintático na linha 5: alguma mensagem aqui
    ------------------------------------------------

    3| var char : texto
    4| var lobo : Animal
    5| var cao : Animal func
                        ^^^^
    """
    err_marker = "^"
    message = str(error)
    fmt_message = "\n".join([message, "-" * len(message)])
    fmt_context = "\n".join(context)
    # Doing this weird stuff to get the indicator '^' under the loc
    err_line = context[len(context) - 1].split("|")
    code_len = len(err_line[1].strip())
    padding = len(err_line[0]) + 2
    # find the size and create the error indicator
    indicator = err_marker * code_len
    indicator = indicator.rjust(padding + code_len)
    return f"{fmt_message}\n{fmt_context}\n{indicator}\n"


def throw_error(error, source):
    """
    Method that deals with errors thrown at different stages of the program.

    param: source - io object where the program is being read from
    Ex:

    Erro sintático na linha 5: alguma mensagem aqui
    ------------------------------------------------

    3| var char : texto
    4| var lobo : Animal
    5| var cao : Animal func
       ^^^^^^^^^^^^^^^^^^^^^
    """
    context = get_context(error, source)
    sys.stderr.write(fmt_error(context, error))
    source.close()
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
