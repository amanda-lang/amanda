use crate::alloc::Ref;
use crate::errors::AmaErr;
use crate::opcode::OpCode;
use crate::values::amatype::Type;
use crate::values::function::{AmaFunc, NativeFunc};
use crate::values::registo::{RegObj, Registo};
use std::borrow::Cow;
use std::cell::RefCell;
use std::convert::From;
use std::fmt;
use std::fmt::Debug;
use std::fmt::{Display, Formatter, Write};
use std::hash::{Hash, Hasher};
use std::rc::Rc;

pub type RcCell<T> = Rc<RefCell<T>>;

macro_rules! arith_ops {
    ($res_type: ident, $left: ident, $op:tt, $op_fn: ident, $right: ident) => {
        match $res_type {
            Type::Real => Ok(AmaValue::F64($left.take_float() $op $right.take_float())),
            Type::Int => {
                    let result = $left.take_int().$op_fn($right.take_int());
                    if let Some(int) = result {
                        Ok(AmaValue::Int(int))
                    } else {
                        Err("Erro ao realizar operação aritmética. Resultado fora do intervalo de inteiros representáveis")
                    }
                }
            _ => unimplemented!("Operand type not supported"),
        }
    };
}

macro_rules! comp_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        Ok(match $res_type {
            Type::Real => AmaValue::Bool($left.take_float() $op $right.take_float()),
            Type::Int => AmaValue::Bool($left.take_int() $op $right.take_int()),
            _ => unimplemented!("Operand type not supported"),
        })
    };
}

macro_rules! eq_ops {
    ($res_type: ident, $left: ident, $op: tt, $right: ident) => {
        Ok(match $res_type {
            Type::Int => AmaValue::Bool($left.take_int() $op $right.take_int()),
            Type::Real => AmaValue::Bool($left.take_float() $op $right.take_float()),
            Type::Bool => AmaValue::Bool($left.take_bool() $op $right.take_bool()),
            Type::Texto => AmaValue::Bool($left.take_str() $op $right.take_str()),
            _ => unimplemented!("Operand type not supported"),
        })
    };
}

