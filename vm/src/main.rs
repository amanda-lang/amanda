use std::collections::HashMap;
use std::convert::From;
use std::{env, fs, path::Path};
use vm::ama_value::{AmaFunc, AmaValue};
use vm::builtins;
use vm::vm::OpCode;

#[derive(Debug)]
struct Program<'a> {
    constants: Vec<AmaValue<'a>>,
    ops: Vec<u8>,
    main: AmaFunc<'a>,
}

fn parse_asm(src: &str) -> Program {
    let sections: Vec<&str> = src.split("<_SECT_BREAK_>").collect();
    assert!(sections.len() == 3, "Unknown amasm file format!");
    let main_locals = sections[0].parse::<usize>().unwrap();
    let constants = sections[1]
        .split("<_CONST_>")
        .map(|constant| constant.parse::<AmaValue>().unwrap())
        .collect();
    let mut ops: Vec<u8> = if !sections[2].is_empty() {
        sections[2]
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
            name: "_inicio_",
            start_ip: 0,
            ip: 0,
            locals: main_locals,
            bp: -1,
        },
    }
}

const RECURSION_LIMIT: usize = 1000;

#[derive(Debug)]
struct FrameStack<'a> {
    stack: [Option<AmaFunc<'a>>; RECURSION_LIMIT],
    sp: isize,
}

impl<'a> FrameStack<'a> {
    pub fn new() -> Self {
        FrameStack {
            stack: [None; RECURSION_LIMIT],
            sp: -1,
        }
    }

    pub fn push(&mut self, frame: AmaFunc<'a>) -> Result<(), ()> {
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

    #[inline]
    pub fn peek(&self) -> &AmaFunc<'a> {
        self.stack[self.sp as usize].as_ref().unwrap()
    }

    #[inline]
    pub fn peek_mut(&mut self) -> &mut AmaFunc<'a> {
        self.stack[self.sp as usize].as_mut().unwrap()
    }
}

struct AmaVM<'a> {
    program: Vec<u8>,
    constants: &'a Vec<AmaValue<'a>>,
    values: Vec<AmaValue<'a>>,
    frames: FrameStack<'a>,
    globals: HashMap<&'a str, AmaValue<'a>>,
    sp: isize,
}

impl<'a> AmaVM<'a> {
    pub fn new(program: &'a mut Program<'a>) -> Self {
        let mut vm = AmaVM {
            program: program.ops.clone(),
            constants: &program.constants,
            values: vec![AmaValue::None; program.main.locals.into()],
            frames: FrameStack::new(),
            globals: HashMap::new(),
            sp: -1,
        };
        vm.frames.push(program.main).unwrap();
        vm.sp = vm.values.len() as isize - 1;
        vm.frames.peek_mut().bp = if vm.sp > -1 { 0 } else { -1 };
        vm
    }

    fn op_push(&mut self, value: AmaValue<'a>) {
        self.sp += 1;
        let values_size = self.values.len() as isize;
        if self.sp == values_size {
            self.values.push(value);
        } else if self.sp < values_size {
            self.values[self.sp as usize] = value;
        }
    }

