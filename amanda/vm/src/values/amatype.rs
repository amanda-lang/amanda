use std::fmt::Debug;

#[derive(Debug, Copy, Clone)]
pub enum Type {
    Int,
    Real,
    Texto,
    Bool,
    Vector,
}

impl Type {
    pub fn name(&self) -> &str {
        match self {
            Type::Int => "int",
            Type::Real => "real",
            Type::Texto => "texto",
            Type::Bool => "bool",
            Type::Vector => "Vector",
        }
    }
}
