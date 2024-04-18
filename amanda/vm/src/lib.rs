use alloc::Alloc;
use std::slice;
use vm::AmaVM;

mod alloc;
mod ama_value;
mod binload;
mod errors;
mod modules;
mod opcode;
mod values;
mod vm;

const OK: u8 = 0;
const ERR: u8 = 1;

#[no_mangle]
pub extern "C" fn run_module(bin_module: *mut u8, size: u32) -> u8 {
    let module = unsafe {
        assert!(!bin_module.is_null());
        //Skip size bytes
        &mut slice::from_raw_parts_mut(bin_module, size as usize)[4..]
    };

    let alloc = Alloc::new();
    let (mut ama_module, imports) = binload::load_bin(module);

    let mut vm = AmaVM::new(&imports, alloc);
    if let Err(err) = vm.run(&mut ama_module, true) {
        eprint!("{}", err);
        ERR
    } else {
        OK
    }
}
