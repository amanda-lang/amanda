use crate::alloc::Ref;
use crate::ama_value::AmaValue;
use crate::values::amatype::Type;
use crate::values::tabela::Tabela;

type RegField = String;

#[derive(Debug)]
pub struct Registo<'a> {
    pub name: &'a str,
    pub fields: Vec<RegField>,
}

#[derive(Debug)]
pub struct RegObj<'a> {
    registo: Ref<'a>,
    state: Tabela<'a>,
}

impl<'a> RegObj<'a> {
    pub fn new(registo: Ref<'a>, state: Tabela<'a>) -> RegObj<'a> {
        RegObj { registo, state }
    }

    pub fn get(&self, field: Ref<'a>) -> Ref<'a> {
        *self.state.get(&field).unwrap()
    }

    pub fn set(&mut self, field: Ref<'a>, value: Ref<'a>) {
        self.state.insert(field, value);
    }

    pub fn reg_name(&self) -> &str {
        match self.registo.inner() {
            AmaValue::Registo(registo) => registo.name,
            _ => unreachable!(),
        }
    }
}
