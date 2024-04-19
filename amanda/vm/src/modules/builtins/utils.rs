macro_rules! definition {
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

macro_rules! definitions {
    (
        $($rule:ident($($es: expr),+)),+
    ) => {

        pub fn declarations<'a>() -> rustc_hash::FxHashMap<&'a str, AmaValue<'a>> {
            let mut map: rustc_hash::FxHashMap<&'a str, AmaValue<'a>> = Default::default();
            $(
                let (ident, val) = super::utils::definition!($rule($($es),+));
                map.insert(ident, val);
            )+
            map
        }
    };
}

macro_rules! builtin_registry {
    () => {};
}

pub(super) use builtin_registry;
pub(super) use definition;
pub(super) use definitions;
