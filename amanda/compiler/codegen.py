import sys
import pdb
from io import StringIO, BytesIO
from enum import Enum, auto
import amanda.compiler.symbols as symbols
from amanda.compiler.type import Type, OType
import amanda.compiler.ast as ast
from amanda.compiler.tokens import TokenType as TT
from amanda.compiler.error import AmandaError, throw_error
from amanda.compiler import bindump


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
    # DEF_GLOBAL takes two args, the index to the name of the var,  table
    # and the type of the var so that appropriate value may be chosen
    # as an initializer
    DEF_GLOBAL = auto()
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
    # Creates a new function. Expects the const table index of the name of the function (TOS2),
    # address of the first instruction to be on the stack (TOS)
    # and the number of locals in the function
    MAKE_FUNCTION = auto()
    # Calls a function. The argument of the op is the number args. Expects function value to be TOS.
    CALL_FUNCTION = auto()
    # Returns  from the caller.
    RETURN = auto()

    def op_size(self) -> int:
        # Return number of bytes (including args) that each op
        # uses
        if self in (
            OpCode.LOAD_CONST,
            OpCode.SET_LOCAL,
            OpCode.GET_LOCAL,
            OpCode.GET_GLOBAL,
            OpCode.SET_GLOBAL,
            OpCode.JUMP,
            OpCode.JUMP_IF_FALSE,
        ):
            return OP_SIZE * 3
        elif self == OpCode.DEF_GLOBAL:
            return OP_SIZE * 4
        elif self in (OpCode.CALL_FUNCTION,):
            return OP_SIZE * 2
        else:
            return OP_SIZE

    def __str__(self) -> str:
        return str(self.value)


