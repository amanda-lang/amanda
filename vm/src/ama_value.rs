use crate::vm::OpCode;
use std::convert::From;
use std::fmt;
use std::fmt::{Display, Formatter};
use std::str::FromStr;

macro_rules! arith_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            AmaValue::F64(_) => AmaValue::F64($left.take_float() $op $right.take_float()),
            AmaValue::Int(_) => AmaValue::Int($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

macro_rules! comp_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            AmaValue::F64(_) => AmaValue::Bool($left.take_float() $op $right.take_float()),
            AmaValue::Int(_) => AmaValue::Bool($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

macro_rules! eq_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        match $res_type {
            AmaValue::Int(_) => AmaValue::Bool($left.take_int() $op $right.take_int()),
            AmaValue::F64(_) => AmaValue::Bool($left.take_float() $op $right.take_float()),
            AmaValue::Bool(_) => AmaValue::Bool($left.take_bool() $op $right.take_bool()),
            AmaValue::Str(_) => AmaValue::Bool($left.take_str() $op $right.take_str()),
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

//TODO: Find a 'safe' way to do this
pub type FuncArgs<'a> = Option<*const AmaValue<'a>>;

#[derive(Debug, Clone, Copy)]
pub struct NativeFunc<'a> {
    pub name: &'a str,
    pub func: fn(FuncArgs<'a>) -> AmaValue<'a>,
}

#[derive(Debug, Clone, Copy)]
pub struct AmaFunc<'a> {
    pub name: &'a str,
    pub start_ip: usize,
    pub ip: usize,
    pub bp: isize,
    pub locals: usize,
}

#[derive(Debug)]
pub enum AmaValue<'a> {
    Str(String),
    Int(i64),
    F64(f64),
    Bool(bool),
    Func(AmaFunc<'a>),
    NativeFn(NativeFunc<'a>),
    None,
}

impl<'a> AmaValue<'a> {
    pub fn is_float(&self) -> bool {
        if let AmaValue::F64(_) = self {
            true
        } else {
            false
        }
    }

    pub fn take_float(&self) -> f64 {
        match self {
            AmaValue::F64(float) => *float,
            AmaValue::Int(int) => *int as f64,
            _ => panic!("Value is not a float"),
        }
    }

    pub fn take_int(&self) -> i64 {
        match self {
            AmaValue::Int(int) => *int,
            AmaValue::F64(float) => *float as i64,
            _ => panic!("Value is not an int"),
        }
    }

    pub fn take_str(&self) -> &str {
        if let AmaValue::Str(string) = self {
            string
        } else {
            panic!("Value is not an str")
        }
    }

    pub fn take_bool(&self) -> bool {
        if let AmaValue::Bool(val) = self {
            *val
        } else {
            panic!("Value is not a bool")
        }
    }

    pub fn take_func(self) -> AmaFunc<'a> {
        if let AmaValue::Func(func) = self {
            func
        } else {
            panic!("Value is not a func")
        }
    }

    pub fn is_str(&self) -> bool {
        if let AmaValue::Str(_) = self {
            true
        } else {
            false
        }
    }

    pub fn is_bool(&self) -> bool {
        if let AmaValue::Bool(_) = self {
            true
        } else {
            false
        }
    }

    pub fn is_int(&self) -> bool {
        if let AmaValue::Int(_) = self {
            true
        } else {
            false
        }
    }

    pub fn binop(left: Self, op: OpCode, right: Self) -> Self {
        let res_type = if left.is_float() || right.is_float() {
            AmaValue::F64(0.0)
        } else if left.is_int() && right.is_int() {
            AmaValue::Int(0)
        } else if left.is_bool() && right.is_bool() {
            AmaValue::Bool(false)
        } else if left.is_str() && right.is_str() {
            AmaValue::Str(String::from(""))
        } else {
            unimplemented!("Error is not implemented")
        };
        match op {
            OpCode::OpAdd => arith_ops!(res_type, left, +, right),
            OpCode::OpMinus => arith_ops!(res_type, left, -, right),
            OpCode::OpMul => arith_ops!(res_type, left, *, right),
            OpCode::OpModulo => arith_ops!(res_type, left, %, right),
            OpCode::OpDiv => AmaValue::F64(left.take_float() / right.take_float()),
            OpCode::OpFloorDiv => AmaValue::Int(left.take_int() / right.take_int()),
            OpCode::OpAnd => AmaValue::Bool(left.take_bool() && right.take_bool()),
            OpCode::OpOr => AmaValue::Bool(left.take_bool() || right.take_bool()),
            OpCode::OpEq => eq_ops!(res_type, left, ==, right),
            OpCode::OpNotEq => eq_ops!(res_type, left, !=,  right),
            OpCode::OpGreater => comp_ops!(res_type, left, >, right),
            OpCode::OpGreaterEq => comp_ops!(res_type, left, >=, right),
            OpCode::OpLess => comp_ops!(res_type, left, <, right),
            OpCode::OpLessEq => comp_ops!(res_type, left, <=, right),
            _ => unimplemented!("Op {:?} has not yet been implemented", op),
        }
    }
}

impl Clone for AmaValue<'_> {
    fn clone(&self) -> Self {
        match self {
            AmaValue::Str(string) => AmaValue::Str(String::clone(string)),
            AmaValue::Int(int) => AmaValue::Int(*int),
            AmaValue::F64(float) => AmaValue::F64(*float),
            AmaValue::Bool(val) => AmaValue::Bool(*val),
            AmaValue::None => AmaValue::None,
            AmaValue::Func(function) => AmaValue::Func(function.clone()),
            AmaValue::NativeFn(func) => AmaValue::NativeFn(*func),
        }
    }
}

impl<'a> FromStr for AmaValue<'a> {
    type Err = ();

    fn from_str(constant: &str) -> Result<AmaValue<'a>, ()> {
        if constant == "verdadeiro" || constant == "falso" {
            let bool_val = if constant == "falso" { false } else { true };
            return Ok(AmaValue::Bool(bool_val));
        }
        let maybe_int = constant.parse::<i64>();
        let maybe_float = constant.parse::<f64>();
        if maybe_int.is_ok() {
            return Ok(AmaValue::Int(maybe_int.unwrap()));
        } else if maybe_float.is_ok() {
            return Ok(AmaValue::F64(maybe_float.unwrap()));
        } else {
            let slice: &str = if &constant[..1] == "\"" || &constant[..1] == "\'" {
                &constant[1..constant.len() - 1]
            } else {
                constant
            };
            return Ok(AmaValue::Str(String::from(slice)));
        }
    }
}

impl Display for AmaValue<'_> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        match self {
            AmaValue::Str(string) => write!(f, "{}", string),
            AmaValue::Int(integer) => write!(f, "{}", integer),
            AmaValue::F64(float) => {
                if float.fract() == 0.0 {
                    return write!(f, "{}.0", float);
                }
                write!(f, "{}", float)
            }
            AmaValue::Bool(val) => {
                let val_str = if *val { "verdadeiro" } else { "falso" };
                write!(f, "{}", val_str)
            }
            AmaValue::None => panic!("None value should not be printed"),
            _ => write!(f, "{:?}", self),
        }
    }
}
