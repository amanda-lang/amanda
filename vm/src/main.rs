use std::collections::HashMap;
use std::convert::From;
use std::fmt;
use std::fmt::{Display, Formatter};
use std::{env, fs, path::Path};

#[repr(u8)]
#[derive(Debug, Clone)]
enum OpCode {
    Mostra,
    LoadConst,
    OpAdd,
    OpMinus,
    OpMul,
    OpDiv,
    OpFloorDiv,
    OpModulo,
    OpInvert,
    OpAnd,
    OpOr,
    OpNot,
    OpEq,
    OpNotEq,
    OpGreater,
    OpGreaterEq,
    OpLess,
    OpLessEq,
    DefGlobal,
    GetGlobal,
    SetGlobal,
    Jump,
    JumpIfFalse,
    SetupBlock,
    ExitBlock,
    GetLocal,
    SetLocal,
    Halt = 255,
}

//TODO: Find better way to do this
impl From<&u8> for OpCode {
    fn from(number: &u8) -> Self {
        let ops = [
            OpCode::Mostra,
            OpCode::LoadConst,
            OpCode::OpAdd,
            OpCode::OpMinus,
            OpCode::OpMul,
            OpCode::OpDiv,
            OpCode::OpFloorDiv,
            OpCode::OpModulo,
            OpCode::OpInvert,
            OpCode::OpAnd,
            OpCode::OpOr,
            OpCode::OpNot,
            OpCode::OpEq,
            OpCode::OpNotEq,
            OpCode::OpGreater,
            OpCode::OpGreaterEq,
            OpCode::OpLess,
            OpCode::OpLessEq,
            OpCode::DefGlobal,
            OpCode::GetGlobal,
            OpCode::SetGlobal,
            OpCode::Jump,
            OpCode::JumpIfFalse,
            OpCode::SetupBlock,
            OpCode::ExitBlock,
            OpCode::GetLocal,
            OpCode::SetLocal,
        ];
        if *number == 0xff {
            OpCode::Halt
        } else {
            ops[*number as usize].clone()
        }
    }
}

macro_rules! arith_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            Const::F64(_) => Const::F64($left.take_float() $op $right.take_float()),
            Const::Int(_) => Const::Int($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        };
    };
}

macro_rules! comp_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            Const::F64(_) => Const::Bool($left.take_float() $op $right.take_float()),
            Const::Int(_) => Const::Bool($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        };
    };
}

macro_rules! eq_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            Const::Int(_) => Const::Bool($left.take_int() $op $right.take_int()),
            Const::F64(_) => Const::Bool($left.take_float() $op $right.take_float()),
            Const::Bool(_) => Const::Bool($left.take_bool() $op $right.take_bool()),
            Const::Str(_) => Const::Bool($left.take_str() $op $right.take_str()),
            _ => unimplemented!("Operand type not supported"),
        };
    };
}

#[derive(Debug)]
enum Const {
    Str(String),
    Int(i64),
    F64(f64),
    Bool(bool),
    None,
}

impl Const {
    fn is_float(&self) -> bool {
        if let Const::F64(_) = self {
            true
        } else {
            false
        }
    }

    fn take_float(&self) -> f64 {
        match self {
            Const::F64(float) => *float,
            Const::Int(int) => *int as f64,
            _ => panic!("Value is not a float"),
        }
    }

    fn take_int(&self) -> i64 {
        match self {
            Const::Int(int) => *int,
            Const::F64(float) => *float as i64,
            _ => panic!("Value is not an int"),
        }
    }

    fn take_str(&self) -> &str {
        if let Const::Str(string) = self {
            string
        } else {
            panic!("Value is not an str")
        }
    }

    fn take_bool(&self) -> bool {
        if let Const::Bool(val) = self {
            *val
        } else {
            panic!("Value is not a bool")
        }
    }

    fn is_str(&self) -> bool {
        if let Const::Str(_) = self {
            true
        } else {
            false
        }
    }

    fn is_bool(&self) -> bool {
        if let Const::Bool(_) = self {
            true
        } else {
            false
        }
    }

    fn is_int(&self) -> bool {
        if let Const::Int(_) = self {
            true
        } else {
            false
        }
    }

