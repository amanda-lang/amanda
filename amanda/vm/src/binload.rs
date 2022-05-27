use crate::alloc::{Alloc, Ref};
use crate::ama_value::{AmaFunc, AmaValue};
use std::borrow::Cow;
use std::collections::HashMap;
use std::io::Cursor;
use std::io::Read;
use std::str::FromStr;

#[derive(Debug)]
pub enum Const {
    Str(String),
    Int(i64),
    Double(f64),
    Bool(bool),
}

#[derive(Debug)]
pub struct Module<'a> {
    pub constants: Vec<Ref<'a>>,
    pub names: Vec<String>,
    pub code: Vec<u8>,
    pub main: AmaFunc<'a>,
    pub functions: Vec<AmaFunc<'a>>,
    pub src_map: Vec<usize>,
}

impl Const {
    pub fn get_str(&self) -> &String {
        match self {
            Self::Str(string) => &string,
            _ => panic!("Const is not a string"),
        }
    }
}

impl<'a> From<BSONType> for Const {
    fn from(bson_val: BSONType) -> Const {
        match bson_val {
            BSONType::String(string) => Const::from_str(&string).unwrap(),
            BSONType::Int(int) => Const::Int(int),
            BSONType::Double(double) => Const::Double(double),
            _ => panic!("Unexpected constant value"),
        }
    }
}

impl<'a> FromStr for Const {
    type Err = ();

    fn from_str(constant: &str) -> Result<Const, ()> {
        if constant == "verdadeiro" || constant == "falso" {
            let bool_val = if constant == "falso" { false } else { true };
            return Ok(Const::Bool(bool_val));
        }
        let maybe_int = constant.parse::<i64>();
        let maybe_float = constant.parse::<f64>();
        if maybe_int.is_ok() {
            return Ok(Const::Int(maybe_int.unwrap()));
        } else if maybe_float.is_ok() {
            return Ok(Const::Double(maybe_float.unwrap()));
        } else {
            let slice: &str = if &constant[..1] == "\"" || &constant[..1] == "\'" {
                &constant[1..constant.len() - 1]
            } else {
                constant
            };
            return Ok(Const::Str(String::from(slice)));
        }
    }
}

#[derive(Debug, PartialEq)]
enum BSONType {
    String(String),
    Int(i64),
    Double(f64),
    Array(Vec<BSONType>),
    Bytes(Vec<u8>),
    Doc(HashMap<String, BSONType>),
}

impl BSONType {
    fn take_vec(self) -> Vec<BSONType> {
        if let Self::Array(arr) = self {
            arr
        } else {
            panic!("Value is not a vec")
        }
    }
}

fn read_bson_key(raw_doc: &mut Cursor<&mut [u8]>) -> String {
    let mut key: String = String::new();
    loop {
        let mut buf: [u8; 1] = [0; 1];
        raw_doc.read_exact(&mut buf).unwrap();
        if buf[0] as char == '\0' {
            break;
        }
        key.push(buf[0] as char);
    }
    key
}

fn read_bytes<const N: usize>(cursor: &mut Cursor<&mut [u8]>) -> [u8; N] {
    let mut buf = [0; N];
    cursor.read_exact(&mut buf).unwrap();
    buf
}

fn unpack_bson_value(raw_doc: &mut Cursor<&mut [u8]>, value_type: u8) -> BSONType {
    match value_type {
        //Doc field types
        0x01 => {
            let num = read_bytes::<8>(raw_doc);
            BSONType::Double(f64::from_le_bytes(num))
        }
        0x02 => {
            let str_size = i32::from_le_bytes(read_bytes::<4>(raw_doc));
            let mut string = vec![0; str_size as usize];
            raw_doc.read_exact(&mut string).unwrap();
            read_bytes::<1>(raw_doc); // Read null byte at the end
            BSONType::String(String::from_utf8(string).unwrap())
        }
        0x03 => {
            read_bytes::<4>(raw_doc);
            let mut nested_doc = HashMap::new();
            let mut buf;
            loop {
                buf = read_bytes::<1>(raw_doc);
                if buf[0] as char == '\0' {
                    break;
                }
                let key = read_bson_key(raw_doc);
                let val = unpack_bson_value(raw_doc, buf[0]);
                nested_doc.insert(key, val);
            }

            BSONType::Doc(nested_doc)
        }
        0x04 => {
            read_bytes::<4>(raw_doc);
            let mut bson_array = Vec::new();
            let mut buf;
            loop {
                buf = read_bytes::<1>(raw_doc);
                if buf[0] as char == '\0' {
                    break;
                }
                read_bson_key(raw_doc);
                bson_array.push(unpack_bson_value(raw_doc, buf[0]));
            }
            BSONType::Array(bson_array)
        }
        0x05 => {
            let bin_len = i32::from_le_bytes(read_bytes::<4>(raw_doc));
            //Ignore subtype
            read_bytes::<1>(raw_doc);
            let mut bin_data = vec![0; bin_len as usize];
            raw_doc.read_exact(&mut bin_data).unwrap();
            BSONType::Bytes(bin_data)
        }
        0x12 => {
            let int64 = i64::from_le_bytes(read_bytes::<8>(raw_doc));
            //Ignore subtype
            BSONType::Int(int64)
        }
        _ => unimplemented!(
            "BSON type has not been implemented. Type byte: {}",
            value_type
        ),
    }
}

