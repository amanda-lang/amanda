use crate::alloc::{Alloc, Ref};
use crate::ama_value::AmaValue;
use crate::errors::AmaErr;
use std::fmt;
use std::fmt::Debug;
use std::fmt::Formatter;

//TODO: Change to Drain iter or something similar
pub type FuncArgs<'a, 'args> = &'args [AmaValue<'a>];

#[derive(Clone, Copy)]
pub struct NativeFunc<'a> {
    pub name: &'a str,
    pub func: fn(FuncArgs<'a, '_>, &mut Alloc<'a>) -> Result<AmaValue<'a>, AmaErr>,
}

impl<'a> Debug for NativeFunc<'a> {
    fn fmt(&self, f: &mut Formatter<'_>) -> fmt::Result {
        write!(f, "NativeFunc").unwrap();
        Ok(())
    }
}

#[derive(Debug, Clone, Copy)]
pub enum FuncModule {
    Main,
    Imported(usize),
}

#[derive(Debug, Clone, Copy)]
pub struct AmaFunc<'a> {
    pub name: &'a str,
    pub start_ip: usize,
    pub ip: usize,
    pub last_i: usize,
    pub bp: isize,
    pub locals: usize,
    pub module: FuncModule,
}
