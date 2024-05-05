use crate::alloc::Ref;
use crate::ama_value::AmaValue;
use crate::values::amatype::Type;
use rustc_hash::FxHashMap;
use std::iter::FromIterator;
use std::vec::Drain;

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
    pub fn new(registo: &'a Registo<'a>) -> RegObj<'a> {
        RegObj {
            registo,
            state: Tabela::default(),
        }
    }

    pub fn with_fields(
        registo: &'a Registo<'a>,
        mut fields: Drain<'_, AmaValue<'a>>,
    ) -> RegObj<'a> {
        let mut state = Tabela::default();
        loop {
            let maybe_key = fields.next();
            if maybe_key.is_none() {
                break;
            }
            let key = maybe_key.expect("Pair starts with key");
            let value = fields.next().expect("Key always comes with value");
            state.insert(key, value);
        }
        RegObj { registo, state }
    }

    pub fn get(&self, field: &AmaValue<'a>) -> AmaValue<'a> {
        self.state.get(&field).unwrap().clone()
    }

    pub fn set(&mut self, field: AmaValue<'a>, value: AmaValue<'a>) {
        self.state.insert(field, value);
    }

    pub fn reg_name(&self) -> &str {
        self.registo.name
    }
}
