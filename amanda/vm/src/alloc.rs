use crate::ama_value::AmaValue;

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

    pub fn alloc_ref(&self, value: AmaValue<'a>) -> Ref<'a> {
        unimplemented!()
    }
}
