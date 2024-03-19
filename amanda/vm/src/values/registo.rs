use crate::alloc::Ref;
use crate::ama_value::AmaValue;
use crate::ama_value::AmaValue;
use crate::values::amatype::Type;
use rustc_hash::FxHashMap;

pub type Tabela<'a> = FxHashMap<AmaValue<'a>, AmaValue<'a>>;

type RegField = String;

#[derive(Debug)]
pub struct Registo<'a> {
    pub name: &'a str,
    pub fields: Vec<RegField>,
}

#[derive(Debug)]
pub struct RegObj<'a> {
    registo: &'a Registo<'a>,
    state: Tabela<'a>,
}

impl<'a> RegObj<'a> {
    pub fn new(registo: &'a Registo<'a>, state: Tabela<'a>) -> RegObj<'a> {
        RegObj { registo, state }
    }

    pub fn get(&self, field: &'a AmaValue<'a>) -> &'a AmaValue<'a> {
        self.state.get(&field).unwrap()
    }

    pub fn set(&mut self, field: AmaValue<'a>, value: AmaValue<'a>) {
        self.state.insert(field, value);
    }

    pub fn reg_name(&self) -> &str {
        self.registo.name
    }
}
