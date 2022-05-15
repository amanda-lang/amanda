use std::borrow::Cow;
use crate::ama_value;
use crate::ama_value::{AmaFunc, AmaValue};
use crate::binload::Module;
use crate::builtins;
use crate::errors::AmaErr;
use unicode_segmentation::UnicodeSegmentation;
use std::collections::HashMap;
use std::convert::From;


#[repr(u8)]
#[derive(Debug, Clone, Copy)]
pub enum OpCode {
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
    OpIndex,
    GetGlobal,
    SetGlobal,
    Jump,
    JumpIfFalse,
    GetLocal,
    SetLocal,
    CallFunction,
    Return,
    Cast,
    BuildStr, 
    Halt = 255,
}

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
            OpCode::OpIndex,
            OpCode::GetGlobal,
            OpCode::SetGlobal,
            OpCode::Jump,
            OpCode::JumpIfFalse,
            OpCode::GetLocal,
            OpCode::SetLocal,
            OpCode::CallFunction,
            OpCode::Return,
            OpCode::Cast,
            OpCode::BuildStr,
        ];
        if *number == 0xff {
            OpCode::Halt
        } else {
            ops[*number as usize]
        }
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
        if self.sp + 1 == RECURSION_LIMIT as isize {
            return Err(());
        }
        self.sp += 1;
        self.stack[self.sp as usize] = Some(frame);
        Ok(())
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

pub struct AmaVM<'a> {
    module: &'a Module<'a>,
    frames: FrameStack<'a>,
    globals: HashMap<&'a str, AmaValue<'a>>,
    values: Vec<AmaValue<'a>>,
    sp: isize,
}

//TODO: Make this faster
fn offset_to_line(offset: usize, src_map: &Vec<usize>) -> usize {
    for i in (0..src_map.len()).step_by(3) {
        if offset >= src_map[i] && offset <= src_map[i + 1] {
            return src_map[i + 2];
        }
    }
    0
}

impl<'a> AmaVM<'a> {
    pub fn new(module: &'a Module<'a>) -> Self {
        let mut vm = AmaVM {
            module,
            frames: FrameStack::new(),
            globals: builtins::load_builtins(),
            values: vec![AmaValue::None; module.main.locals.into()],
            sp: -1,
        };
        vm.frames.push(module.main).unwrap();
        vm.sp = vm.values.len() as isize - 1;
        vm.frames.peek_mut().bp = if vm.sp > -1 { 0 } else { -1 };

        for func in module.functions.iter() {
            vm.globals.insert(func.name, AmaValue::Func(*func));
        }

        vm
    }

