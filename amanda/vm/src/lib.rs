use alloc::Alloc;
use std::slice;
use vm::AmaVM;

mod alloc;
mod ama_value;
mod binload;
mod builtins;
mod errors;
mod opcode;
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

    let mut alloc = Alloc::new();
    let mut ama_module = binload::load_bin(module, &mut alloc);
    let mut vm = AmaVM::new(&mut ama_module, alloc);
    if let Err(err) = vm.run() {
        eprint!("{}", err);
        OK
    } else {
        ERR
    }
}
