use crate::values::function::AmaFunc;
use crate::values::registo::Registo;
use std::borrow::Cow;
use std::collections::HashMap;
use std::io::Cursor;
use std::io::Read;
use std::str::FromStr;

#[derive(Debug)]
pub struct Module<'a> {
    pub name: String,
    pub builtin: bool,
    pub constants: Vec<AmaValue<'a>>,
    pub names: Vec<String>,
    pub code: Vec<u8>,
    pub main: AmaFunc<'a>,
    pub functions: Vec<AmaFunc<'a>>,
    pub registos: Vec<Registo<'a>>,
    pub src_map: Vec<usize>,
    pub imports: Vec<Module<'a>>,
}