    //TODO: Review use of clone in push and pop 
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
        self.module.code[self.frames.peek().ip]
    }

    fn get_u16_arg(&mut self) -> u16 {
        ((self.get_byte() as u16) << 8) | self.get_byte() as u16
    }

    fn get_u64_arg(&mut self) -> u64 {
        let mut uint64 = [0; 8];
        for i in 0..8 {
            uint64[i] = self.get_byte();
        }
        u64::from_be_bytes(uint64)
    }

    fn reserve_stack_space(&mut self, size: usize) {
        let new_len = self.values.len() + size;
        self.values.resize(new_len, AmaValue::None);
        self.sp = self.values.len() as isize - 1;
    }

    pub fn run(&mut self) -> Result<(), AmaErr> {
        loop {
            let op = self.module.code[self.frames.peek().ip];
            self.frames.peek_mut().last_i = self.frames.peek().ip;
            match OpCode::from(&op) {
                OpCode::LoadConst => {
                    let idx = self.get_u16_arg();
                    self.op_push(AmaValue::from(&self.module.constants[idx as usize]));
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
                    let result = AmaValue::binop(left, OpCode::from(&op), right);

                    if let Err(msg) = result {
                        return self.panic_and_throw(msg);
                    } else {
                        self.op_push(result.unwrap());
                    }
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
                OpCode::OpIndex => {
                    let idx = self.op_pop().take_int();
                    let target = self.op_pop();
                    match target {
                        //TODO - Optimization: Maybe should implement some kind of cache for the grapheme clusters  
                        // to avoid repeatedly calling iterator
                        AmaValue::Str(string) =>{
                            if idx < 0 {
                               self.panic_and_throw("Erro de índice inválido. Strings só podem ser indexadas com inteiros positivos")?;
                            }
                            let real_str = &string as &str;
                            let user_char = real_str.graphemes(true).nth(idx as usize);
                            if let Some(user_char) = user_char {
                                self.op_push(AmaValue::Str(Cow::Owned(String::from(user_char))));
                            } else {
                                self.panic_and_throw(&format!("Erro de índice inválido. O tamanho da string é {}, mas o índice é {}", real_str.graphemes(true).count(), idx))?;
                            }
                        }
                        _ => panic!("Fatal error!"),
                    }

                }
                OpCode::GetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id: &str = &self.module.names[id_idx];
                    //TODO: Do not use clone
                    self.op_push(self.globals.get(id).unwrap().clone());
                }
                OpCode::SetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id: &str = &self.module.names[id_idx];
                    let value = self.op_pop();
                    self.globals.insert(id, value);
                }
                OpCode::Jump => {
                    let addr = self.get_u64_arg() as usize;
                    self.frames.peek_mut().ip = addr;
                    continue;
                }
                OpCode::JumpIfFalse => {
                    /*
                     * Jumps if the top of the values is false
                     * Pops the values
                     * */
                    let addr = self.get_u64_arg() as usize;
                    let value = self.op_pop();
                    if let AmaValue::Bool(false) = value {
                        self.frames.peek_mut().ip = addr;
                        continue;
                    }
                }
                OpCode::GetLocal => {
                    let idx = self.get_u16_arg() as usize + self.frames.peek().bp as usize;
                    //TODO: Do not use clone
                    self.op_push(self.values[idx].clone());
                }
                OpCode::SetLocal => {
                    let idx = self.frames.peek().bp as usize + self.get_u16_arg() as usize;
                    self.values[idx] = self.op_pop();
                }
                OpCode::CallFunction => {
                    let args = self.get_byte() as isize;
                    let fn_val = self.op_pop();
                    match fn_val {
                        AmaValue::Func(mut func) => {
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
                            if let Err(()) = self.frames.push(func) {
                                return self.panic_and_throw("Limite máximo de recursão atingido");
                            }
                            continue;
                        }
                        AmaValue::NativeFn(native_fn) => {
                            let mut fn_args = None;
                            if args > 0 {
                                let start = (self.sp - (args - 1)) as usize;
                                fn_args = Some(self.values[start..=self.sp as usize].as_ptr());
                                self.sp = start as isize - 1;
                            }
                            let result = (native_fn.func)(fn_args);
                            if let Err(msg) = result {
                                return self.panic_and_throw(&msg);
                            }
                            self.op_push(result.unwrap());
                            //Drop values
                            self.values.drain(self.sp as usize + 1..);
                        }
                        _ => panic!("Expected function at the top of the stack!"),
                    }
                }
                OpCode::Return => {
                    let val = self.op_pop();
                    let frame_bp = self.frames.peek().bp;
                    self.sp = if frame_bp > -1 { frame_bp - 1 } else { self.sp };
                    self.frames.pop().unwrap();
                    self.op_push(val);
                    continue;
                }
                OpCode::BuildStr => {
                    let num_parts = self.get_byte() as isize;
                    let start = (self.sp - (num_parts - 1)) as usize;
                    let mut built_str = String::new();
                    for i in start..=self.sp as usize {
                        built_str.push_str(&format!("{}", self.values[i]));
                    }
                    //Drop values
                    self.sp = start as isize - 1;
                    self.values.drain((self.sp + 1) as usize..);
                    self.op_push(AmaValue::Str(Cow::Owned(built_str)));
                }
                OpCode::Cast => {
                    let arg = self.get_byte();
                    let new_type = self.op_pop().take_type();
                    let val = self.op_pop();
                    if arg == 0 {
                        let cast_res = ama_value::cast(val, new_type);
                        if let Err(msg) = cast_res {
                            return self.panic_and_throw(&msg);
                        }
                        self.op_push(cast_res.unwrap());
                    } else if arg == 1 {
                        if !ama_value::check_cast(val.get_type(), new_type) {
                            return self.panic_and_throw(&format!(
                                "Conversão inválida. O tipo original do valor é '{}', mas tentou converter o valor para o tipo '{}'",
                                val.get_type().name(), 
                                new_type.name()
                            ));
                        }
                        self.op_push(val);
                    }
                }
                OpCode::Halt => break,
                _ => unimplemented!(
                    "Cannot not execute OpCode {:?}, maybe it hasn't been implemented yet",
                    op
                ),
            }
            self.frames.peek_mut().ip += 1;
        }
        debug_assert!(
            self.frames.peek().name == "_inicio_",
            "Some function did not cleanely exit! \n{:?}",
            self.values
        );
        Ok(())
    }

    fn panic_and_throw(&mut self, error: &str) -> Result<(), AmaErr> {
        let mut frames_sp = self.frames.sp;
        let mut err_str = if frames_sp > 0 {
            String::from("Fluxo de execução: \n")
        } else {
            String::from("")
        };
        while let Ok(func) = self.frames.pop() {
            if frames_sp == 0 {
                err_str.push_str(&format!(
                    "Erro na linha {}: {}.",
                    offset_to_line(func.last_i, &self.module.src_map),
                    error
                ));
                break;
            }
            err_str.push_str(&format!(
                "    Linha {}, na função {}\n",
                offset_to_line(func.last_i, &self.module.src_map),
                func.name
            ));
            frames_sp = self.frames.sp;
        }
        Err(err_str)
    }

    fn print_debug_info(&self) {
        println!("[Function]: {}", self.frames.peek().name);
        println!("[IP]: {}", self.frames.peek().ip);
        println!("[SP]: {}", self.sp);
        println!(
            "[OP]: {:?}",
            OpCode::from(&self.module.code[self.frames.peek().ip])
        );
        println!("[BP]: {}", self.frames.peek().bp);
        println!("[STACK]: {:?}", self.values);
        println!("--------------");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn offset_to_line_works() {
        let src_map = vec![0, 3, 1, 4, 5, 2];
        assert_eq!(offset_to_line(0, &src_map), 1);
        assert_eq!(offset_to_line(1, &src_map), 1);
        assert_eq!(offset_to_line(3, &src_map), 1);
        assert_eq!(offset_to_line(5, &src_map), 2);
    }
}
