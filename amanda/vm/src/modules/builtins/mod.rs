use crate::ama_value::AmaValue;
use crate::errors::AmaErr;
mod embutidos;
mod mat;
mod utils;

/*Helpers*/
type AmaResult<'a> = Result<AmaValue<'a>, AmaErr>;
pub(crate) type BuiltinDefs<'a> =
    rustc_hash::FxHashMap<&'a str, rustc_hash::FxHashMap<&'a str, AmaValue<'a>>>;

utils::builtin_defs! {
    embutidos,
    mat
}
