use crate::alloc::Ref;
use rustc_hash::FxHashMap;

pub type Tabela<'a> = FxHashMap<Ref<'a>, Ref<'a>>;
