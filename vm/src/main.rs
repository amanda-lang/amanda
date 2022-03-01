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
    DefGlobal,
    GetGlobal,
    SetGlobal,
    Jump,
    JumpIfFalse,
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
            OpCode::DefGlobal,
            OpCode::GetGlobal,
            OpCode::SetGlobal,
            OpCode::Jump,
            OpCode::JumpIfFalse,
        ];
        if *number == 0xff {
            OpCode::Halt
        } else {
            ops[*number as usize].clone()
        }
    }
}

#[derive(Debug)]
enum Const {
    Str(String),
    Int(i64),
    F64(f64),
    Bool(bool),
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
        } else {
            unimplemented!("Error is not implemented")
        };
        match op {
            OpCode::OpAdd => match res_type {
                Const::F64(_) => Const::F64(left.take_float() + right.take_float()),
                Const::Int(_) => Const::Int(left.take_int() + right.take_int()),
                _ => unimplemented!("Operand type not supported"),
            },
            OpCode::OpMinus => match res_type {
                Const::F64(_) => Const::F64(left.take_float() - right.take_float()),
                Const::Int(_) => Const::Int(left.take_int() - right.take_int()),
                _ => unimplemented!("Operand type not supported"),
            },
            OpCode::OpMul => match res_type {
                Const::F64(_) => Const::F64(left.take_float() * right.take_float()),
                Const::Int(_) => Const::Int(left.take_int() * right.take_int()),
                _ => unimplemented!("Operand type not supported"),
            },
            OpCode::OpModulo => match res_type {
                Const::F64(_) => Const::F64(left.take_float() % right.take_float()),
                Const::Int(_) => Const::Int(left.take_int() % right.take_int()),
                _ => unimplemented!("Operand type not supported"),
            },
            OpCode::OpDiv => Const::F64(left.take_float() / right.take_float()),
            OpCode::OpFloorDiv => Const::Int(left.take_int() / right.take_int()),
            _ => unimplemented!(),
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
                    | OpCode::OpInvert => ops.push(*op as u8),
                    OpCode::LoadConst => {
                        let idx = instr[1].parse::<ConstIndex>().unwrap();
                        ops.push(OpCode::LoadConst as u8);
                        //Store const index
                        push_u16_arg(&mut ops, idx);
                    }
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
                    OpCode::SetGlobal | OpCode::GetGlobal | OpCode::JumpIfFalse | OpCode::Jump => {
                        /* Pushes the value of a global variable onto the stack.
                         * The only arg is the index to the name of the var.
                         */
                        ops.push(*op as u8);
                        let arg = instr[1].parse::<ConstIndex>().unwrap();
                        push_u16_arg(&mut ops, arg);
                    }
                    _ => unimplemented!(
                        "Cannot not parse this OpCode, maybe it hasn't been implemented yet"
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
            globals: HashMap::new(),
        }
    }

    fn op_push(&mut self, value: Const) {
        self.sp += 1;
        self.stack.push(value);
    }

    fn op_pop(&mut self) -> Const {
        self.sp -= 1;
        self.stack.pop().unwrap()
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
                | OpCode::OpModulo => {
                    let right = self.op_pop();
                    let left = self.op_pop();
                    self.op_push(Const::binop(left, OpCode::from(&op), right))
                }
                OpCode::OpInvert => {
                    let operand = self.op_pop();
                    match operand {
                        Const::Int(num) => self.op_push(Const::Int(-num)),
                        Const::F64(num) => self.op_push(Const::F64(-num)),
                        _ => panic!("Fatal error!"),
                    };
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
                OpCode::Halt => break,
                _ => unimplemented!(
                    "Cannot not execute this OpCode, maybe it hasn't been implemented yet"
                ),
            }
            self.pc += 1;
        }
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