fn unpack_bson_doc(raw_doc: &mut [u8]) -> HashMap<String, BSONType> {
    let mut doc = HashMap::new();
    let mut cursor = Cursor::new(raw_doc);
    let mut buf: [u8; 1] = [0; 1];
    while let Ok(()) = cursor.read_exact(&mut buf) {
        if buf[0] as char == '\0' {
            break;
        }
        let key = read_bson_key(&mut cursor);
        let value = unpack_bson_value(&mut cursor, buf[0]);
        doc.insert(key, value);
    }
    doc
}

macro_rules! bson_take {
    ($inner: path, $packed: expr) => {
        if let $inner(inner) = $packed {
            inner
        } else {
            unreachable!("Invalid field unpacking")
        }
    };
}

fn doc_into_amafn<'a>(doc: BSONType) -> (String, usize, usize) {
    if let BSONType::Doc(mut func) = doc {
        let start_ip = bson_take!(BSONType::Int, func.remove("start_ip").unwrap()) as usize;

        (
            bson_take!(BSONType::String, func.remove("name").unwrap()),
            start_ip,
            bson_take!(BSONType::Int, func.remove("locals").unwrap()) as usize,
        )
    } else {
        unreachable!("functions should be an array of functions")
    }
}

pub fn consume_const<'a>(constant: Const) -> AmaValue<'a> {
    match constant {
        Const::Str(string) => AmaValue::Str(Cow::Owned(string)),
        Const::Int(int) => AmaValue::Int(int),
        Const::Double(real) => AmaValue::F64(real),
        Const::Bool(boolean) => AmaValue::Bool(boolean),
    }
}

