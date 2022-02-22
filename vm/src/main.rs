use std::convert::From;
use std::fmt;
use std::fmt::{Display, Formatter};
use std::ops::Add;
use std::{env, fs, path::Path};

#[repr(u8)]
#[derive(Debug)]
enum OpCode {
    Mostra,
    PushConst,
    OpAdd,
    OpMinus,
    OpMul,
    OpDiv,
    OpFloorDiv,
    OpModulo,
    OpInvert,
    Halt = 255,
}

//TODO: Find better way to do this
impl From<&u8> for OpCode {
    fn from(number: &u8) -> Self {
        match number {
            0x00 => OpCode::Mostra,
            0x01 => OpCode::PushConst,
            0x02 => OpCode::OpAdd,
            0x03 => OpCode::OpMinus,
            0x04 => OpCode::OpMul,
            0x05 => OpCode::OpDiv,
            0x06 => OpCode::OpFloorDiv,
            0x07 => OpCode::OpModulo,
            0x08 => OpCode::OpInvert,
            0xFF => OpCode::Halt,
            _ => unimplemented!(),
        }
    }
}

#[derive(Debug)]
enum Const {
    Str(String),
    Int(i64),
    F64(f64),
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
            _ => unimplemented!(),
        }
    }

    fn take_int(&self) -> i64 {
        match self {
            Const::Int(int) => *int,
            Const::F64(float) => *float as i64,
            _ => unimplemented!(),
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
        }
    }
}

#[derive(Debug)]
struct Program {
    constants: Vec<Const>,
    ops: Vec<u8>,
}

fn parse_asm(src: String) -> Program {
    let lines: Vec<&str> = src.split("\n").collect();
    //If data section is present, load constants
    let mut constants = Vec::new();
    let mut ops: Vec<u8> = Vec::new();
    let mut idx = 0;
    if lines[idx].trim() == ".data" {
        idx = 1;
        for line in &lines[idx..] {
            if line.trim() == ".ops" {
                break;
            }
            let constant: &str = line.trim();
            let maybe_int = constant.parse::<i64>();
            let maybe_float = constant.parse::<f64>();
            if maybe_int.is_ok() {
                constants.push(Const::Int(maybe_int.unwrap()))
            } else if maybe_float.is_ok() {
                constants.push(Const::F64(maybe_float.unwrap()))
            } else {
                let string = String::from(constant.replace("\"", "").replace("\'", ""));
                constants.push(Const::Str(string))
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
                    OpCode::PushConst => {
                        let idx = instr[1].parse::<u16>().unwrap();
                        ops.push(OpCode::PushConst as u8);
                        //Split index into high and low
                        let high: u8 = ((idx & 0xFF00) >> 8) as u8;
                        let low: u8 = (idx & 0x00FF) as u8;
                        ops.push(high);
                        ops.push(low);
                    }
                    _ => unimplemented!("Op not implemented"),
                },
                _ => panic!("Invalid syntax in amasm file"),
            };
        }
    }
    //Add halt opcode
    ops.push(OpCode::Halt as u8);
    Program { constants, ops }
}

struct AmaVM {
    program: Vec<u8>,
    constants: Vec<Const>,
    pc: usize,
    stack: Vec<Const>,
    sp: isize,
}

impl AmaVM {
    pub fn from_program(program: Program) -> Self {
        AmaVM {
            program: program.ops,
            constants: program.constants,
            pc: 0,
            stack: Vec::new(),
            sp: -1,
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

    pub fn run(&mut self) {
        loop {
            let op = self.program[self.pc];
            match OpCode::from(&op) {
                OpCode::PushConst => {
                    let idx = ((self.get_byte() as u16) << 8) | self.get_byte() as u16;
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
                OpCode::Halt => break,
                _ => unimplemented!(),
            }
            self.pc += 1;
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 1 {
        eprintln!("Por favor especifique o ficheiro a ser executado");
        return;
    }
    let file = Path::new(&args[1]);
    let src = String::from_utf8(fs::read(file).unwrap()).unwrap();
    let mut vm = AmaVM::from_program(parse_asm(src));
    vm.run();
}