    fn binop(left: Self, op: OpCode, right: Self) -> Self {
        let res_type = if left.is_float() || right.is_float() {
            Const::F64(0.0)
        } else if left.is_int() && right.is_int() {
            Const::Int(0)
        } else if left.is_bool() && right.is_bool() {
            Const::Bool(false)
        } else if left.is_str() && right.is_str() {
            Const::Str(String::from(""))
        } else {
            unimplemented!("Error is not implemented")
        };
        match op {
            OpCode::OpAdd => arith_ops!(res_type, left, +, right),
            OpCode::OpMinus => arith_ops!(res_type, left, -, right),
            OpCode::OpMul => arith_ops!(res_type, left, *, right),
            OpCode::OpModulo => arith_ops!(res_type, left, %, right),
            OpCode::OpDiv => Const::F64(left.take_float() / right.take_float()),
            OpCode::OpFloorDiv => Const::Int(left.take_int() / right.take_int()),
            OpCode::OpAnd => Const::Bool(left.take_bool() && right.take_bool()),
            OpCode::OpOr => Const::Bool(left.take_bool() || right.take_bool()),
            OpCode::OpEq => eq_ops!(res_type, left, ==, right),
            OpCode::OpNotEq => eq_ops!(res_type, left, !=,  right),
            OpCode::OpGreater => comp_ops!(res_type, left, >, right),
            OpCode::OpGreaterEq => comp_ops!(res_type, left, >=, right),
            OpCode::OpLess => comp_ops!(res_type, left, <, right),
            OpCode::OpLessEq => comp_ops!(res_type, left, <=, right),
            _ => unimplemented!("Op {:?} has not yet been implemented", op),
        }
    }
}

impl Clone for Const {
    fn clone(&self) -> Self {
        match self {
            Const::Str(string) => Const::Str(String::clone(string)),
            Const::Int(int) => Const::Int(*int),
            Const::F64(float) => Const::F64(*float),
            Const::Bool(val) => Const::Bool(*val),
            Const::None => Const::None,
        }
    }
}

impl Display for Const {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match self {
            Const::Str(string) => write!(f, "{}", string),
            Const::Int(integer) => write!(f, "{}", integer),
            Const::F64(float) => {
                if float.fract() == 0.0 {
                    return write!(f, "{}.0", float);
                }
                write!(f, "{}", float)
            }
            Const::Bool(val) => {
                let val_str = if *val { "verdadeiro" } else { "falso" };
                write!(f, "{}", val_str)
            }
            Const::None => panic!("None value should not be printed"),
        }
    }
}

#[derive(Debug)]
struct Program {
    constants: Vec<Const>,
    ops: Vec<u8>,
}

type ConstIndex = u16;

fn push_u16_arg(vec: &mut Vec<u8>, arg: u16) {
    let high: u8 = ((arg & 0xFF00) >> 8) as u8;
    let low: u8 = (arg & 0x00FF) as u8;
    vec.push(high);
    vec.push(low);
}

