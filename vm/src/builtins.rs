use crate::ama_value::{AmaValue, FuncArgs, NativeFunc};
use std::borrow::Cow;
use std::collections::HashMap;
use std::io;
use std::io::Write;

fn get_fn_arg<'a>(args: FuncArgs<'a>, idx: usize) -> Result<&AmaValue<'a>, ()> {
    if let Some(ptr) = args {
        //Safety: Args must either be none or point to
        //the first argument of the function.
        // Pointer is valid because it was read from the stack
        unsafe { Ok(&*ptr.offset(idx as isize)) }
    } else {
        Err(())
    }
}

#[inline]
fn new_builtin<'a>(
    name: &'a str,
    func: fn(FuncArgs<'a>) -> AmaValue<'a>,
) -> (&'a str, AmaValue<'a>) {
    (name, AmaValue::NativeFn(NativeFunc { name, func }))
}

fn escrevaln<'a>(args: FuncArgs<'a>) -> AmaValue<'a> {
    let value: &AmaValue = get_fn_arg(args, 0).unwrap();

    println!("{}", value);
    AmaValue::None
}

fn escreva<'a>(args: FuncArgs<'a>) -> AmaValue<'a> {
    let value: &AmaValue = get_fn_arg(args, 0).unwrap();

    print!("{}", value);
    io::stdout().flush().unwrap();
    AmaValue::None
}

fn leia<'a>(args: FuncArgs<'a>) -> AmaValue<'a> {
    escreva(args);

    let mut input = String::from("");
    //TODO: Propagate possible errors to caller
    io::stdin().read_line(&mut input).unwrap();
    //Remove newline at the end
    debug_assert!(
        input.remove(input.len() - 1) == 0xA as char,
        "Removing wrong char"
    );

    AmaValue::Str(Cow::Owned(input))
}

fn leia_int<'a>(args: FuncArgs<'a>) -> AmaValue<'a> {
    if let AmaValue::Str(input) = leia(args) {
        //TODO: Propagate possible errors to caller
        AmaValue::Int(input.parse().unwrap())
    } else {
        unreachable!()
    }
}

fn leia_real<'a>(args: FuncArgs<'a>) -> AmaValue<'a> {
    if let AmaValue::Str(input) = leia(args) {
        //TODO: Propagate possible errors to caller
        AmaValue::F64(input.parse().unwrap())
    } else {
        unreachable!()
    }
}

pub fn load_builtins<'a>() -> HashMap<&'a str, AmaValue<'a>> {
    HashMap::from([
        new_builtin("escrevaln", escrevaln),
        new_builtin("escreva", escreva),
        new_builtin("leia", leia),
        new_builtin("leia_int", leia_int),
        new_builtin("leia_real", leia_real),
    ])
}
