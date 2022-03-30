use std::{env, fs, path::Path};
use vm::binload;
use vm::vm::AmaVM;

fn main() -> Result<(), ()> {
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        eprintln!("Please specify a compiled bytecode file to run");
        return Err(());
    }

    let file = Path::new(&args[1]);
    let mut program_bin = fs::read(file).unwrap();
    let mut program = binload::load_bin(&mut program_bin);
    let mut vm = AmaVM::new(&mut program);
    if let Err(err) = vm.run() {
        eprint!("{}", err);
        std::process::exit(1);
    } else {
        Ok(())
    }
}
