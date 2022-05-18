use crate::ama_value::AmaValue;
use std::collections::LinkedList;

type LiveObj<'a> = AmaValue<'a>;

pub struct Alloc<'a> {
    active: LinkedList<LiveObj<'a>>,
}

impl<'a> Alloc<'a> {
    pub fn new() -> Alloc<'a> {
        Alloc {
            active: LinkedList::new(),
        }
    }

    pub fn alloc_value(&mut self, value: AmaValue<'a>) -> &AmaValue<'a> {
        self.active.push_back(value);
        self.active.back().unwrap()
    }
}
