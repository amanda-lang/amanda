use crate::ama_value::{AmaValue, RcCell};
use crate::opcode::OpCode;
use std::cell::RefCell;
use std::hash::{Hash, Hasher};
use std::ptr;
use std::rc::Rc;

#[derive(Debug)]
struct InnerRef<'a> {
    inner: *mut AmaValue<'a>,
    next: *const InnerRef<'a>,
}

#[derive(Debug, Copy, Clone)]
pub struct Ref<'a>(*mut InnerRef<'a>);

impl<'a> Ref<'a> {
    pub fn inner(&self) -> &AmaValue<'a> {
        /*SAFETY: The InnerRef should be obtained from the 'alloc_ref' function
         * of the Alloc struct.
         */
        unsafe { &(*(*self.0).inner) }
    }

    pub fn inner_mut(&self) -> &mut AmaValue<'a> {
        /*SAFETY: The InnerRef should be obtained from the 'alloc_ref' function
         * of the Alloc struct.
         */
        unsafe { &mut (*(*self.0).inner) }
    }
}

macro_rules! raw_from_box {
    ($target: expr) => {
        Box::into_raw(Box::new($target))
    };
}

#[derive(Debug)]
pub struct Alloc<'a> {
    objects: Option<Ref<'a>>,
    null_ref: Option<AmaValue<'a>>,
}

impl<'a> Alloc<'a> {
    pub fn new() -> Alloc<'a> {
        let mut alloc = Alloc {
            objects: None,
            null_ref: None,
        };
        //Create a single reference to None to be used
        //by the vm
        let null_ref = AmaValue::None;
        alloc.null_ref = Some(null_ref);
        alloc
    }

    pub fn alloc_ref<T>(&mut self, value: T) -> RcCell<T> {
        Rc::new(RefCell::new(value))
        //unimplemented!()
    }

    pub fn null_ref(&self) -> AmaValue<'a> {
        self.null_ref.unwrap()
    }
}