class ByteGen:
    """
    Converts an amanda AST into executable bytecode instructions.
    """

    def __init__(self):
        self.depth = -1
        self.ama_lineno = 1  # tracks lineno in input amanda src
        self.program_symtab = None
        self.scope_symtab = None
        self.func_locals = {}
        self.const_table = {}
        self.constants = 0
        self.labels = {}
        self.ops = []
        self.ip = 0  # Current bytecode offset

    def compile(self, program) -> bytes:
        """ Method that begins compilation of amanda source."""
        self.program_symtab = self.scope_symtab = program.symbols
        # Define builtin constants
        self.get_const_index("verdadeiro")
        self.get_const_index("falso")
        for name, symbol in program.symbols.symbols.items():
            if isinstance(symbol, symbols.VariableSymbol) or isinstance(
                symbol, symbols.FunctionSymbol
            ):
                self.get_const_index(name)

        self.compile_block(program)
        assert self.depth == -1, "A block was not exited in some local scope!"

        ops = BytesIO()
        for op in self.ops:
            ops.write(self.write_op_bytes(op))
        code = ops.getvalue()
        ops.close()

        src_object = {
            "entry_locals": len(self.func_locals),
            "constants": [str(s) for s in self.const_table],
            "ops": code,
        }

        return bindump.dumps(src_object)
        return code

    def new_label(self) -> str:
        idx = len(self.labels)
        self.labels[idx] = self.ip  # Placeholder value
        return idx

    def patch_label_loc(self, label) -> str:
        # TODO: Make jump instructions use 64 bit args
        if self.ip > (2 ** 16) - 1:
            raise Exception(
                f"Address of jump ({self.ip}) is too large to be supported by the vm"
            )
        self.labels[label] = self.ip

    def append_op(self, op, *args):
        self.ip += op.op_size() // OP_SIZE
        self.ops.append((op, args))

    def load_const(self, const):
        self.append_op(OpCode.LOAD_CONST, self.get_const_index(const))

    def format_u16_arg(self, arg):
        high = (arg & 0xFF00) >> 8
        low = arg & 0x00FF
        return high, low

    def write_op_bytes(self, op) -> bytes:
        op, args = op
        if op in (OpCode.JUMP_IF_FALSE, OpCode.JUMP):
            args = [self.labels[args[0]]]
        if op in (
            OpCode.LOAD_CONST,
            OpCode.SET_LOCAL,
            OpCode.GET_LOCAL,
            OpCode.GET_GLOBAL,
            OpCode.SET_GLOBAL,
            OpCode.JUMP,
            OpCode.JUMP_IF_FALSE,
        ):
            high, low = self.format_u16_arg(args[0])
            return bytes([op.value, high, low])
        elif op == OpCode.DEF_GLOBAL:
            high, low = self.format_u16_arg(args[0])
            return bytes([op.value, high, low, args[1]])
        elif op.op_size() == OP_SIZE * 2:
            return bytes([op.value, args[0]])
        elif op.op_size() == OP_SIZE:
            return bytes(op.value)
        else:
            raise NotImplementedError(
                f"Encoding of op {op} has not yet been implemented"
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
        debug_out.write(".data\n")
        for const, i in self.const_table.items():
            debug_out.write(f"{i}: {const}\n")
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
        # Update line only if node type has line attribute
        self.ama_lineno = getattr(node, "lineno", self.ama_lineno)
        if node_class == "block":
            return gen_method(node, args)
        return gen_method(node)

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

    def get_const_index(self, constant):
        if constant in self.const_table:
            idx = self.const_table[constant]
        else:
            idx = self.constants
            self.const_table[constant] = idx
            self.constants += 1
        assert (
            idx < 2 ** 16
        ), f"Too many constants found in program. VM cannot handle them"
        return idx

    def gen_constant(self, node):
        literal = str(node.token.lexeme)
        idx = self.get_const_index(literal)
        self.append_op(OpCode.LOAD_CONST, idx)
        self.update_line_info()

    def load_variable(self, symbol):
        name = symbol.name
        if symbol.is_global:
            self.append_op(OpCode.GET_GLOBAL, self.const_table[name])
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

    def gen_vardecl(self, node):
        assign = node.assign
        idt = node.name.lexeme
        symbol = self.scope_symtab.resolve(idt)
        # Code that indicates the type of  global
        # to be initialized
        # Find a better way to do this
        init_values = {
            "int": 0,
            "real": 1,
            "bool": 2,
            "texto": 3,
        }
        # Def global vars
        if symbol.is_global:
            id_idx = self.get_const_index(idt)
            if assign:
                self.gen(assign)
            else:
                self.append_op(
                    OpCode.DEF_GLOBAL, id_idx, init_values[str(node.var_type)]
                )
            return
        # Def local var
        if assign:
            self.gen_assign(assign)
        else:
            node_type = init_values[str(node.var_type)]
            initializer = {0: 0, 1: 0.0, 2: "falso", 3: "''"}[node_type]
            init_idx = self.get_const_index(initializer)
            self.append_op(OpCode.LOAD_CONST, init_idx)
            self.set_variable(symbol)

    def set_variable(self, symbol):
        name = symbol.name
        if symbol.is_global:
            var_idx = self.get_const_index(name)
            self.append_op(OpCode.SET_GLOBAL, var_idx)
        else:
            local = symbol.out_id
            if local not in self.func_locals:
                idx = len(self.func_locals)
                self.func_locals[local] = idx
            self.append_op(OpCode.SET_LOCAL, self.func_locals[local])

    def gen_assign(self, node):
        expr = node.right
        self.gen(expr)
        # Deal with consecutive assignments
        if isinstance(expr, ast.Assign):
            var_sym = expr.left.var_symbol
            name = expr.left.token.lexeme
            self.load_variable(var_sym)
        var = node.left
        assert isinstance(var, ast.Variable)
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
        loop = self.new_label()
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
        name = func_symbol.out_id
        name_idx = self.get_const_index(func_symbol.name)
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
        # Push args for function data
        self.load_const(name_idx)
        self.load_const(self.labels[func_start])
        self.load_const(num_locals)

        self.append_op(OpCode.MAKE_FUNCTION)
        self.set_variable(func_symbol)

    def gen_call(self, node):
        func = node.symbol
        # Push and store params
        for arg in node.fargs:
            self.gen(arg)
        self.gen(node.callee)
        self.append_op(OpCode.CALL_FUNCTION, len(node.fargs))

    def gen_retorna(self, node):
        if node.exp:
            self.gen(node.exp)
        else:
            self.load_const("falso")
        self.append_op(OpCode.RETURN)

    def gen_mostra(self, node):
        self.gen(node.exp)
        self.append_op(OpCode.MOSTRA)
