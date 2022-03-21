use crate::ama_value::AmaFunc;
use std::str::FromStr;

#[derive(Debug)]
pub enum Const {
    Str(String),
    Int(i64),
    Double(f64),
    Bool(bool),
}

#[derive(Debug)]
pub struct Program<'a> {
    pub constants: Vec<Const>,
    pub ops: Vec<u8>,
    pub main: AmaFunc<'a>,
}

//TODO: Implement From after i move Const to it's own file

impl Const {
    pub fn get_str(&self) -> &String {
        match self {
            Self::Str(string) => &string,
            _ => panic!("Const is not a string"),
        }
    }
}

impl<'a> FromStr for Const {
    type Err = ();

    fn from_str(constant: &str) -> Result<Const, ()> {
        if constant == "verdadeiro" || constant == "falso" {
            let bool_val = if constant == "falso" { false } else { true };
            return Ok(Const::Bool(bool_val));
        }
        let maybe_int = constant.parse::<i64>();
        let maybe_float = constant.parse::<f64>();
        if maybe_int.is_ok() {
            return Ok(Const::Int(maybe_int.unwrap()));
        } else if maybe_float.is_ok() {
            return Ok(Const::Double(maybe_float.unwrap()));
        } else {
            let slice: &str = if &constant[..1] == "\"" || &constant[..1] == "\'" {
                &constant[1..constant.len() - 1]
            } else {
                constant
            };
            return Ok(Const::Str(String::from(slice)));
        }
    }
}
