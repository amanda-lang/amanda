use super::utils::exports;
use super::AmaResult;
use crate::alloc::Alloc;
use crate::ama_value::AmaValue;
use crate::values::function::{FuncArgs, NativeFunc};

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

exports! {
    fn(abs),
    fn(raizqd),
    fn(expoente),
    var(PI, AmaValue::F64(std::f64::consts::PI)),
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