fn parse_asm(src: String) -> Program {
    let lines: Vec<&str> = src.split("\n").collect();
    let mut constants = Vec::new();
    let mut ops: Vec<u8> = Vec::new();
    let mut idx = 0;
    //If data section is present, load constants
    if lines[idx].trim() == ".data" {
        idx = 1;
        for line in &lines[idx..] {
            if line.trim() == ".ops" {
                break;
            }
            let constant: &str = line.trim();
            if constant == "verdadeiro" || constant == "falso" {
                let bool_val = if constant == "falso" { false } else { true };
                constants.push(Const::Bool(bool_val));
                idx += 1;
                continue;
            }
            let maybe_int = constant.parse::<i64>();
            let maybe_float = constant.parse::<f64>();
            if maybe_int.is_ok() {
                constants.push(Const::Int(maybe_int.unwrap()))
            } else if maybe_float.is_ok() {
                constants.push(Const::F64(maybe_float.unwrap()))
            } else {
                let slice: &str = if &constant[..1] == "\"" || &constant[..1] == "\'" {
                    &constant[1..constant.len() - 1]
                } else {
                    constant
                };
                constants.push(Const::Str(String::from(slice)))
            }
            idx += 1;
        }
    }
    if lines[idx].trim() == ".ops" {
        idx += 1;
        for line in &lines[idx..] {
            if line as &str == "" {
                break;
            }
            let instr: Vec<&str> = line.split(" ").collect();
            match &instr[0].trim().parse::<u8>() {
                Ok(op) => match OpCode::from(op) {
                    OpCode::Mostra
                    | OpCode::OpAdd
                    | OpCode::OpMinus
                    | OpCode::OpMul
                    | OpCode::OpDiv
                    | OpCode::OpFloorDiv
                    | OpCode::OpModulo
                    | OpCode::OpInvert
                    | OpCode::OpAnd
                    | OpCode::OpOr
                    | OpCode::OpNot
                    | OpCode::OpEq
                    | OpCode::OpNotEq
                    | OpCode::OpGreater
                    | OpCode::OpGreaterEq
                    | OpCode::OpLess
                    | OpCode::OpLessEq
                    | OpCode::ExitBlock => ops.push(*op as u8),
                    OpCode::DefGlobal => {
                        /* Defines a new global variable
                         * takes two args, the index to the name of the var on the
                         * constant table
                         * and the type of the var so that appropriate value may be chosen
                         * as an initializer
                         */
                        ops.push(*op as u8);
                        let id_idx = instr[1].parse::<ConstIndex>().unwrap();
                        let init_type = instr[2].parse::<u8>().unwrap();
                        push_u16_arg(&mut ops, id_idx);
                        ops.push(init_type);
                    }
                    //TODO: Make jump instructions use 64 bit args
                    OpCode::LoadConst
                    | OpCode::SetupBlock
                    | OpCode::SetGlobal
                    | OpCode::GetGlobal
                    | OpCode::SetLocal
                    | OpCode::GetLocal
                    | OpCode::JumpIfFalse
                    | OpCode::Jump => {
                        ops.push(*op as u8);
                        let arg = instr[1].parse::<ConstIndex>().unwrap();
                        push_u16_arg(&mut ops, arg);
                    }
                    _ => unimplemented!(
                        "Cannot not parse OpCode {:?}, maybe it hasn't been implemented yet",
                        op
                    ),
                },
                _ => panic!("Invalid syntax in amasm file"),
            };
        }
    }
    //Add halt opcode
    ops.push(OpCode::Halt as u8);
    Program { constants, ops }
}

struct AmaVM<'a> {
    program: Vec<u8>,
    constants: &'a Vec<Const>,
    pc: usize,
    stack: Vec<Const>,
    sp: isize,
    bp: isize,
    globals: HashMap<&'a str, Const>,
}

impl<'a> AmaVM<'a> {
    pub fn from_program(program: &'a mut Program) -> Self {
        AmaVM {
            program: program.ops.clone(),
            constants: &program.constants,
            pc: 0,
            stack: Vec::new(),
            sp: -1,
            bp: -1,
            globals: HashMap::new(),
        }
    }

    fn op_push(&mut self, value: Const) {
        self.sp += 1;
        let stack_size = self.stack.len() as isize;
        if self.sp == stack_size {
            self.stack.push(value);
        } else if self.sp < stack_size {
            self.stack[self.sp as usize] = value;
        }
    }

    fn op_pop(&mut self) -> Const {
        let stack_size = (self.stack.len() - 1) as isize;
        if self.sp == stack_size {
            self.sp -= 1;
            self.stack.pop().unwrap()
        } else if self.sp < stack_size {
            let idx = self.sp;
            self.sp -= 1;
            self.stack[idx as usize].clone()
        } else {
            panic!("Undefined VM State. sp larger than stack!");
        }
    }

    fn get_byte(&mut self) -> u8 {
        self.pc += 1;
        self.program[self.pc]
    }

    fn get_u16_arg(&mut self) -> u16 {
        ((self.get_byte() as u16) << 8) | self.get_byte() as u16
    }

