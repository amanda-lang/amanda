macro_rules! export {
    (fn($fn:expr)) => {
        (
            stringify!($fn),
            (AmaValue::NativeFn(NativeFunc {
                name: stringify!($fn),
                func: $fn,
            })),
        )
    };

    (var($var:expr, $e:expr)) => {
        (stringify!($var), $e)
    };
}

macro_rules! exports {
    (
        $($rule:ident($($es: expr),+)),+
    ) => {

        pub fn exports<'a>() -> rustc_hash::FxHashMap<&'a str, AmaValue<'a>> {
            let mut map: rustc_hash::FxHashMap<&'a str, AmaValue<'a>> = Default::default();
            $(
                let (ident, val) = super::utils::export!($rule($($es),+));
                map.insert(ident, val);
            )+
            map
        }
    };
}

macro_rules! builtin_defs {
    ($($mod:ident),+) => {
        pub fn definitions<'a>() -> BuiltinDefs<'a> {
            let mut defs: BuiltinDefs<'a> = Default::default();
            $(
                defs.insert(stringify!($mod), $mod::exports());
            )+
            defs
        }
    };
}

pub(super) use builtin_defs;
pub(super) use export;
pub(super) use exports;
