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

macro_rules! raw_from_box {
    ($target: expr) => {
        Box::into_raw(Box::new($target))
    };
}

#[derive(Debug)]
pub struct Alloc<'a> {
    objects: Option<Ref<'a>>,
    null_ref: Option<Ref<'a>>,
}

impl<'a> Alloc<'a> {
    pub fn new() -> Alloc<'a> {
        let mut alloc = Alloc {
            objects: None,
            null_ref: None,
        };
        //Create a single reference to None to be used
        //by the vm
        let null_ref = alloc.alloc_ref(AmaValue::None);
        alloc.null_ref = Some(null_ref);
        alloc
    }

    pub fn alloc_ref(&mut self, value: AmaValue<'a>) -> Ref<'a> {
        if let AmaValue::None = value {
            debug_assert!(
                self.null_ref.is_none(),
                "Do not allocate a new None reference, use the one returned from Alloc::null_ref()"
            );
        }
        let value_alloc = raw_from_box!(value);
        let ama_ref = Ref(raw_from_box!(InnerRef {
            inner: value_alloc,
            next: ptr::null(),
        }));
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

    pub fn null_ref(&self) -> Ref<'a> {
        self.null_ref.unwrap()
    }
}
