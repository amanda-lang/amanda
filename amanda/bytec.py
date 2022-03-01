import sys
import pdb
from io import StringIO, BytesIO
from enum import Enum, auto
import amanda.symbols as symbols
from amanda.type import Type, OType
import amanda.ast as ast
from amanda.tokens import TokenType as TT
from amanda.error import AmandaError, throw_error


OP_SIZE = 8


class OpCode(Enum):
    MOSTRA = 0x00
    LOAD_CONST = auto()
    OP_ADD = auto()
    OP_MINUS = auto()
    OP_MUL = auto()
    OP_DIV = auto()
    OP_FLOORDIV = auto()
    OP_MODULO = auto()
    OP_INVERT = auto()
    OP_AND = auto()
    OP_OR = auto()
    OP_NOT = auto()
    OP_EQ = auto()
    OP_NOTEQ = auto()
    OP_GREATER = auto()
    OP_GREATEREQ = auto()
    OP_LESS = auto()
    OP_LESSEQ = auto()
    DEF_GLOBAL = auto()
    GET_GLOBAL = auto()
    SET_GLOBAL = auto()
    JUMP = auto()
    JUMP_IF_FALSE = auto()

    def op_size(self) -> int:
        # Return number of bytes (including args) that each op
        # uses
        if self in (
            OpCode.LOAD_CONST,
            OpCode.GET_GLOBAL,
            OpCode.SET_GLOBAL,
            OpCode.JUMP,
            OpCode.JUMP_IF_FALSE,
        ):
            return OP_SIZE * 3
        elif self == OpCode.DEF_GLOBAL:
            return OP_SIZE * 4
        else:
            return OP_SIZE

    def __str__(self) -> str:
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
        self.const_table = dict()
        self.constants = 0
        self.labels = {}
        self.ops = []
        self.ip = 0  # Amount of instructions written

    def compile(self, program):
        """ Method that begins compilation of amanda source."""
        self.program_symtab = self.scope_symtab = program.symbols
        # Define builtin constants
        self.get_const_index("verdadeiro")
        self.get_const_index("falso")

        py_code = self.gen(program)
        return py_code

    def new_label(self) -> str:
        idx = len(self.labels)
        self.labels[idx] = -1  # Placeholder value
        return idx

    def mark_label_loc(self, label) -> str:
        self.labels[label] = self.ip

    def decode_op(self, op) -> str:
        op, args = op
        if op in (OpCode.JUMP_IF_FALSE, OpCode.JUMP):
            # get jump address
            args = [self.labels[args[0]]]
        if len(args):
            op_args = " ".join([str(s) for s in args])
            return f"{op} {op_args}\n"
        else:
            return f"{op}\n"

    def write_op(self, op, *args):
        self.ip += op.op_size() // OP_SIZE
        self.ops.append((op, args))

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
        self.compile_block(node)
        # Output constants
        program = StringIO()
        program.write(".data\n")
        for const in self.const_table:
            program.write(f"{const}\n")
        program.write(".ops\n")
        for op in self.ops:
            program.write(self.decode_op(op))
        return self.build_str(program)

    def compile_block(self, node):
        # stmts param is a list of stmts
        # node defined here because caller may want
        # to add custom statement to the beginning of
        # a block
        self.depth += 1
        self.scope_symtab = node.symbols
        # Newline for header
        self.update_line_info()
        for child in node.children:
            self.gen(child)
        self.depth -= 1
        self.scope_symtab = self.scope_symtab.enclosing_scope

    def get_const_index(self, constant):
        if constant in self.const_table:
            idx = self.const_table[constant]
        else:
            idx = self.constants
            self.const_table[constant] = idx
            self.constants += 1
        return idx

    def gen_constant(self, node):
        literal = str(node.token.lexeme)
        idx = self.get_const_index(literal)
        self.write_op(OpCode.LOAD_CONST, idx)
        self.update_line_info()

    def gen_variable(self, node):
        name = node.token.lexeme
        symbol = node.var_symbol
        # TODO: Make sure that every identifier goes through
        # 'visit_variable' so that symbol attribute can be set
        if symbol is None:
            symbol = self.scope_symtab.resolve(name)
        expr = symbol.out_id
        # TODO: Handle prom_type later
        prom_type = node.prom_type
        self.write_op(OpCode.GET_GLOBAL, self.const_table[expr])

    def gen_vardecl(self, node):
        assign = node.assign
        idt = node.name.lexeme
        symbol = self.scope_symtab.resolve(idt)
        # Code that indicates the type of  global
        # to be initialized
        init_values = {
            "int": 0,
            "real": 1,
            "bool": 2,
            "texto": 3,
        }
        # DEF_GLOBAL takes two args, the index to the name of the var,  table
        # and the type of the var so that appropriate value may be chosen
        # as an initializer
        id_idx = self.get_const_index(symbol.out_id)
        self.write_op(
            OpCode.DEF_GLOBAL, id_idx, init_values[str(node.var_type)]
        )
        # TODO: Optimize this
        if assign:
            self.gen(assign)

    def gen_assign(self, node):
        # Push value onto the stack
        self.gen(node.right)
        var = node.left
        assert isinstance(var, ast.Variable)
        var_idx = self.get_const_index(var.token.lexeme)
        # SET_GLOBAL takes one args, the index to the name of the var,  table
        # And sets it to the value at the top of the constant table
        self.write_op(OpCode.SET_GLOBAL, var_idx)

    def gen_unaryop(self, node):
        self.gen(node.operand)
        operator = node.token.token
        if operator == TT.MINUS:
            self.write_op(OpCode.OP_INVERT)
        elif operator == TT.NAO:
            self.write_op(OpCode.OP_NOT)
        else:
            raise NotImplementedError(
                f"OP {node.token.token} has not yet been implemented"
            )

    def gen_binop(self, node):
        self.gen(node.left)
        self.gen(node.right)
        operator = node.token.token
        if operator == TT.PLUS:
            self.write_op(OpCode.OP_ADD)
        elif operator == TT.MINUS:
            self.write_op(OpCode.OP_MINUS)
        elif operator == TT.STAR:
            self.write_op(OpCode.OP_MUL)
        elif operator == TT.SLASH:
            self.write_op(OpCode.OP_DIV)
        elif operator == TT.DOUBLESLASH:
            self.write_op(OpCode.OP_FLOORDIV)
        elif operator == TT.MODULO:
            self.write_op(OpCode.OP_MODULO)
        elif operator == TT.E:
            self.write_op(OpCode.OP_AND)
        elif operator == TT.OU:
            self.write_op(OpCode.OP_OR)
        elif operator == TT.DOUBLEEQUAL:
            self.write_op(OpCode.OP_EQ)
        elif operator == TT.NOTEQUAL:
            self.write_op(OpCode.OP_NOTEQ)
        elif operator == TT.GREATER:
            self.write_op(OpCode.OP_GREATER)
        elif operator == TT.GREATEREQ:
            self.write_op(OpCode.OP_GREATEREQ)
        elif operator == TT.LESS:
            self.write_op(OpCode.OP_LESS)
        elif operator == TT.LESSEQ:
            self.write_op(OpCode.OP_LESSEQ)
        else:
            raise NotImplementedError(
                f"OP {node.token.token} has not yet been implemented"
            )

    def gen_se(self, node):
        else_branch = node.else_branch

        self.gen(node.condition)
        after_if = self.new_label()
        after_then = self.new_label()
        if not else_branch:
            self.write_op(OpCode.JUMP_IF_FALSE, after_if)
        else:
            self.write_op(OpCode.JUMP_IF_FALSE, after_then)

        self.compile_block(node.then_branch)
        if else_branch:
            # then branch can't fall into else branch
            self.write_op(OpCode.JUMP, after_if)
            self.mark_label_loc(after_then)
            self.compile_block(else_branch)

        if node.elsif_branches:
            raise NotImplementedError("Cannot yet gen else of elsif branches")

        self.mark_label_loc(after_if)

    def gen_mostra(self, node):
        self.gen(node.exp)
        self.write_op(OpCode.MOSTRA)
