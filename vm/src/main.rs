use std::convert::From;
use std::fmt;
use std::fmt::{Display, Formatter};
use std::{env, fs, path::Path};

#[repr(u8)]
enum OpCode {
    MOSTRA,
    PUSHCONST,
    HALT = 255,
}

//TODO: Find better way to do this
impl From<u8> for OpCode {
    fn from(number: u8) -> Self {
        match number {
            0x00 => OpCode::MOSTRA,
            0x01 => OpCode::PUSHCONST,
            0xFF => OpCode::HALT,
            _ => unimplemented!(),
        }
    }
}

#[derive(Debug)]
enum Op {
    MOSTRA,
    PUSHCONST(u16),
}

#[derive(Debug)]
enum Const {
    Str(String),
    Int(i128),
    F64(f64),
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
            Const::F64(float) => write!(f, "{}", float),
        }
    }
}

#[derive(Debug)]
struct Program {
    constants: Vec<Const>,
    ops: Vec<Op>,
}

fn parse_asm(src: String) -> Program {
    let lines: Vec<&str> = src.split("\n").collect();
    //If data section is present, load constants
    let mut constants = Vec::new();
    let mut ops = Vec::new();
    let mut idx = 0;
    if lines[idx].trim() == ".data" {
        idx = 1;
        for line in &lines[idx..] {
            if line.trim() == ".ops" {
                break;
            }
            let constant: &str = line.trim();
            let maybe_int = constant.parse::<i128>();
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
            let op: Op = match &instr[0].trim().parse::<u8>() {
                Ok(op) => match op {
                    0x00 => Op::MOSTRA,
                    0x01 => {
                        let idx = instr[1].parse::<u16>().unwrap();
                        Op::PUSHCONST(idx)
                    }
                    _ => unimplemented!("Op not implemented"),
                },
                _ => panic!("Invalid syntax in amasm file"),
            };
            ops.push(op);
        }
    }
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
    pub fn new() -> Self {
        AmaVM {
            program: Vec::new(),
            constants: Vec::new(),
            pc: 0,
            stack: Vec::new(),
            sp: -1,
        }
    }

    pub fn init_vm(&mut self, program: Program) {
        self.constants = program.constants;
        self.sp = (self.constants.len() - 1) as isize;
        for op in &program.ops {
            match op {
                Op::MOSTRA => {
                    self.program.push(OpCode::MOSTRA as u8);
                }
                Op::PUSHCONST(idx) => {
                    self.program.push(OpCode::PUSHCONST as u8);
                    //Split index into high and low
                    let high: u8 = ((idx & 0xFF00) >> 8) as u8;
                    let low: u8 = (idx & 0x00FF) as u8;
                    self.program.push(high);
                    self.program.push(low);
                }
            }
        }
        self.program.push(OpCode::HALT as u8);
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
            match OpCode::from(op) {
                OpCode::PUSHCONST => {
                    let idx = ((self.get_byte() as u16) << 8) | self.get_byte() as u16;
                    self.op_push(Const::clone(&self.constants[idx as usize]));
                }
                OpCode::MOSTRA => println!("{}", self.op_pop()),
                OpCode::HALT => break,
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
    let program = parse_asm(src);
    let mut vm = AmaVM::new();
    vm.init_vm(program);
    vm.run();
}