pub fn load_bin<'bin>(amac_bin: &'bin mut [u8], alloc: &mut Alloc<'bin>) -> Module<'bin> {
    //Skip size bytes
    let mut prog_data = unpack_bson_doc(amac_bin);
    let raw_consts = prog_data.remove("constants").unwrap().take_vec();
    let mut constants = Vec::with_capacity(raw_consts.len());
    raw_consts
        .into_iter()
        .for_each(|constant| constants.push(alloc.alloc_ref(consume_const(Const::from(constant)))));
    let names: Vec<String> = prog_data
        .remove("names")
        .unwrap()
        .take_vec()
        .into_iter()
        .map(|name| bson_take!(BSONType::String, name))
        .collect();

    let ops = bson_take!(BSONType::Bytes, prog_data.remove("ops").unwrap());
    let entry_locals = bson_take!(BSONType::Int, prog_data.remove("entry_locals").unwrap());
    let src_map: Vec<usize> = if let BSONType::Array(offsets) = prog_data.remove("src_map").unwrap()
    {
        offsets
            .iter()
            .map(|num| *bson_take!(BSONType::Int, num) as usize)
            .collect()
    } else {
        unreachable!("src_map should be an array of ints")
    };

    let functions: Vec<AmaFunc> =
        if let BSONType::Array(funcs) = prog_data.remove("functions").unwrap() {
            funcs
                .into_iter()
                .map(|func| {
                    let (name, start_ip, locals) = doc_into_amafn(func);
                    AmaFunc {
                        //TODO: Check if i should be leaking memory
                        name: Box::leak(name.into_boxed_str()),
                        bp: -1,
                        start_ip: start_ip,
                        last_i: start_ip,
                        ip: start_ip,
                        locals: locals,
                    }
                })
                .collect()
        } else {
            unreachable!("functions should be an array of functions")
        };

    Module {
        constants,
        names,
        code: ops,
        src_map,
        main: AmaFunc {
            name: "_inicio_",
            bp: -1,
            start_ip: 0,
            last_i: 0,
            ip: 0,
            locals: entry_locals as usize,
        },
        functions,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    impl BSONType {
        fn is_doc(&self) -> bool {
            if let Self::Doc(_) = self {
                true
            } else {
                false
            }
        }

        fn is_vec(&self) -> bool {
            if let Self::Array(_) = self {
                true
            } else {
                false
            }
        }
        fn get_doc(&self) -> &HashMap<String, BSONType> {
            if let Self::Doc(doc) = self {
                doc
            } else {
                panic!("Value is not a doc")
            }
        }

        fn get_vec(&self) -> &Vec<BSONType> {
            if let Self::Array(arr) = self {
                arr
            } else {
                panic!("Value is not a vec")
            }
        }

        fn get_f64(&self) -> f64 {
            if let Self::Double(float) = self {
                *float
            } else {
                panic!("Value is not a float")
            }
        }

        fn get_i64(&self) -> i64 {
            if let Self::Int(int) = self {
                *int
            } else {
                panic!("Value is not a float")
            }
        }

        fn get_str(&self) -> &str {
            if let Self::String(string) = self {
                &string
            } else {
                panic!("Value is not a string")
            }
        }

        fn get_bytes(&self) -> &Vec<u8> {
            if let Self::Bytes(bytes) = self {
                bytes
            } else {
                panic!("Value is not a string")
            }
        }
    }

    #[test]
    fn test_string_field() {
        // { "name": "João Boris" }
        let mut bytes = vec![
            22, 0, 0, 0, 2, 110, 97, 109, 101, 0, 11, 0, 0, 0, 74, 111, 195, 163, 111, 32, 66, 111,
            114, 105, 115, 0, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("name"), true);
        assert_eq!(doc.get("name").unwrap().get_str(), "João Boris");
    }

    #[test]
    fn test_f64_field() {
        // { "credit": 100.50 }
        let mut bytes = vec![
            16, 0, 0, 0, 1, 99, 114, 101, 100, 105, 116, 0, 0, 0, 0, 0, 0, 32, 89, 64, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("credit"), true);
        assert_eq!(doc.get("credit").unwrap().get_f64(), 100.50);
    }

    #[test]
    fn test_i64_field() {
        // { "age": 100 }
        let mut bytes = vec![
            13, 0, 0, 0, 18, 97, 103, 101, 0, 100, 0, 0, 0, 0, 0, 0, 0, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("age"), true);
        assert_eq!(doc.get("age").unwrap().get_i64(), 100);
    }

    #[test]
    fn test_bytes_field() {
        // { "bytes": [0, 1, 1, 2, 3 , 255] }
        let mut bytes = vec![
            18, 0, 0, 0, 5, 98, 121, 116, 101, 115, 0, 6, 0, 0, 0, 128, 0, 1, 1, 2, 3, 255, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("bytes"), true);
        assert_eq!(
            doc.get("bytes").unwrap().get_bytes().clone(),
            vec![0, 1, 1, 2, 3, 255]
        );
    }

    #[test]
    fn test_array_field() {
        // { "names": ["João Boris", "Some other dude"] }
        let mut bytes = vec![
            54, 0, 0, 0, 4, 110, 97, 109, 101, 115, 0, 42, 0, 0, 0, 2, 48, 0, 11, 0, 0, 0, 74, 111,
            195, 163, 111, 32, 66, 111, 114, 105, 115, 0, 2, 49, 0, 15, 0, 0, 0, 83, 111, 109, 101,
            32, 111, 116, 104, 101, 114, 32, 100, 117, 100, 101, 0, 0, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("names"), true);
        assert_eq!(doc.get("names").unwrap().is_vec(), true);
        let arr = doc.get("names").unwrap().get_vec();
        let mut arr_iter = arr.iter();
        assert_eq!(arr_iter.len(), 2);
        assert_eq!(arr_iter.next().unwrap().get_str(), "João Boris");
        assert_eq!(arr_iter.next().unwrap().get_str(), "Some other dude");
    }

    #[test]
    fn test_doc_field() {
        // { "user": {"name": "João Boris", "age": 28, "balance": 1000.52}  }
        let mut bytes = vec![
            63, 0, 0, 0, 3, 117, 115, 101, 114, 0, 52, 0, 0, 0, 2, 110, 97, 109, 101, 0, 11, 0, 0,
            0, 74, 111, 195, 163, 111, 32, 66, 111, 114, 105, 115, 0, 18, 97, 103, 101, 0, 28, 0,
            0, 0, 0, 0, 0, 0, 1, 98, 97, 108, 97, 110, 99, 101, 0, 92, 143, 194, 245, 40, 68, 143,
            64, 0, 0,
        ];
        bytes.drain(0..4);

        let doc = unpack_bson_doc(&mut bytes);
        assert_eq!(doc.is_empty(), false);
        assert_eq!(doc.contains_key("user"), true);
        assert_eq!(doc.get("user").unwrap().is_doc(), true);

        let nested_doc = doc.get("user").unwrap().get_doc();
        assert_eq!(nested_doc.get("name").unwrap().get_str(), "João Boris");
        assert_eq!(nested_doc.get("age").unwrap().get_i64(), 28);
        assert_eq!(nested_doc.get("balance").unwrap().get_f64(), 1000.52);
    }
}
