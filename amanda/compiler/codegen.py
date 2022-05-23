import sys
import pdb
from typing import List
from io import StringIO, BytesIO
from enum import Enum, auto
import amanda.compiler.symbols as symbols
from amanda.compiler.type import Type, Kind
import amanda.compiler.ast as ast
from amanda.compiler.tokens import TokenType as TT
from amanda.compiler.error import AmandaError, throw_error
from amanda.compiler import bindump
import struct


OP_SIZE = 8


class OpCode(Enum):
    # Prints TOS
    MOSTRA = 0x00
    # Loads the constant at index specified by arg. Constant becomes TOS.
    LOAD_CONST = auto()
    # All OP instructions use 1 or 2 on the stack add pop them
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
    # Uses TOS to index into TOS - 1. The result is pushed onto the stack
    OP_INDEX_GET = auto()
    # Performs TOS-2[TOS-1] = TOS.
    OP_INDEX_SET = auto()
    # Gets a global variable. The arg is the index to the name of the var on the
    # constant table. Pushes value to the top of the stack
    GET_GLOBAL = auto()
    # Sets global variable. The arg is the index to the name of the var on the
    # constant table. Pops TOS and sets it as the value of the local
    SET_GLOBAL = auto()
    # Sets the pc to the arg.
    JUMP = auto()
    # If TOS == false, sets pc to the args. Pops TOS
    JUMP_IF_FALSE = auto()
    # Gets the value of a non-global variable. The arg is the slot on the stack where the var was stored
    GET_LOCAL = auto()
    # Sets the value of a non-global variable. The arg is the slot on the stack where the var should be stored
    SET_LOCAL = auto()
    # Calls a function. The argument of the op is the number args. Expects function value to be TOS.
    CALL_FUNCTION = auto()
    # Returns  from the caller.
    RETURN = auto()
    # Converts a value into the desired type. Expects TOS to be the target type and TOS-1 the value to convert.
    # Takes an 8-bit argument that changes the 'strictness' of the conversion.
    # 0 (cast): Performs the cast as long as the builtin type can be cast into type.
    # 1 (check cast): Validates if 'interface' type can be cast into the desired type.
    CAST = auto()
    # Builds a string using elements on the stack. 8-bit arg indicates the number of elements
    # on the stack to use
    BUILD_STR = auto()
    # Builds a vec using elements on the stack. 8-bit arg indicates the number of elements
    # on the stack to use.
    BUILD_VEC = auto()
    # Stops execution of the VM. Must always be added to stop execution of the vm
    HALT = 0xFF

    def op_size(self) -> int:
        # Return number of bytes (including args) that each op
        # uses
        num_ops = len(list(OpCode))
        assert (
            num_ops == 32
        ), f"Please update the size of ops after adding a new Op. New size: {num_ops}"
        if self in (
            OpCode.CALL_FUNCTION,
            OpCode.CAST,
            OpCode.BUILD_STR,
            OpCode.BUILD_VEC,
        ):
            return OP_SIZE * 2
        elif self in (
            OpCode.LOAD_CONST,
            OpCode.SET_LOCAL,
            OpCode.GET_LOCAL,
            OpCode.GET_GLOBAL,
            OpCode.SET_GLOBAL,
        ):
            return OP_SIZE * 3
        elif self in (
            OpCode.JUMP,
            OpCode.JUMP_IF_FALSE,
        ):
            return OP_SIZE * 9
        else:
            return OP_SIZE

    def __str__(self) -> str:
        return str(self.value)


