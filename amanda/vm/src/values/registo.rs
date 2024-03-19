use crate::alloc::Ref;
use crate::ama_value::AmaValue;
use crate::values::amatype::Type;
use rustc_hash::FxHashMap;
use std::iter::FromIterator;

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

    pub fn with_fields(registo: &'a Registo<'a>, fields: &'a [AmaValue<'a>]) -> RegObj<'a> {
        let init_pairs = fields[0..]
            .iter()
            .step_by(2)
            .zip(fields[1..].iter().step_by(2))
            .map(|pair| (*pair.0, *pair.1));
        let state = Tabela::from_iter(init_pairs);
        RegObj { registo, state }
    }

    pub fn get(&self, field: &'a AmaValue<'a>) -> AmaValue<'a> {
        self.state.get(&field).unwrap().clone()
    }

    pub fn set(&mut self, field: AmaValue<'a>, value: AmaValue<'a>) {
        self.state.insert(field, value);
    }

    pub fn reg_name(&self) -> &str {
        self.registo.name
    }
}
