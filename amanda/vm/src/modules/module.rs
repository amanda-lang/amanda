use crate::ama_value::AmaValue;
use crate::modules::builtins::BuiltinDefs;
use crate::values::function::AmaFunc;
use crate::values::registo::Registo;
use rustc_hash::FxHashMap;
use std::cell::RefCell;

pub type MGlobals<'a> = FxHashMap<&'a str, AmaValue<'a>>;

#[derive(Debug)]
pub struct Module<'a> {
    pub name: String,
    pub builtin: bool,
    pub constants: Vec<AmaValue<'a>>,
    pub names: Vec<String>,
    pub code: Vec<u8>,
    pub main: AmaFunc<'a>,
    pub functions: Vec<AmaFunc<'a>>,
    pub globals: RefCell<MGlobals<'a>>,
    pub registos: Vec<Registo<'a>>,
    pub src_map: Vec<usize>,
}

impl<'a> Module<'a> {
    pub fn initialize(&self, builtin_defs: &BuiltinDefs<'a>) {
        if self.builtin {
            //TODO: Figure this out
            match builtin_defs.get(self.name.as_str()) {
                Some(defs) => {
                    for (def, val) in defs {
                        self.globals.borrow_mut().insert(*def, val.clone());
                    }
                }
                None => panic!("Module {} has not yet been declared!!!", self.name),
            }
        } else {
            for func in self.functions.iter() {
                self.globals
                    .borrow_mut()
                    .insert(func.name, AmaValue::Func(*func));
            }
        }
    }
}
