use std::{env, fs, path::Path};

mod alloc;
mod ama_value;
mod binload;
mod builtins;
mod errors;
mod opcode;
mod vm;

use alloc::Alloc;
use vm::AmaVM;

fn main() -> Result<(), ()> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Please specify a compiled bytecode file to run");
        return Err(());
    }

    let file = Path::new(&args[1]);
    let mut program_bin = fs::read(file).unwrap();
    let mut alloc = Alloc::new();
    let mut program = binload::load_bin(&mut program_bin, &mut alloc);
    let mut vm = AmaVM::new(&mut program, alloc);
    if let Err(err) = vm.run() {
        eprint!("{}", err);
        std::process::exit(1);
    } else {
        Ok(())
    }
}
