use super::utils::definitions;
use super::AmaResult;
use crate::alloc::Alloc;
use crate::ama_value::AmaValue;
use crate::values::amatype::Type;
use crate::values::function::{FuncArgs, NativeFunc};
use std::borrow::Cow;
use std::io;
use std::io::Write;
use unicode_segmentation::UnicodeSegmentation;

/* Builtin functions*/
fn escrevaln<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let value = &args[0];

    println!("{}", value);
    Ok(AmaValue::None)
}

fn escreva<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let value = &args[0];

    print!("{}", value);
    io::stdout().flush().unwrap();
    Ok(AmaValue::None)
}

fn leia<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
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

fn leia_int<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let input = leia(args, alloc);
    if input.is_ok() {
        //TODO: Propagate possible errors to caller
        let maybe_int = input.unwrap().take_str().parse::<i64>();
        if let Err(_) = maybe_int {
            Err("Valor introduzido não é um inteiro válido".to_string())
        } else {
            Ok(AmaValue::Int(maybe_int.unwrap()))
        }
    } else {
        unreachable!()
    }
}

fn leia_real<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let input = leia(args, alloc);
    if input.is_ok() {
        //TODO: Propagate possible errors to caller
        let maybe_double = input.unwrap().take_str().parse::<f64>();
        if let Err(_) = maybe_double {
            Err("Valor introduzido não é um número real válido".to_string())
        } else {
            Ok(AmaValue::F64(maybe_double.unwrap()))
        }
    } else {
        unreachable!()
    }
}

fn tam<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let value = &args[0];
    match value {
        AmaValue::Str(string) => Ok(AmaValue::Int(
            (&string as &str).graphemes(true).count() as i64
        )),
        AmaValue::Vector(vec) => Ok(AmaValue::Int(vec.borrow().len() as i64)),
        _ => unreachable!("function called with something of invalid type"),
    }
}

fn txt_contem<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let haystack = &args[0];
    let needle = &args[1];
    match (haystack, needle) {
        (AmaValue::Str(haystack), AmaValue::Str(needle)) => {
            Ok((AmaValue::Bool((haystack as &str).contains(needle as &str))))
        }
        _ => unreachable!("function called with something of invalid type"),
    }
}

//TODO: Maybe optimize this
fn build_vec<'a>(
    dim: usize,
    n_dims: usize,
    dims: &[AmaValue],
    el_type: Type,
    alloc: &mut Alloc<'a>,
) -> Vec<AmaValue<'a>> {
    let size = dims[dim].take_int() as usize;
    if dim == n_dims {
        match el_type {
            Type::Int => vec![AmaValue::Int(0); size as usize],
            Type::Real => vec![AmaValue::F64(0.0); size],
            Type::Bool => vec![AmaValue::Bool(false); size],
            Type::Texto => vec![AmaValue::Str(Cow::Owned(String::new())); size],
            _ => unreachable!("Only primitives types should have this"),
        }
    } else {
        if size == 0 {
            Vec::with_capacity(0)
        } else {
            let inner = build_vec(dim + 1, n_dims, dims, el_type, alloc);
            let mut container = Vec::with_capacity(inner.len());
            container.resize_with(size, || (AmaValue::Vector(alloc.alloc_ref(inner.clone()))));
            container
        }
    }
}

fn vec<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let el_type = args[0].take_type();
    let dims = &args[1..];
    let n_dims = dims.len();
    for dim in dims {
        let size = dim.take_int();
        if size < 0 {
            return Err(String::from(
                "Dimensões de um vector devem ser especificidas por números inteiros positivos",
            ));
        }
    }
    let built_vec = build_vec(0, n_dims - 1, dims, el_type, alloc);
    let vec = AmaValue::Vector(alloc.alloc_ref(built_vec));
    Ok(vec)
}

fn anexa<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let vec = match &args[0] {
        AmaValue::Vector(vec) => vec,
        _ => unreachable!("Something bad is happening"),
    };
    vec.borrow_mut().push(args[1].clone());
    Ok(AmaValue::None)
}

fn remova<'a>(args: FuncArgs<'a, '_>, _: &mut Alloc<'a>) -> AmaResult<'a> {
    let vec = &args[0];
    let idx = args[1].take_int();
    vec.vec_index_check(idx)?;
    match vec {
        AmaValue::Vector(vec) => Ok(vec.borrow_mut().remove(idx as usize)),
        _ => unreachable!("Invalid call!"),
    }
}

fn abs<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::F64(number.abs()))
}

fn expoente<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let base = args[0].take_float();
    let exp = args[1].take_float();
    Ok(AmaValue::F64(base.powf(exp)))
}

fn raizqd<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::F64(number.sqrt()))
}

fn arredonda<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::Int(number.round() as i64))
}

fn piso<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::Int(number.floor() as i64))
}

fn teto<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::Int(number.ceil() as i64))
}

fn sen<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::F64(number.sin()))
}

fn cos<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::F64(number.cos()))
}

fn tan<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    Ok(AmaValue::F64(number.tan()))
}

fn log<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let number = args[0].take_float();
    let base = args[1].take_float();
    Ok(AmaValue::F64(number.log(base)))
}

fn grausprad<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let degrees = args[0].take_float();
    Ok(AmaValue::F64(degrees.to_radians()))
}

fn radpgraus<'a>(args: FuncArgs<'a, '_>, alloc: &mut Alloc<'a>) -> AmaResult<'a> {
    let rad = args[0].take_float();
    Ok(AmaValue::F64(rad.to_degrees()))
}

#[inline]
fn new_builtin<'a>(
    name: &'a str,
    func: fn(FuncArgs<'a, '_>, &mut Alloc<'a>) -> AmaResult<'a>,
) -> (&'a str, AmaValue<'a>) {
    (name, (AmaValue::NativeFn(NativeFunc { name, func })))
}

definitions! {
    var(int, AmaValue::Type(Type::Int)),
    var(real, AmaValue::Type(Type::Real)),
    var(bool, AmaValue::Type(Type::Bool)),
    var(texto, AmaValue::Type(Type::Texto)),
    var(PI, AmaValue::F64(std::f64::consts::PI)),
    fn(escrevaln),
    fn(escreva),
    fn(leia),
    fn(leia),
    fn(leia_int),
    fn(leia_real),
    fn(tam),
    fn(vec),
    fn(anexa),
    fn(remova),
    fn(txt_contem),
    fn(abs),
    fn(raizqd),
    fn(expoente),
    fn(arredonda),
    fn(piso),
    fn(teto),
    fn(sen),
    fn(cos),
    fn(tan),
    fn(log),
    fn(grausprad),
    fn(radpgraus)
}