class ByteGen:
    """
    Converts an amanda AST into executable bytecode instructions.
    """

    CONST_TABLE = 0
    NAME_TABLE = 1

    def __init__(self):
        self.depth = -1
        self.ama_lineno = 1  # tracks lineno in input amanda src
        self.program_symtab = None
        self.scope_symtab = None
        self.func_locals = {}
        self.const_table = {}
        self.names = {}
        self.labels = {}
        self.ops = []
        self.funcs = []
        self.ip = 0  # Current bytecode offset
        self.lineno = -1
        self.ctx_loop_start = -1
        self.ctx_loop_exit = -1
        self.src_map = {}  # Maps source lines to bytecode offset

    def compile(self, program) -> bytes:
        """Compiles an amanda ast into bytecode ops.
        Returns a serialized object that contains the bytecode and
        other info used at runtime.
        """
        self.program_symtab = self.scope_symtab = program.symbols
        # Define builtin constants
        self.get_table_index("verdadeiro", self.CONST_TABLE)
        self.get_table_index("falso", self.CONST_TABLE)
        sym_types = (
            symbols.VariableSymbol,
            symbols.FunctionSymbol,
            Type,
        )
        for name, symbol in program.symbols.symbols.items():
            if type(symbol) in sym_types:
                self.get_table_index(name, self.NAME_TABLE)

        self.compile_block(program)
        assert self.depth == -1, "A block was not exited in some local scope!"
        # Add halt ops
        self.lineno = 0
        self.append_op(OpCode.HALT)

        ops = BytesIO()
        for op in self.ops:
            ops.write(self.write_op_bytes(op))
        code = ops.getvalue()
        ops.close()

        src_map = []
        for lineno, offsets in self.src_map.items():
            if lineno == 0:
                continue
            # Offset array must contain start and end
            # If it only contains one value, start == end
            if len(offsets) == 1:
                offsets.append(offsets[0])
            assert (
                len(offsets) == 2
            ), f"Found line with offset != 2: {(lineno, offsets)}"
            offsets.append(lineno)
            src_map.extend(offsets)
        module = {
            "entry_locals": len(self.func_locals),
            "constants": list(self.const_table.keys()),
            "names": list(self.names.keys()),
            "ops": code,
            "functions": self.funcs,
            "src_map": src_map,
        }

        return bindump.dumps(module)

    def new_label(self) -> str:
        idx = len(self.labels)
        self.labels[idx] = self.ip  # Placeholder value
        return idx

    def patch_label_loc(self, label) -> str:
        if self.ip > (2 ** 64) - 1:
            raise Exception(
                f"Address of jump ({self.ip}) is too large to be supported by the vm"
            )
        self.labels[label] = self.ip

    def append_op(self, op, *args):
        if self.lineno in self.src_map:
            offsets = self.src_map[self.lineno]
            if len(offsets) < 2:
                offsets.append(self.ip)
            elif offsets[-1] < self.ip:
                offsets[-1] = self.ip
        else:
            self.src_map[self.lineno] = [self.ip]
        self.ip += op.op_size() // OP_SIZE
        self.ops.append((op, args))

    def load_const(self, const):
        self.append_op(
            OpCode.LOAD_CONST, self.get_table_index(const, self.CONST_TABLE)
        )

    def format_u64_arg(self, arg) -> List[int]:
        u64 = struct.pack(">Q", arg)
        return [int(b) for b in u64]

    def format_u16_arg(self, arg):
        high = (arg & 0xFF00) >> 8
        low = arg & 0x00FF
        return high, low

    def write_op_bytes(self, op) -> bytes:
        op, args = op
        # Get patched jump label
        if op in (OpCode.JUMP_IF_FALSE, OpCode.JUMP):
            args = [self.labels[args[0]]]

        if op.op_size() == OP_SIZE:
            return bytes([op.value])
        elif op.op_size() == OP_SIZE * 2:
            return bytes([op.value, args[0]])
        elif op.op_size() == OP_SIZE * 3:
            high, low = self.format_u16_arg(args[0])
            return bytes([op.value, high, low])
        elif op.op_size() == OP_SIZE * 9:
            u64 = self.format_u64_arg(args[0])
            return bytes([op.value, *u64])
        else:
            raise NotImplementedError(
                f"Encoding of op {op.name} has not yet been implemented"
            )

    def disassemble_op(self, op, args) -> str:
        if op in (OpCode.JUMP_IF_FALSE, OpCode.JUMP):
            # get jump address
            args = [self.labels[args[0]]]
        if len(args):
            op_args = " ".join([str(s) for s in args])
            return f"{op_args}"
        else:
            return f""

    def make_debug_asm(self) -> str:
        debug_out = StringIO()
        debug_out.write(f".entry_space: ")
        debug_out.write(str(len(self.func_locals)))
        debug_out.write("\n")
        debug_out.write(".consts\n")
        for const, i in self.const_table.items():
            debug_out.write(f"{i}: {const}\n")
        debug_out.write(".names\n")
        for name, i in self.names.items():
            debug_out.write(f"{i}: {name}\n")
        debug_out.write(".ops\n")

        i = 0
        for op, args in self.ops:
            op_args = self.disassemble_op(op, args)
            debug_out.write(f"{i}: {op.name} {op_args}".strip() + "\n")
            i += op.op_size() // OP_SIZE

        return self.build_str(debug_out)

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
        self.lineno = getattr(node, "lineno", self.lineno)
        if node_class == "block":
            result = gen_method(node, args)
        else:
            result = gen_method(node)
        return result

    def enter_block(self, scope):
        self.depth += 1
        self.scope_symtab = scope

    def exit_block(self):
        self.depth -= 1
        self.scope_symtab = self.scope_symtab.enclosing_scope
        num_locals = len(self.func_locals)

    def compile_block(self, node):
        self.enter_block(node.symbols)
        for child in node.children:
            self.gen(child)
        self.exit_block()

    def get_table_index(self, item, table):
        # TODO: Make load const instruction use 64 bit arg
        tab = self.const_table if table == self.CONST_TABLE else self.names
        if item in tab:
            idx = tab[item]
        else:
            idx = len(tab)
            tab[item] = idx
        assert (
            idx < (2 ** 16) - 1
        ), f"Too many items in a single table for the current file."
        return idx

    def gen_constant(self, node):
        literal = str(node.token.lexeme)
        idx = self.get_table_index(literal, self.CONST_TABLE)
        self.append_op(OpCode.LOAD_CONST, idx)
        self.gen_auto_cast(node.prom_type)

    def load_variable(self, symbol):
        name = symbol.name
        if symbol.is_global:
            self.append_op(OpCode.GET_GLOBAL, self.names[name])
        else:
            self.append_op(OpCode.GET_LOCAL, self.func_locals[symbol.out_id])

    def gen_variable(self, node):
        name = node.token.lexeme
        symbol = node.var_symbol
        # TODO: Make sure that every identifier goes through
        # 'visit_variable' so that symbol attribute can be set
        if symbol is None:
            symbol = self.scope_symtab.resolve(name)
        # TODO: Handle prom_type later
        prom_type = node.prom_type
        var_scope = self.scope_symtab.resolve_scope(name, self.depth)
        self.load_variable(symbol)
        self.gen_auto_cast(prom_type)

    def gen_vardecl(self, node):
        assign = node.assign
        idt = node.name.lexeme
        symbol = self.scope_symtab.resolve(idt)
        # Code that indicates the type of  global
        # to be initialized
        # Find a better way to do this
        init_values = {
            "int": 0,
            "real": "0.0",  # Warning: This might come back to haunt me
            "bool": "falso",
            "texto": "''",
        }
        if assign:
            self.gen_assign(assign)
        else:
            initializer = init_values.get(str(node.var_type), "falso")
            init_idx = self.get_table_index(initializer, self.CONST_TABLE)
            self.append_op(OpCode.LOAD_CONST, init_idx)
            self.set_variable(symbol)

    def set_variable(self, symbol):
        name = symbol.name
        if symbol.is_global:
            var_idx = self.get_table_index(name, self.NAME_TABLE)
            self.append_op(OpCode.SET_GLOBAL, var_idx)
        else:
            local = symbol.out_id
            if local not in self.func_locals:
                idx = len(self.func_locals)
                self.func_locals[local] = idx
            self.append_op(OpCode.SET_LOCAL, self.func_locals[local])

    # TODO: Test whether chained assign still with
    # mixture of normal assigns and index set (Potential bug)
    def gen_assign(self, node):
        expr = node.right
        self.gen(expr)
        # Deal with consecutive assignments
        if isinstance(expr, ast.Assign):
            var_sym = expr.left.var_symbol
            name = expr.left.token.lexeme
            self.load_variable(var_sym)
        var = node.left
        assert isinstance(
            var, ast.Variable
        ), f"Expected ast.Variable, Got node {type(var)}. Line: {var.token}"
        var_sym = var.var_symbol
        self.set_variable(var_sym)

    def gen_unaryop(self, node):
        self.gen(node.operand)
        operator = node.token.token
        if operator == TT.MINUS:
            self.append_op(OpCode.OP_INVERT)
        elif operator == TT.NAO:
            self.append_op(OpCode.OP_NOT)
        else:
            raise NotImplementedError(
                f"OP {node.token.token} has not yet been implemented"
            )
        self.gen_auto_cast(node.prom_type)

    def gen_binop(self, node):
        self.gen(node.left)
        self.gen(node.right)
        operator = node.token.token
        if operator == TT.PLUS:
            self.append_op(OpCode.OP_ADD)
        elif operator == TT.MINUS:
            self.append_op(OpCode.OP_MINUS)
        elif operator == TT.STAR:
            self.append_op(OpCode.OP_MUL)
        elif operator == TT.SLASH:
            self.append_op(OpCode.OP_DIV)
        elif operator == TT.DOUBLESLASH:
            self.append_op(OpCode.OP_FLOORDIV)
        elif operator == TT.MODULO:
            self.append_op(OpCode.OP_MODULO)
        elif operator == TT.E:
            self.append_op(OpCode.OP_AND)
        elif operator == TT.OU:
            self.append_op(OpCode.OP_OR)
        elif operator == TT.DOUBLEEQUAL:
            self.append_op(OpCode.OP_EQ)
        elif operator == TT.NOTEQUAL:
            self.append_op(OpCode.OP_NOTEQ)
        elif operator == TT.GREATER:
            self.append_op(OpCode.OP_GREATER)
        elif operator == TT.GREATEREQ:
            self.append_op(OpCode.OP_GREATEREQ)
        elif operator == TT.LESS:
            self.append_op(OpCode.OP_LESS)
        elif operator == TT.LESSEQ:
            self.append_op(OpCode.OP_LESSEQ)
        else:
            raise NotImplementedError(
                f"OP {node.token.token} has not yet been implemented"
            )
        self.gen_auto_cast(node.prom_type)

    def gen_se(self, node):
        else_branch = node.else_branch
        elsif_branches = node.elsif_branches

        after_if = self.new_label()
        after_then = self.new_label()

        self.gen(node.condition)
        self.append_op(OpCode.JUMP_IF_FALSE, after_then)
        self.compile_block(node.then_branch)
        self.append_op(OpCode.JUMP, after_if)
        self.patch_label_loc(after_then)

        for branch in elsif_branches:
            after_elsif = self.new_label()
            self.gen(branch.condition)
            self.append_op(OpCode.JUMP_IF_FALSE, after_elsif)
            self.compile_block(branch.then_branch)
            self.append_op(OpCode.JUMP, after_if)
            self.patch_label_loc(after_elsif)

        if else_branch:
            self.compile_block(else_branch)

        self.patch_label_loc(after_if)

    def gen_enquanto(self, node):
        after_loop = self.new_label()
        # Set the current loop exit
        loop_exit_state = self.ctx_loop_exit
        self.ctx_loop_exit = after_loop

        loop = self.new_label()
        # Set the current loop start
        loop_start_state = self.ctx_loop_start
        self.ctx_loop_start = loop

        block = node.statement
        self.enter_block(block.symbols)
        # BEGIN LOOP
        self.patch_label_loc(loop)
        self.gen(node.condition)
        self.append_op(OpCode.JUMP_IF_FALSE, after_loop)
        # Block
        for child in block.children:
            self.gen(child)
        self.append_op(OpCode.JUMP, loop)
        # END LOOP
        self.patch_label_loc(after_loop)
        self.exit_block()

        # Restore old loop start
        self.ctx_loop_start = loop_start_state
        # Restore old loop exit
        self.ctx_loop_exit = loop_exit_state

    # NOTE: this statement is very unstable and will be changed
    # NOTE: This is a loop that can only count forward
    def gen_para(self, node):
        para_expr = node.expression
        range_expr = para_expr.range_expr
        scope = node.statement.symbols
        control_var = scope.resolve(para_expr.name.lexeme)
        # BEGIN LOOP
        after_loop = self.new_label()
        loop = self.new_label()
        block = node.statement
        self.enter_block(block.symbols)

        # initializer
        self.gen(range_expr.start)
        self.set_variable(control_var)
        self.patch_label_loc(loop)

        # Condition: while control_var < end
        self.load_variable(control_var)
        self.gen(range_expr.end)
        self.append_op(OpCode.OP_LESS)
        self.append_op(OpCode.JUMP_IF_FALSE, after_loop)
        # Body
        for child in block.children:
            self.gen(child)
        # update: control_var += inc
        self.gen(range_expr.inc)
        self.load_variable(control_var)
        self.append_op(OpCode.OP_ADD)
        self.set_variable(control_var)
        self.append_op(OpCode.JUMP, loop)

        # END LOOP
        self.patch_label_loc(after_loop)
        self.exit_block()
        # raise NotImplementedError()

    def gen_functiondecl(self, node):
        func_symbol = self.scope_symtab.resolve(node.name.lexeme)
        name = func_symbol.name
        name_idx = self.get_table_index(func_symbol.name, self.NAME_TABLE)
        func_end = self.new_label()

        self.append_op(OpCode.JUMP, func_end)
        func_start = self.new_label()

        block = node.block

        prev_func_locals = self.func_locals
        self.func_locals = {}
        for param in func_symbol.params.values():
            local = param.out_id
            idx = len(self.func_locals)
            self.func_locals[local] = idx

        self.enter_block(block.symbols)
        for child in block.children:
            self.gen(child)
        # default return
        self.load_const("falso")
        self.append_op(OpCode.RETURN)
        self.exit_block()
        num_locals = len(self.func_locals)
        self.func_locals = prev_func_locals

        self.patch_label_loc(func_end)
        # TODO: use uint64 for ip and locals
        self.funcs.append(
            {
                "name": name,
                "start_ip": self.labels[func_start],
                "locals": num_locals,
            }
        )

    def gen_call(self, node):
        func = node.symbol
        # Push and store params
        for arg in node.fargs:
            self.gen(arg)
        self.gen(node.callee)
        self.append_op(OpCode.CALL_FUNCTION, len(node.fargs))
        self.gen_auto_cast(node.prom_type)

    def gen_retorna(self, node):
        if node.exp:
            self.gen(node.exp)
        else:
            self.load_const("falso")
        self.append_op(OpCode.RETURN)

    def gen_converta(self, node):
        target_t = node.target.eval_type
        new_t = node.eval_type
        self.gen(node.target)
        # Converting to same type, can ignore this
        # TODO: Do this in sem analysis
        if new_t.kind == target_t.kind or new_t.kind == Kind.TINDEF:
            return
        self.load_variable(new_t)
        arg = 0 if target_t.kind != Kind.TINDEF else 1
        self.append_op(OpCode.CAST, arg)

    def gen_auto_cast(self, prom_type):
        if not prom_type or prom_type.kind != Kind.TREAL:
            return
        self.load_variable(prom_type)
        self.append_op(OpCode.CAST, 0)

    def gen_mostra(self, node):
        self.gen(node.exp)
        self.append_op(OpCode.MOSTRA)

    def gen_indexget(self, node, gen_get=True):
        self.gen(node.target)
        self.gen(node.index)
        if gen_get:
            self.append_op(OpCode.OP_INDEX_GET)

    def gen_indexset(self, node):
        self.gen_indexget(node.index, gen_get=False)
        self.gen(node.value)
        self.append_op(OpCode.OP_INDEX_SET)

    def gen_fmtstr(self, node):
        for part in node.parts:
            self.gen(part)
        self.append_op(OpCode.BUILD_STR, len(node.parts))

    def gen_loopctlstmt(self, node):
        token = node.token
        if token.token == TT.QUEBRA:
            self.append_op(OpCode.JUMP, self.ctx_loop_exit)
        else:
            self.append_op(OpCode.JUMP, self.ctx_loop_start)

    def gen_listliteral(self, node):
        elements = node.elements
        for element in elements:
            self.gen(element)
        self.append_op(OpCode.BUILD_VEC, len(elements))
