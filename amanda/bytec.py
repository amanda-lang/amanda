import sys
import pdb
from io import StringIO, BytesIO
from enum import Enum, auto
import amanda.symbols as symbols
from amanda.type import Type, OType
import amanda.ast as ast
from amanda.error import AmandaError, throw_error


class OpCode(Enum):
    MOSTRA = 0x00
    LOAD_CONST = 0x01

    def __str__(self):
        return str(self.value)


class ByteGen:
    """
    Writes amanda bytecode to a file, to later be executed on
    the vm.
    The compiled files have the following structure:
    //DATA SECTION - where constants are placed
    //OPS SECTION - Where actual bytecode ops are
    Example
    .data:
    0:'string'
    .ops:
    0 0
    """

    def __init__(self):
        self.depth = -1
        self.ama_lineno = 1  # tracks lineno in input amanda src
        self.program_symtab = None
        self.scope_symtab = None
        self.const_table = []
        self.constants = 0
        self.ops = StringIO()

    def compile(self, program):
        """ Method that begins compilation of amanda source."""
        self.program_symtab = self.scope_symtab = program.symbols
        py_code = self.gen(program)
        return py_code

    def bad_gen(self, node):
        raise NotImplementedError(
            f"Cannot generate code for this node type yet: (TYPE) {type(node)}"
        )

    def update_line_info(self):
        self.ama_lineno += 1

    def build_str(self, str_buffer):
        string = str_buffer.getvalue()
        str_buffer.close()
        return string

    def gen(self, node, args=None):
        node_class = type(node).__name__.lower()
        method_name = f"gen_{node_class}"
        gen_method = getattr(self, method_name, self.bad_gen)
        # Update line only if node type has line attribute
        self.ama_lineno = getattr(node, "lineno", self.ama_lineno)
        if node_class == "block":
            return gen_method(node, args)
        return gen_method(node)

    def gen_program(self, node):
        ops = self.compile_block(node)
        # Output constants
        data = StringIO()
        data.write(".data\n")
        for idx, const in enumerate(self.const_table):
            data.write(f"{const}\n")
        data.write(".ops\n")
        return self.build_str(data) + self.build_str(self.ops)

    def compile_block(self, node):
        # stmts param is a list of stmts
        # node defined here because caller may want
        # to add custom statement to the beginning of
        # a block
        self.depth += 1
        self.scope_symtab = node.symbols
        # Newline for header
        self.update_line_info()
        block = StringIO()
        for child in node.children:
            self.gen(child)
        self.depth -= 1
        self.scope_symtab = self.scope_symtab.enclosing_scope
        return self.build_str(block)

    def gen_constant(self, node):
        literal = str(node.token.lexeme)
        idx = self.constants
        self.const_table.append(literal)
        self.constants += 1
        self.ops.write(f"{OpCode.LOAD_CONST} {idx}\n")
        self.update_line_info()

    def gen_mostra(self, node):
        self.gen(node.exp)
        self.ops.write(f"{OpCode.MOSTRA}\n")