    fn op_pop(&mut self) -> AmaValue<'a> {
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
        self.frames.peek_mut().ip += 1;
        self.program[self.frames.peek().ip]
    }

    fn get_u16_arg(&mut self) -> u16 {
        ((self.get_byte() as u16) << 8) | self.get_byte() as u16
    }

    fn reserve_stack_space(&mut self, size: usize) {
        for _ in 0..size {
            self.op_push(AmaValue::None);
        }
    }

    pub fn run(&mut self) {
        loop {
            let op = self.program[self.frames.peek().ip];
            match OpCode::from(&op) {
                OpCode::LoadConst => {
                    let idx = self.get_u16_arg();
                    self.op_push(AmaValue::clone(&self.constants[idx as usize]));
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
                    self.op_push(AmaValue::binop(left, OpCode::from(&op), right))
                }
                OpCode::OpInvert | OpCode::OpNot => {
                    let operand = self.op_pop();
                    let op = OpCode::from(&op);
                    if let OpCode::OpInvert = op {
                        match operand {
                            AmaValue::Int(num) => self.op_push(AmaValue::Int(-num)),
                            AmaValue::F64(num) => self.op_push(AmaValue::F64(-num)),
                            _ => panic!("Fatal error!"),
                        };
                    } else {
                        if let AmaValue::Bool(val) = operand {
                            self.op_push(AmaValue::Bool(!val));
                        } else {
                            panic!("Value should always be a bool");
                        }
                    }
                }
                OpCode::DefGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let init_type = self.get_byte();
                    let initializer = match init_type {
                        0 => AmaValue::Int(0),
                        1 => AmaValue::F64(0.0),
                        2 => AmaValue::Bool(false),
                        3 => AmaValue::Str(String::from("")),
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
                    self.frames.peek_mut().ip = addr;
                    continue;
                }
                OpCode::JumpIfFalse => {
                    /*
                     * Jumps if the top of the values is false
                     * Pops the values
                     * */
                    let addr = self.get_u16_arg() as usize;
                    let value = self.op_pop();
                    if let AmaValue::Bool(false) = value {
                        self.frames.peek_mut().ip = addr;
                        continue;
                    }
                }
                OpCode::GetLocal => {
                    let idx = self.get_u16_arg() as usize + self.frames.peek().bp as usize;
                    //#TODO: Do not use clone
                    self.op_push(self.values[idx].clone());
                }
                OpCode::SetLocal => {
                    let idx = self.frames.peek().bp as usize + self.get_u16_arg() as usize;
                    self.values[idx] = self.op_pop();
                }
                OpCode::MakeFunction => {
                    let locals = self.op_pop().take_int() as usize;
                    let addr = self.op_pop().take_int() as usize;
                    let name_idx = self.op_pop().take_int() as usize;
                    let name = self.constants[name_idx].take_str();

                    self.op_push(AmaValue::Func(AmaFunc {
                        name,
                        start_ip: addr,
                        ip: addr,
                        bp: -1,
                        locals,
                    }));
                }
                OpCode::CallFunction => {
                    let args = self.get_byte() as isize;
                    let mut func = self.op_pop().take_func();
                    //Reserve space
                    //TODO: Find out if this is the fatest way to do this
                    if args > 0 {
                        func.bp = self.sp - (args - 1);
                        let extra = func.locals - args as usize;
                        self.reserve_stack_space(extra);
                    } else if func.locals > 0 {
                        func.bp = self.sp + 1;
                        self.reserve_stack_space(func.locals);
                    }
                    //Set return addr in caller
                    self.frames.peek_mut().ip += 1;
                    self.frames.push(func).unwrap();
                    continue;
                }
                OpCode::Return => {
                    let val = self.op_pop();
                    let frame_bp = self.frames.peek().bp;
                    self.sp = if frame_bp > -1 { frame_bp - 1 } else { self.sp };
                    self.frames.pop().unwrap();
                    self.op_push(val);
                    continue;
                }
                OpCode::Halt => break,
                _ => unimplemented!(
                    "Cannot not execute OpCode {:?}, maybe it hasn't been implemented yet",
                    op
                ),
            }
            self.frames.peek_mut().ip += 1;
        }
    }

    fn print_debug_info(&self) {
        println!("[Function]: {}", self.frames.peek().name);
        println!("[IP]: {}", self.frames.peek().ip);
        println!("[SP]: {}", self.sp);
        println!("[BP]: {}", self.frames.peek().bp);
        println!("[STACK]: {:?}", self.values);
        println!("--------------");
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
    let mut program = parse_asm(&src);
    let mut vm = AmaVM::new(&mut program);
    vm.run();
    debug_assert!(
        vm.frames.peek().name == "_inicio_",
        "Some function did not cleanely exit! \n{:?}",
        vm.values
    );
}
