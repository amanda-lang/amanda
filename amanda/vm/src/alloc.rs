use crate::ama_value::AmaValue;
use std::ptr;

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
        let ama_ref = Ref(Box::into_raw(Box::new(InnerRef {
            inner: Box::into_raw(boxed),
            next: ptr::null(),
        })));
        if let Some(ref object) = self.objects {
            //SAFETY: Pointer obtained from box
            unsafe { &mut *ama_ref.0 }.next = object.0;
            self.objects = Some(ama_ref);
        } else {
            self.objects = Some(ama_ref);
        }
        ama_ref
        //unimplemented!()
    }
}
