use crate::ama_value::AmaValue;
use crate::errors::AmaErr;
mod embutidos;

/*Helpers*/
type AmaResult<'a> = Result<AmaValue<'a>, AmaErr>;

builtin_registry! {
    embutidos,
}
