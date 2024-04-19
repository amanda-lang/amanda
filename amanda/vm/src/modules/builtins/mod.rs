use crate::ama_value::AmaValue;
use crate::errors::AmaErr;
mod embutidos;
mod utils;

/*Helpers*/
type AmaResult<'a> = Result<AmaValue<'a>, AmaErr>;

utils::builtin_registry! {
    embutidos,
}
