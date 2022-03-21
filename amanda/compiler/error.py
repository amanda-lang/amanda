from __future__ import annotations
import sys
from os import path
from typing import Any, Literal, Optional, ClassVar, cast
from dataclasses import dataclass


@dataclass
class AmandaError(Exception):
    # error types
    SYNTAX_ERR: ClassVar[Literal[0]] = 0
    COMMON_ERR: ClassVar[Literal[1]] = 1
    RUNTIME_ERR: ClassVar[Literal[2]] = 2

    err_type: Literal[0, 1, 2]
    fpath: str
    message: str
    line: int
    col: int = -1

    @classmethod
    def syntax_error(
        cls, fpath: str, message: str, line: int, col: int
    ) -> AmandaError:
        return cls(cls.SYNTAX_ERR, fpath, message, line, col)

    @classmethod
    def common_error(cls, fpath: str, message: str, line: int) -> AmandaError:
        return cls(cls.COMMON_ERR, fpath, message, line)

    @classmethod
    def runtime_err(cls, message: str) -> AmandaError:
        return cls(cls.RUNTIME_ERR, "", message, -1)

    def __str__(self) -> str:
        return self.message


def fmt_error(context: str, error: AmandaError) -> str:
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
        err_loc += f": coluna {error.col}"

    err_header = f"""Ficheiro "{filepath}", {err_loc}"""
    err_msg = (
        f"Erro sintático: {error.message}."
        if error.err_type == AmandaError.SYNTAX_ERR
        else f"Erro: {error.message}."
    )

    return f"\n{err_header}\n    {context}\n{err_msg}\n"


def throw_error(err: AmandaError) -> None:
    # Attempt to get error line from file
    filename = path.abspath(err.fpath)
    assert path.isfile(filename), "Invalid filename supplied to error"
    context = None
    with open(filename, "r", encoding="utf8") as f:
        for lineno, line in enumerate(f):
            if lineno == err.line - 1:
                context = line.strip()
                break
    # Line should always be valid because it came from file
    assert context is not None, "Context should always be a line from the file"

    sys.stderr.write(fmt_error(context, err))
    sys.exit()


def get_info_from_tb(exception: Exception, filename: str) -> Any:
    """Get info from traceback object based
    on the kind of error it is"""
    tb: Any = exception.__traceback__
    # Return line number of traceback object
    # that is in compiled file
    while True:
        next_tb: Any = tb.tb_next
        if not next_tb or (
            tb.tb_frame.f_code.co_filename == filename
            and next_tb.tb_frame.f_code.co_filename != filename
        ):
            break
        tb = tb.tb_next
    return tb.tb_lineno


def handle_exception(
    exception: Exception, outfile: str, srcfile: str, src_map: Any
) -> Optional[Exception]:
    """Method that gets info about exceptions that
    happens during execution of compiled source and
    uses info to raise an amanda exception"""
    # Get to the first tb object of the trace
    py_lineno = get_info_from_tb(exception, outfile)
    ama_lineno = src_map[py_lineno]
    if type(exception) == ZeroDivisionError:
        return AmandaError.common_error(
            srcfile, "não pode dividir um número por zero", ama_lineno
        )
    elif type(exception) == AmandaError:
        return AmandaError.common_error(srcfile, exception.message, ama_lineno)
    return None
