use crate::ama_value::AmaValue;
use std::ptr;

#[derive(Debug, Copy)]
pub struct Ref<'a> {
    inner: *mut AmaValue<'a>,
    next: *const Ref<'a>,
}

impl Clone for Ref<'_> {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner,
            next: self.next,
        }
    }
}

impl<'a> Ref<'a> {
    pub fn inner(&self) -> &AmaValue<'a> {
        /*SAFETY: Inner should be a valid and non-null pointer as it should only be obtained
         * from the alloc_ref
         */
        unsafe { &*(self.inner) }
    }

    pub fn inner_mut(&self) -> &mut AmaValue<'a> {
        /*SAFETY: Inner should be a valid and non-null pointer as it should only be obtained
         * from the alloc_ref
         */
        unsafe { &mut *(self.inner) }
    }
}

#[derive(Debug)]
pub struct Alloc<'a> {
    objects: Option<Ref<'a>>,
}

impl<'a> Alloc<'a> {
    pub fn new() -> Alloc<'a> {
        Alloc { objects: None }
    }

    pub fn alloc_ref(&mut self, value: AmaValue<'a>) -> Ref<'a> {
        let boxed = match value {
            AmaValue::Int(_)
            | AmaValue::F64(_)
            | AmaValue::Bool(_)
            | AmaValue::Func(_)
            | AmaValue::NativeFn(_)
            | AmaValue::None
            | AmaValue::Type(_)
            | AmaValue::Str(_) => {
                //Cheap and sized type, use stack
                Box::new(value)
            }
            _ => unimplemented!(),
        };
        let mut new_ref = Ref {
            inner: Box::into_raw(boxed),
            next: ptr::null(),
        };
        if let Some(ref object) = self.objects {
            new_ref.next = object;
            self.objects = Some(new_ref);
        } else {
            self.objects = Some(new_ref);
        }
        new_ref
        //unimplemented!()
    }
}
