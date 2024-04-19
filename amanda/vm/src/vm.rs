use std::collections::HashMap;
use std::fmt::Write;
use std::borrow::Cow;
use crate::ama_value;
use crate::ama_value::{AmaValue, RcCell};
use crate::values::function::{AmaFunc};
use crate::values::registo::{Tabela, RegObj};
use crate::modules::module::{Module, MGlobals};
use crate::errors::AmaErr;
use crate::alloc::{Alloc, Ref};
use crate::opcode::OpCode;
use crate::modules::builtins;
use unicode_segmentation::UnicodeSegmentation;
use std::convert::From;
use std::mem;

const RECURSION_LIMIT: usize = 1000;
const DEFAULT_STACK_SIZE: usize = 256;

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
    //globals: &'a mut MGlobals<'a>, 
    module: Option<&'a Module<'a>>,
    frames: FrameStack<'a>,
    values: Vec<AmaValue<'a>>,
    alloc: Alloc<'a>, 
    builtin_defs: builtins::BuiltinDefs<'a>, 
    imports: &'a Vec<Module<'a>>, 
    sp: isize
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
    pub fn new(imports: &'a Vec<Module<'a>>, alloc: Alloc<'a>) -> Self {
        let builtin_defs = builtins::definitions();
        AmaVM {
            module: None,
            frames: FrameStack::new(),
            values: vec![AmaValue::None; DEFAULT_STACK_SIZE],
            alloc, 
            builtin_defs, 
            imports, 
            sp: -1,
        }
    }

    fn init(&mut self, main: AmaFunc<'a>) {
        self.sp = -1;
        self.frames.push(main).unwrap();
        self.frames.peek_mut().bp = if self.sp > -1 { 0 } else { -1 };
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
            mem::replace(&mut self.values[idx as usize], AmaValue::None)
        } else {
            panic!("Undefined VM State. sp larger than values!");
        }
    }

    fn get_byte(&mut self) -> u8 {
        self.frames.peek_mut().ip += 1;
        self.module.unwrap().code[self.frames.peek().ip]
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

    fn alloc_ref<V>(&mut self, value: V) -> RcCell<V> {
        self.alloc.alloc_ref(value)
    }

    fn reset(&mut self) {
        self.sp = -1;
        self.frames.sp = -1;
    }

    pub fn run(&mut self, module: &'a Module<'a>, is_main: bool) -> Result<(), AmaErr> {
        if is_main {
            for module in self.imports {
                module.initialize(&self.builtin_defs);
                self.run(module, false)?;
                self.reset();
            }
        }
        self.module = Some(module);
        self.init(self.module.unwrap().main);

        loop {
            let op = self.module.unwrap().code[self.frames.peek().ip];
            self.frames.peek_mut().last_i = self.frames.peek().ip;
            match OpCode::from(&op) {
                OpCode::LoadConst => {
                    let idx = self.get_u16_arg();
                    self.op_push(self.module.unwrap().constants[idx as usize].clone());
                }
                OpCode::LoadName => {
                    let idx = self.get_u16_arg();
                    self.op_push(AmaValue::Str(Cow::Borrowed(&self.module.unwrap().names[idx as usize])));
                }
                OpCode::LoadRegisto => {
                    let idx = self.get_u16_arg() as usize;
                    self.op_push(AmaValue::Registo(&self.module.unwrap().registos[idx]))
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
                    let result = AmaValue::binop(&left, OpCode::from(&op), &right);

                    if let Err(msg) = result {
                        return self.panic_and_throw(msg);
                    } else {
                        self.op_push(result.unwrap());
                    }
                }
                OpCode::IsNull => {
                    let is_null = self.op_pop().is_none();
                    self.op_push(AmaValue::Bool(is_null));
                }
                OpCode::OpInvert | OpCode::OpNot => {
                    let op_ref = self.op_pop();
                    let operand = op_ref;
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
                OpCode::OpIndexGet => {
                    let idx_ref = self.op_pop();
                    let idx = idx_ref.take_int();
                    let target = self.op_pop();
                    match target {
                        //TODO - Optimization: Check at compile if string is going to get indexed
                        //generate graphemes ahead of time.
                        AmaValue::Str(Cow::Borrowed(ref string)) =>{
                            if idx < 0 {
                               self.panic_and_throw("Erro de índice inválido. Strings só podem ser indexadas com inteiros positivos")?;
                            }
                            let user_char = string.graphemes(true).nth(idx as usize);
                            if let Some(user_char) = user_char {
                                self.op_push(AmaValue::Str(Cow::Borrowed(user_char)));
                            } else {
                                self.panic_and_throw(&format!("Erro de índice inválido. O tamanho da string é {}, mas o índice é {}", string.graphemes(true).count(), idx))?;
                            }
                        }
                        AmaValue::Str(Cow::Owned(ref string)) =>{
                            if idx < 0 {
                               self.panic_and_throw("Erro de índice inválido. Strings só podem ser indexadas com inteiros positivos")?;
                            }
                            let user_char = string.graphemes(true).nth(idx as usize);
                            if let Some(user_char) = user_char {
                                self.op_push(AmaValue::Str(Cow::Owned(String::from(user_char))));
                            } else {
                                self.panic_and_throw(&format!("Erro de índice inválido. O tamanho da string é {}, mas o índice é {}", string.graphemes(true).count(), idx))?;
                            }
                        }
                        AmaValue::Vector(ref vec) =>{
                            match target.vec_index_check(idx){
                                Ok(_) => self.op_push(vec.borrow()[idx as usize].clone()), 
                                Err(err) => self.panic_and_throw(&err)?
                            };
                        }
                        _ => unimplemented!(),
                    }
                }
                OpCode::OpIndexSet => {
                    let value = self.op_pop();
                    let idx_ref = self.op_pop();
                    let idx = idx_ref.take_int();
                    let target = self.op_pop();
                    match target {
                        AmaValue::Vector(ref vec) =>{
                            match target.vec_index_check(idx){
                                Ok(_) => vec.borrow_mut()[idx as usize] = value, 
                                Err(err) => self.panic_and_throw(&err)?
                            };
                        }
                        _ => unimplemented!(),
                    }

                }
                OpCode::GetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id: &str = &self.module.unwrap().names[id_idx];
                    let global = self.module.unwrap().globals.borrow().get(id).unwrap().clone();
                    self.op_push(global);
                }
                OpCode::SetGlobal => {
                    let id_idx = self.get_u16_arg() as usize;
                    let id: &str = &self.module.unwrap().names[id_idx];
                    let value = self.op_pop();
                    self.module.unwrap().globals.borrow_mut().insert(id, value);
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
                            let mut fn_args: &[AmaValue] = &[];
                            if args > 0 {
                                let start = (self.sp - (args - 1)) as usize;
                                fn_args = &self.values[start..=self.sp as usize];
                                self.sp = start as isize - 1;
                            }
                            let result = (native_fn.func)(fn_args, &mut self.alloc);
                            if let Err(ref msg) = result {
                                return self.panic_and_throw(msg);
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
                        write!(built_str, "{}", self.values[i]).unwrap();
                    }
                    //Drop values
                    self.sp = start as isize - 1;
                    self.values.drain((self.sp + 1) as usize..);
                    self.op_push(AmaValue::Str(Cow::Owned(built_str)));
                }
                OpCode::BuildVec => {
                    let args = self.get_byte() as isize;
                    if args == 0 {
                        let alloc_ref =self.alloc_ref(Vec::new());
                        self.op_push(AmaValue::Vector(alloc_ref));
                        self.frames.peek_mut().ip += 1;
                        continue;
                    }
                    let start = (self.sp - (args - 1)) as usize;
                    let elements = AmaValue::Vector(self.alloc_ref(Vec::from(&self.values[start..=self.sp as usize])));
                    self.sp = start as isize - 1;
                    self.op_push(elements);
                    //Drop values
                    self.values.drain(self.sp as usize + 1..);
                }
                OpCode::BuildObj => {
                    let fields_init = self.get_byte() as isize;
                    let registo = match self.op_pop() {
                        AmaValue::Registo(reg) =>  reg,  
                        _=> panic!("Expected registo")
                    };

                    if fields_init == 0 {
                        let alloc_ref =  self.alloc_ref(RegObj::new(
                                registo
                        ));
                        self.op_push(AmaValue::RegObj(alloc_ref));
                        self.frames.peek_mut().ip += 1;
                        continue;
                    }
                    let start = (self.sp - ((fields_init * 2) - 1))  as usize;
                    //let build_args = &self.values[start..=self.sp as usize];
                    let build_args = self.values.drain(start..= self.sp as usize);
                    let reg_obj = RegObj::with_fields(registo, build_args);

                    self.sp = start as isize - 1;
                    let alloc_ref =  self.alloc_ref(reg_obj);
                    self.op_push(AmaValue::RegObj(alloc_ref));
                    //Drop values
                    //self.values.drain(self.sp as usize + 1..);
                }
                OpCode::GetProp => {
                    let field = self.op_pop();
                    let reg_ref = self.op_pop();
                    let reg_obj = reg_ref.take_regobj();
                    self.op_push(reg_obj.borrow().get(&field));
                }
                OpCode::SetProp => {
                    let new_val = self.op_pop();
                    let field = self.op_pop();
                    let reg_ref = self.op_pop().take_regobj();
                    let mut reg_obj = reg_ref.borrow_mut();
                    reg_obj.set(field, new_val);
                }
                OpCode::Unwrap => {
                    let has_default = self.get_byte() == 1;
                    let args = if has_default {
                        (Some(self.op_pop()), self.op_pop())
                    } else {
                        (None, self.op_pop())
                    };

                    match (has_default, &args.1) {
                        (true, AmaValue::None) => {
                            self.op_push(args.0.unwrap());
                        }, 
                        (false, AmaValue::None) => {
                            self.panic_and_throw("Não pode aceder uma referência nula")? ;
                        }, 
                        (_, _) => {
                            self.op_push(args.1);
                        }
                    }
                }
                OpCode::Cast => {
                    let arg = self.get_byte();
                    let new_type = self.op_pop().take_type();
                    let val_ref = self.op_pop();
                    let val = val_ref;
                    if arg == 0 {
                        let cast_res = ama_value::cast(&val, new_type);
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
                    offset_to_line(func.last_i, &self.module.unwrap().src_map),
                    error
                ));
                break;
            }
            err_str.push_str(&format!(
                "    Linha {}, na função {}\n",
                offset_to_line(func.last_i, &self.module.unwrap().src_map),
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
            OpCode::from(&self.module.unwrap().code[self.frames.peek().ip])
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
