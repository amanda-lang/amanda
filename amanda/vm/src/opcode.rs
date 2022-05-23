use std::convert::From;

#[derive(Debug, Clone, Copy)]
pub enum OpCode {
    Mostra,
    LoadConst,
    OpAdd,
    OpMinus,
    OpMul,
    OpDiv,
    OpFloorDiv,
    OpModulo,
    OpInvert,
    OpAnd,
    OpOr,
    OpNot,
    OpEq,
    OpNotEq,
    OpGreater,
    OpGreaterEq,
    OpLess,
    OpLessEq,
    OpIndexGet,
    OpIndexSet,
    GetGlobal,
    SetGlobal,
    Jump,
    JumpIfFalse,
    GetLocal,
    SetLocal,
    CallFunction,
    Return,
    Cast,
    BuildStr,
    BuildVec,
    Halt = 255,
}

impl From<&u8> for OpCode {
    fn from(number: &u8) -> Self {
        let ops = [
            OpCode::Mostra,
            OpCode::LoadConst,
            OpCode::OpAdd,
            OpCode::OpMinus,
            OpCode::OpMul,
            OpCode::OpDiv,
            OpCode::OpFloorDiv,
            OpCode::OpModulo,
            OpCode::OpInvert,
            OpCode::OpAnd,
            OpCode::OpOr,
            OpCode::OpNot,
            OpCode::OpEq,
            OpCode::OpNotEq,
            OpCode::OpGreater,
            OpCode::OpGreaterEq,
            OpCode::OpLess,
            OpCode::OpLessEq,
            OpCode::OpIndexGet,
            OpCode::OpIndexSet,
            OpCode::GetGlobal,
            OpCode::SetGlobal,
            OpCode::Jump,
            OpCode::JumpIfFalse,
            OpCode::GetLocal,
            OpCode::SetLocal,
            OpCode::CallFunction,
            OpCode::Return,
            OpCode::Cast,
            OpCode::BuildStr,
            OpCode::BuildVec,
        ];
        if *number == 0xff {
            OpCode::Halt
        } else {
            ops[*number as usize]
        }
    }
}
