use std::{env, fs, path::Path};
use vm::binload;
use vm::vm::AmaVM;

fn main() {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Please specify a compiled bytecode file to run");
        return;
    }

    let file = Path::new(&args[1]);
    let mut program_bin = fs::read(file).unwrap();
    let mut program = binload::load_bin(&mut program_bin);
    let mut vm = AmaVM::new(&mut program);
    vm.run();
}
