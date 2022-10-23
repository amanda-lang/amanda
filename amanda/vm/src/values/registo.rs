use crate::alloc::Ref;
use crate::values::amatype::Type;
use crate::values::tabela::Tabela;

type RegField<'a> = (&'a str, Type);

#[derive(Debug)]
pub struct Registo<'a> {
    pub name: &'a str,
    pub fields: Vec<RegField<'a>>,
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
}
