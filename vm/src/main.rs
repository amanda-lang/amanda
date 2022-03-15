use std::borrow::Cow;
use std::collections::HashMap;
use std::convert::From;
use std::fmt;
use std::fmt::{Display, Formatter};
use std::rc::Rc;
use std::str::FromStr;
use std::{env, fs, path::Path};

#[repr(u8)]
#[derive(Debug, Clone)]
enum OpCode {
    Mostra,
    LoadAmaData,
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
            OpCode::LoadAmaData,
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
            AmaData::F64(_) => AmaData::F64($left.take_float() $op $right.take_float()),
            AmaData::Int(_) => AmaData::Int($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

macro_rules! comp_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            AmaData::F64(_) => AmaData::Bool($left.take_float() $op $right.take_float()),
            AmaData::Int(_) => AmaData::Bool($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

macro_rules! eq_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            AmaData::Int(_) => AmaData::Bool($left.take_int() $op $right.take_int()),
            AmaData::F64(_) => AmaData::Bool($left.take_float() $op $right.take_float()),
            AmaData::Bool(_) => AmaData::Bool($left.take_bool() $op $right.take_bool()),
            AmaData::Str(_) => AmaData::Bool($left.take_str() $op $right.take_str()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

#[derive(Debug, Clone, Copy)]
struct AmaFunc {
    name_idx: usize,
    start_ip: usize,
    ip: usize,
}

#[derive(Debug)]
enum AmaData {
    Str(String),
    Int(i64),
    F64(f64),
    Bool(bool),
    Func(AmaFunc),
    None,
}

impl AmaData {
    fn is_float(&self) -> bool {
        if let AmaData::F64(_) = self {
            true
        } else {
            false
        }
    }

    fn take_float(&self) -> f64 {
        match self {
            AmaData::F64(float) => *float,
            AmaData::Int(int) => *int as f64,
            _ => panic!("Value is not a float"),
        }
    }

    fn take_int(&self) -> i64 {
        match self {
            AmaData::Int(int) => *int,
            AmaData::F64(float) => *float as i64,
            _ => panic!("Value is not an int"),
        }
    }

    fn take_str(&self) -> &str {
        if let AmaData::Str(string) = self {
            string
        } else {
            panic!("Value is not an str")
        }
    }

    fn take_bool(&self) -> bool {
        if let AmaData::Bool(val) = self {
            *val
        } else {
            panic!("Value is not a bool")
        }
    }

    fn is_str(&self) -> bool {
        if let AmaData::Str(_) = self {
            true
        } else {
            false
        }
    }

    fn is_bool(&self) -> bool {
        if let AmaData::Bool(_) = self {
            true
        } else {
            false
        }
    }

    fn is_int(&self) -> bool {
        if let AmaData::Int(_) = self {
            true
        } else {
            false
        }
    }

    fn binop(left: Self, op: OpCode, right: Self) -> Self {
        let res_type = if left.is_float() || right.is_float() {
            AmaData::F64(0.0)
        } else if left.is_int() && right.is_int() {
            AmaData::Int(0)
        } else if left.is_bool() && right.is_bool() {
            AmaData::Bool(false)
        } else if left.is_str() && right.is_str() {
            AmaData::Str(String::from(""))
        } else {
            unimplemented!("Error is not implemented")
        };
        match op {
            OpCode::OpAdd => arith_ops!(res_type, left, +, right),
            OpCode::OpMinus => arith_ops!(res_type, left, -, right),
            OpCode::OpMul => arith_ops!(res_type, left, *, right),
            OpCode::OpModulo => arith_ops!(res_type, left, %, right),
            OpCode::OpDiv => AmaData::F64(left.take_float() / right.take_float()),
            OpCode::OpFloorDiv => AmaData::Int(left.take_int() / right.take_int()),
            OpCode::OpAnd => AmaData::Bool(left.take_bool() && right.take_bool()),
            OpCode::OpOr => AmaData::Bool(left.take_bool() || right.take_bool()),
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

impl Clone for AmaData {
    fn clone(&self) -> Self {
        match self {
            AmaData::Str(string) => AmaData::Str(String::clone(string)),
            AmaData::Int(int) => AmaData::Int(*int),
            AmaData::F64(float) => AmaData::F64(*float),
            AmaData::Bool(val) => AmaData::Bool(*val),
            AmaData::None => AmaData::None,
            AmaData::Func(function) => AmaData::Func(function.clone()),
        }
    }
}

impl FromStr for AmaData {
    type Err = ();

    fn from_str(constant: &str) -> Result<AmaData, ()> {
        if constant == "verdadeiro" || constant == "falso" {
            let bool_val = if constant == "falso" { false } else { true };
            return Ok(AmaData::Bool(bool_val));
        }
        let maybe_int = constant.parse::<i64>();
        let maybe_float = constant.parse::<f64>();
        if maybe_int.is_ok() {
            return Ok(AmaData::Int(maybe_int.unwrap()));
        } else if maybe_float.is_ok() {
            return Ok(AmaData::F64(maybe_float.unwrap()));
        } else {
            let slice: &str = if &constant[..1] == "\"" || &constant[..1] == "\'" {
                &constant[1..constant.len() - 1]
            } else {
                constant
            };
            return Ok(AmaData::Str(String::from(slice)));
        }
    }
}

impl Display for AmaData {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match self {
            AmaData::Str(string) => write!(f, "{}", string),
            AmaData::Int(integer) => write!(f, "{}", integer),
            AmaData::F64(float) => {
                if float.fract() == 0.0 {
                    return write!(f, "{}.0", float);
                }
                write!(f, "{}", float)
            }
            AmaData::Bool(val) => {
                let val_str = if *val { "verdadeiro" } else { "falso" };
                write!(f, "{}", val_str)
            }
            AmaData::None => panic!("None value should not be printed"),
            _ => write!(f, "{:?}", self),
        }
    }
}

#[derive(Debug)]
struct Program {
    constants: Vec<AmaData>,
    ops: Vec<u8>,
    main: AmaFunc,
}

fn parse_asm(src: String) -> Program {
    let sections: Vec<&str> = src.split("<_SECT_BREAK_>").collect();
    assert!(sections.len() == 2, "Unknown amasm file format!");
    let constants = sections[0]
        .split("<_CONST_>")
        .map(|constant| constant.parse::<AmaData>().unwrap())
        .collect();
    let mut ops: Vec<u8> = if !sections[1].is_empty() {
        sections[1]
            .split(" ")
            .map(|op| op.parse::<u8>().unwrap())
            .collect()
    } else {
        Vec::with_capacity(1)
    };

    ops.push(OpCode::Halt as u8);
    Program {
        constants,
        ops,
        main: AmaFunc {
            name_idx: 0,
            start_ip: 0,
            ip: 0,
        },
    }
}

const RECURSION_LIMIT: usize = 1000;

#[derive(Debug)]
struct FrameStack {
    stack: [Option<AmaFunc>; RECURSION_LIMIT],
    sp: isize,
}

impl FrameStack {
    pub fn new() -> Self {
        FrameStack {
            stack: [None; RECURSION_LIMIT],
            sp: -1,
        }
    }

    pub fn push(&mut self, frame: AmaFunc) -> Result<(), ()> {
        self.sp += 1;
        if self.sp as usize == RECURSION_LIMIT {
            Err(())
        } else {
            self.stack[self.sp as usize] = Some(frame);
            Ok(())
        }
    }

    pub fn pop(&mut self) -> Result<AmaFunc, ()> {
        if self.sp < -1 {
            Err(())
        } else {
            let top = self.stack[self.sp as usize];
            self.sp -= 1;
            Ok(top.unwrap())
        }
    }

    pub fn peek_mut(&mut self) -> Option<AmaFunc> {
        self.stack[self.sp as usize]
    }
}

struct AmaVM<'a> {
    program: Vec<u8>,
    constants: &'a Vec<AmaData>,
    values: Vec<AmaData>,
    frames: FrameStack,
    c_func: AmaFunc,
    globals: HashMap<&'a str, AmaData>,
    sp: isize,
    bp: isize,
}

impl<'a> AmaVM<'a> {
    pub fn new(program: &'a mut Program) -> Self {
        let mut vm = AmaVM {
            program: program.ops.clone(),
            constants: &program.constants,
            values: Vec::new(),
            frames: FrameStack::new(),
            globals: HashMap::new(),
            c_func: program.main,
            sp: -1,
            bp: -1,
        };
        vm.frames.push(program.main).unwrap();
        vm
    }

    fn op_push(&mut self, value: AmaData) {
        self.sp += 1;
        let values_size = self.values.len() as isize;
        if self.sp == values_size {
            self.values.push(value);
        } else if self.sp < values_size {
            self.values[self.sp as usize] = value;
        }
    }

    fn op_pop(&mut self) -> AmaData {
        let values_size = (self.values.len() - 1) as isize;
        if self.sp == values_size {
            self.sp -= 1;
            self.values.pop().unwrap()
        } else if self.sp < values_size {
            let idx = self.sp;
            self.sp -= 1;
            self.values[idx as usize].clone()
        } else {
            panic!("Undefined VM State. sp larger than values!");
        }
    }

    fn get_byte(&mut self) -> u8 {
        self.c_func.ip += 1;
        self.program[self.c_func.ip]
    }

    fn get_u16_arg(&mut self) -> u16 {
        ((self.get_byte() as u16) << 8) | self.get_byte() as u16
    }

    pub fn run(&mut self) {
        loop {
            let op = self.program[self.c_func.ip];
            match OpCode::from(&op) {
                OpCode::LoadAmaData => {
                    let idx = self.get_u16_arg();
                    self.op_push(AmaData::clone(&self.constants[idx as usize]));
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
                    self.op_push(AmaData::binop(left, OpCode::from(&op), right))
                }
                OpCode::OpInvert | OpCode::OpNot => {
                    let operand = self.op_pop();
                    let op = OpCode::from(&op);
                    if let OpCode::OpInvert = op {
                        match operand {
                            AmaData::Int(num) => self.op_push(AmaData::Int(-num)),
                            AmaData::F64(num) => self.op_push(AmaData::F64(-num)),
                            _ => panic!("Fatal error!"),
                        };
                    } else {
                        if let AmaData::Bool(val) = operand {
                            self.op_push(AmaData::Bool(!val));
                        } else {
                            panic!("Value should always be a bool");
                        }
                    }
                }
                OpCode::DefGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let init_type = self.get_byte();
                    let initializer = match init_type {
                        0 => AmaData::Int(0),
                        1 => AmaData::F64(0.0),
                        2 => AmaData::Bool(false),
                        3 => AmaData::Str(String::from("")),
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
                    self.c_func.ip = addr;
                    continue;
                }
                OpCode::JumpIfFalse => {
                    /*
                     * Jumps if the top of the values is false
                     * Pops the values
                     * */
                    let addr = self.get_u16_arg() as usize;
                    let value = self.op_pop();
                    if let AmaData::Bool(false) = value {
                        self.c_func.ip = addr;
                        continue;
                    }
                }
                OpCode::SetupBlock => {
                    let num_locals = self.get_u16_arg();
                    self.values.reserve(num_locals as usize);
                    self.bp = self.sp + 1;
                    for _ in 0..num_locals {
                        self.op_push(AmaData::None);
                    }
                }
                OpCode::ExitBlock => {
                    self.sp = self.bp - 1;
                    self.bp = -1;
                }
                OpCode::GetLocal => {
                    let idx = self.get_u16_arg() as usize + self.bp as usize;
                    //#TODO: Do not use clone
                    self.op_push(self.values[idx].clone());
                }
                OpCode::SetLocal => {
                    let idx = self.bp as usize + self.get_u16_arg() as usize;
                    self.values[idx] = self.op_pop();
                }
                OpCode::Halt => break,
                _ => unimplemented!(
                    "Cannot not execute OpCode {:?}, maybe it hasn't been implemented yet",
                    op
                ),
            }
            self.c_func.ip += 1;
        }
    }

    fn print_debug_info(&self) {
        println!("[IP]: {}", self.c_func.ip);
        println!("[SP]: {}", self.sp);
        println!("[BP]: {}", self.bp);
        println!("[STACK]: {:?}", self.values);
        println!("[CALL FRAMES]: {:?}", self.frames);
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
    let mut vm = AmaVM::new(&mut program);
    vm.run();
    debug_assert!(
        vm.sp == -1,
        "Stack was not cleaned up properly! \n{:?}",
        vm.values
    )
}