macro_rules! is_fn {
    ($fn_name: ident, $to_match: path) => {
        pub fn $fn_name(&self) -> bool {
            if let $to_match(_) = self {
                true
            } else {
                false
            }
        }
    };
}
#[derive(Debug)]
pub enum AmaValue<'a> {
    Int(i64),
    F64(f64),
    Bool(bool),
    Func(AmaFunc<'a>),
    NativeFn(NativeFunc<'a>),
    Type(Type),
    None,
    //Heap objects
    Vector(RcCell<Vec<AmaValue<'a>>>),
    //TODO: Change this into a Box<str>,
    Str(Cow<'a, str>),
    Registo(&'a Registo<'a>),
    RegObj(RcCell<RegObj<'a>>),
    Variant(u64, Option<Rc<Vec<AmaValue<'a>>>>),
}

impl<'a> AmaValue<'a> {
    pub fn get_type(&self) -> Type {
        match self {
            AmaValue::Str(_) => Type::Texto,
            AmaValue::Int(_) => Type::Int,
            AmaValue::F64(_) => Type::Real,
            AmaValue::Bool(_) => Type::Bool,
            AmaValue::Vector(_) => Type::Vector,
            _ => unimplemented!("Cannot return type for this value: {:?}", self),
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

    pub fn take_type(&self) -> Type {
        match self {
            AmaValue::Type(t) => *t,
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

    pub fn take_regobj(&self) -> RcCell<RegObj<'a>> {
        if let AmaValue::RegObj(val) = self {
            Rc::clone(&val)
        } else {
            panic!("Value is not a bool")
        }
    }

    is_fn!(is_float, AmaValue::F64);
    is_fn!(is_str, AmaValue::Str);
    is_fn!(is_bool, AmaValue::Bool);
    is_fn!(is_int, AmaValue::Int);

    pub fn is_none(&self) -> bool {
        match self {
            AmaValue::None => true,
            _ => false,
        }
    }

    pub fn vec_index_check(&self, idx: i64) -> Result<(), AmaErr> {
        if idx < 0 {
            return Err(String::from(
                "Erro de índice inválido. Vectores só podem ser indexados com inteiros positivos",
            ));
        }
        //Check bounds
        let vec = match self {
            AmaValue::Vector(vec) => vec.borrow(),
            _ => unreachable!(),
        };
        if idx as usize >= vec.len() {
            return Err(format!(
                "Erro de índice inválido. O tamanho do vector é {}, mas tentou aceder o índice {}",
                vec.len(),
                idx
            ));
        }
        Ok(())
    }

    pub fn binop(left: &Self, op: OpCode, right: &Self) -> Result<Self, &'a str> {
        let res_type = if left.is_float() || right.is_float() {
            Type::Real
        } else if left.is_int() && right.is_int() {
            Type::Int
        } else if left.is_bool() && right.is_bool() {
            Type::Bool
        } else if left.is_str() && right.is_str() {
            Type::Texto
        } else if left.is_none() && right.is_str() {
            Type::Texto
        } else {
            unimplemented!("Error is not implemented")
        };
        match op {
            OpCode::OpAdd => arith_ops!(res_type, left, +, checked_add, right),
            OpCode::OpMinus => arith_ops!(res_type, left, -, checked_sub, right),
            OpCode::OpMul => arith_ops!(res_type, left, *, checked_mul, right),
            OpCode::OpModulo => {
                if right.take_float() == 0.0 {
                    Err("não pode calcular o resto da divisão de um número por zero")
                } else {
                    arith_ops!(res_type, left, %, checked_rem, right)
                }
            }
            OpCode::OpDiv => {
                if right.take_float() == 0.0 {
                    Err("não pode dividir um número por zero")
                } else {
                    Ok(AmaValue::F64(left.take_float() / right.take_float()))
                }
            }
            OpCode::OpFloorDiv => {
                if right.take_int() == 0 {
                    Err("não pode dividir um número por zero")
                } else {
                    let res_type = Type::Int;
                    arith_ops!(res_type, left, /, checked_div, right)
                }
            }
            OpCode::OpAnd => Ok(AmaValue::Bool(left.take_bool() && right.take_bool())),
            OpCode::OpOr => Ok(AmaValue::Bool(left.take_bool() || right.take_bool())),
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
            AmaValue::Str(string) => AmaValue::Str(Clone::clone(string)),
            AmaValue::Int(int) => AmaValue::Int(*int),
            AmaValue::F64(float) => AmaValue::F64(*float),
            AmaValue::Bool(val) => AmaValue::Bool(*val),
            AmaValue::None => AmaValue::None,
            AmaValue::Func(function) => AmaValue::Func(*function),
            AmaValue::NativeFn(func) => AmaValue::NativeFn(*func),
            AmaValue::Type(t) => AmaValue::Type(*t),
            AmaValue::Vector(ref vec) => AmaValue::Vector(Rc::clone(vec)),
            AmaValue::RegObj(ref obj) => AmaValue::RegObj(Rc::clone(obj)),
            AmaValue::Registo(reg) => AmaValue::Registo(reg),
            AmaValue::Variant(tag, items) => match items {
                Some(ref items) => AmaValue::Variant(*tag, Some(Rc::clone(items))),
                None => AmaValue::Variant(*tag, None),
            },
            _ => unimplemented!("Cannot clone value of type"),
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
            AmaValue::Vector(vec) => {
                let vec = vec.borrow();
                let mut res = String::new();
                write!(res, "[").unwrap();
                vec.iter().enumerate().for_each(|(i, val)| {
                    if i == vec.len() - 1 {
                        write!(res, "{}", val).unwrap();
                        return;
                    }
                    write!(res, "{}, ", val).unwrap();
                });
                write!(res, "]").unwrap();
                write!(f, "{}", res)
            }
            AmaValue::None => write!(f, "nulo"),
            AmaValue::RegObj(reg) => {
                write!(f, "<Instância do tipo {}>", reg.borrow().reg_name())
            }
            AmaValue::Variant(tag, _) => {
                write!(f, "<Variante({})>", tag)
            }
            _ => unimplemented!(),
        }
    }
}

pub fn cast<'a>(value: &AmaValue, target: Type) -> Result<AmaValue<'a>, String> {
    match target {
        Type::Texto => Ok(AmaValue::Str(Cow::Owned(format!("{}", value)))),
        Type::Int => match value {
            AmaValue::F64(_) => Ok(AmaValue::Int(value.take_int())),
            AmaValue::Str(string) => {
                let maybe_int = string.parse::<i64>();
                if let Err(_) = maybe_int {
                    Err(format!(
                        "A sequência de caracteres '{}' não é um inteiro válido",
                        string
                    ))
                } else {
                    Ok(AmaValue::Int(maybe_int.unwrap()))
                }
            }
            _ => unimplemented!(
                "Fatal error! Should not reach conversion between: {:?} and {:?}",
                value,
                target
            ),
        },
        Type::Real => match value {
            AmaValue::Int(_) => Ok(AmaValue::F64(value.take_float())),
            AmaValue::Str(string) => {
                let maybe_real = string.parse::<f64>();
                if let Err(_) = maybe_real {
                    Err(format!(
                        "A sequência de caracteres '{}' não é um número real válido",
                        string
                    ))
                } else {
                    Ok(AmaValue::F64(maybe_real.unwrap()))
                }
            }
            _ => unimplemented!(
                "Fatal error! Should not reach conversion between: {:?} and {:?}",
                value,
                target
            ),
        },
        Type::Bool => match value {
            AmaValue::Int(int) => Ok(AmaValue::Bool(*int != 0)),
            AmaValue::F64(double) => Ok(AmaValue::Bool(*double != 0.0)),
            AmaValue::Str(string) => Ok(AmaValue::Bool(string.as_ref() != "")),
            _ => unimplemented!(
                "Fatal error! Should not reach conversion between: {:?} and {:?}",
                value,
                target
            ),
        },
        _ => unreachable!("Fraudulent cast!"),
    }
}

impl<'a> PartialEq for AmaValue<'a> {
    fn eq(&self, other: &Self) -> bool {
        AmaValue::binop(self, OpCode::OpEq, other)
            .unwrap()
            .take_bool()
    }
}

impl<'a> Eq for AmaValue<'a> {}

impl<'a> Hash for AmaValue<'a> {
    fn hash<H: Hasher>(&self, state: &mut H) {
        match self {
            AmaValue::Int(int) => int.hash(state),
            AmaValue::Bool(boolean) => boolean.hash(state),
            AmaValue::Str(string) => string.hash(state),
            _ => unimplemented!("Can't hash whatever type was sent in"),
        };
    }
}

#[inline]
pub fn check_cast(val_t: Type, target: Type) -> bool {
    val_t as u8 == target as u8
}
