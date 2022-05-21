use crate::alloc::Alloc;
use crate::ama_value::{AmaValue, FuncArgs, NativeFunc, Type};
use crate::errors::AmaErr;
use std::borrow::Cow;
use std::io;
use std::io::Write;
use unicode_segmentation::UnicodeSegmentation;

/*Helpers*/
type AmaResult<'a> = Result<AmaValue<'a>, AmaErr>;

/* Builtin functions*/
fn escrevaln<'a>(args: FuncArgs, _: &mut Alloc<'a>) -> AmaResult<'a> {
    let value: &AmaValue = args[0].inner();

    println!("{}", value);
    Ok(AmaValue::None)
}

fn escreva<'a>(args: FuncArgs, _: &mut Alloc<'a>) -> AmaResult<'a> {
    let value: &AmaValue = args[0].inner();

    print!("{}", value);
    io::stdout().flush().unwrap();
    Ok(AmaValue::None)
}

fn leia<'a>(args: FuncArgs, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    escreva(args, alloc)?;

    let mut input = String::from("");
    //TODO: Propagate possible errors to caller
    io::stdin().read_line(&mut input).unwrap();
    //Remove newline at the end
    debug_assert!(
        input.remove(input.len() - 1) == 0xA as char,
        "Removing wrong char"
    );

    Ok(AmaValue::Str(Cow::Owned(input)))
}

fn leia_int<'a>(args: FuncArgs, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    if let Ok(AmaValue::Str(input)) = leia(args, alloc) {
        //TODO: Propagate possible errors to caller
        let maybe_int = input.parse::<i64>();
        if let Err(_) = maybe_int {
            Err("Valor introduzido não é um inteiro válido".to_string())
        } else {
            Ok(AmaValue::Int(maybe_int.unwrap()))
        }
    } else {
        unreachable!()
    }
}

fn leia_real<'a>(args: FuncArgs, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    if let Ok(AmaValue::Str(input)) = leia(args, alloc) {
        //TODO: Propagate possible errors to caller
        let maybe_double = input.parse::<f64>();
        if let Err(_) = maybe_double {
            Err("Valor introduzido não é um número real válido".to_string())
        } else {
            Ok(AmaValue::F64(maybe_double.unwrap()))
        }
    } else {
        unreachable!()
    }
}

fn tam<'a>(args: FuncArgs, _: &mut Alloc<'a>) -> AmaResult<'a> {
    let value = args[0].inner();
    match value {
        AmaValue::Str(string) => Ok(AmaValue::Int(
            (&string as &str).graphemes(true).count() as i64
        )),
        AmaValue::Vector(vec) => Ok(AmaValue::Int(vec.len() as i64)),
        _ => unreachable!("function called with something of invalid type"),
    }
}

fn txt_contem<'a>(args: FuncArgs, _: &mut Alloc<'a>) -> AmaResult<'a> {
    let haystack = args[0].inner();
    let needle = args[1].inner();
    match (haystack, needle) {
        (AmaValue::Str(haystack), AmaValue::Str(needle)) => Ok(AmaValue::Bool(
            (&haystack as &str).contains(&needle as &str),
        )),
        _ => unreachable!("function called with something of invalid type"),
    }
}

fn vec<'a>(args: FuncArgs, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let el_type = args[0].inner().take_type();
    let size = args[1].inner().take_int();
    if size < 0 {
        return Err(String::from(
            "Tamanho de vector deve ser um número inteiro positivo",
        ));
    }
    let new_vec = match el_type {
        Type::Int => AmaValue::Vector(vec![alloc.alloc_ref(AmaValue::Int(0)); size as usize]),
        Type::Real => AmaValue::Vector(vec![alloc.alloc_ref(AmaValue::F64(0.0)); size as usize]),
        Type::Bool => AmaValue::Vector(vec![alloc.alloc_ref(AmaValue::Bool(false)); size as usize]),
        Type::Texto => AmaValue::Vector(vec![
            alloc.alloc_ref(AmaValue::Str(Cow::Owned(
                String::new()
            )));
            size as usize
        ]),
        _ => unreachable!("Only primitives types should have this"),
    };
    Ok(new_vec)
}

#[inline]
fn new_builtin<'a>(
    name: &'a str,
    func: fn(FuncArgs, &mut Alloc<'a>) -> AmaResult<'a>,
) -> (&'a str, AmaValue<'a>) {
    (name, (AmaValue::NativeFn(NativeFunc { name, func })))
}

pub fn load_builtins<'a>() -> [(&'a str, AmaValue<'a>); 12] {
    [
        new_builtin("escrevaln", escrevaln),
        new_builtin("escreva", escreva),
        new_builtin("leia", leia),
        new_builtin("leia_int", leia_int),
        new_builtin("leia_real", leia_real),
        new_builtin("tam", tam),
        new_builtin("vec", vec),
        new_builtin("txt_contem", txt_contem),
        ("int", AmaValue::Type(Type::Int)),
        ("real", AmaValue::Type(Type::Real)),
        ("bool", AmaValue::Type(Type::Bool)),
        ("texto", AmaValue::Type(Type::Texto)),
    ]
}