    pub fn run(&mut self) {
        loop {
            let op = self.program[self.pc];
            match OpCode::from(&op) {
                OpCode::LoadConst => {
                    let idx = self.get_u16_arg();
                    self.op_push(Const::clone(&self.constants[idx as usize]));
                }
                OpCode::Mostra => println!("{}", self.op_pop()),
                //Binary Operations
                OpCode::OpAdd
                | OpCode::OpMinus
                | OpCode::OpMul
                | OpCode::OpDiv
                | OpCode::OpFloorDiv
                | OpCode::OpModulo
                | OpCode::OpAnd
                | OpCode::OpOr
                | OpCode::OpEq
                | OpCode::OpNotEq
                | OpCode::OpGreater
                | OpCode::OpGreaterEq
                | OpCode::OpLess
                | OpCode::OpLessEq => {
                    let right = self.op_pop();
                    let left = self.op_pop();
                    self.op_push(Const::binop(left, OpCode::from(&op), right))
                }
                OpCode::OpInvert | OpCode::OpNot => {
                    let operand = self.op_pop();
                    let op = OpCode::from(&op);
                    if let OpCode::OpInvert = op {
                        match operand {
                            Const::Int(num) => self.op_push(Const::Int(-num)),
                            Const::F64(num) => self.op_push(Const::F64(-num)),
                            _ => panic!("Fatal error!"),
                        };
                    } else {
                        if let Const::Bool(val) = operand {
                            self.op_push(Const::Bool(!val));
                        } else {
                            panic!("Value should always be a bool");
                        }
                    }
                }
                OpCode::DefGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let init_type = self.get_byte();
                    let initializer = match init_type {
                        0 => Const::Int(0),
                        1 => Const::F64(0.0),
                        2 => Const::Bool(false),
                        3 => Const::Str(String::from("")),
                        _ => unimplemented!("Unknown type initializer"),
                    };
                    let id = self.constants[id_idx].take_str();
                    self.globals.insert(id, initializer);
                }
                OpCode::GetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id = self.constants[id_idx].take_str();
                    //#TODO: Do not use clone
                    self.op_push(self.globals.get(id).unwrap().clone());
                }
                OpCode::SetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id = self.constants[id_idx].take_str();
                    let value = self.op_pop();
                    self.globals.insert(id, value);
                }
                OpCode::Jump => {
                    let addr = self.get_u16_arg() as usize;
                    self.pc = addr;
                    continue;
                }
                OpCode::JumpIfFalse => {
                    /*
                     * Jumps if the top of the stack is false
                     * Pops the stack
                     * */
                    let addr = self.get_u16_arg() as usize;
                    let value = self.op_pop();
                    if let Const::Bool(false) = value {
                        self.pc = addr;
                        continue;
                    }
                }
                OpCode::SetupBlock => {
                    let num_locals = self.get_u16_arg();
                    self.stack.reserve(num_locals as usize);
                    self.bp = self.sp + 1;
                    for _ in 0..num_locals {
                        self.op_push(Const::None);
                    }
                }
                OpCode::ExitBlock => {
                    self.sp = self.bp - 1;
                    self.bp = -1;
                }
                OpCode::GetLocal => {
                    let idx = self.get_u16_arg() as usize + self.bp as usize;
                    //#TODO: Do not use clone
                    self.op_push(self.stack[idx].clone());
                }
                OpCode::SetLocal => {
                    let idx = self.bp as usize + self.get_u16_arg() as usize;
                    self.stack[idx] = self.op_pop();
                }
                OpCode::Halt => break,
                _ => unimplemented!(
                    "Cannot not execute OpCode {:?}, maybe it hasn't been implemented yet",
                    op
                ),
            }
            self.pc += 1;
        }
    }

    fn print_debug_info(&self) {
        println!("[IP]: {}", self.pc);
        println!("[SP]: {}", self.sp);
        println!("[BP]: {}", self.bp);
        println!("[STACK]: {:?}", self.stack);
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Por favor especifique o ficheiro a ser executado");
        return;
    }
    let file = Path::new(&args[1]);
    let src = String::from_utf8(fs::read(file).unwrap()).unwrap();
    let mut program = parse_asm(src);
    let mut vm = AmaVM::from_program(&mut program);
    vm.run();
}
