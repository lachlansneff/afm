
use bitflags::bitflags;

bitflags! {
    #[repr(transparent)]
    struct Flags: u32 {
        const ENABLE = 1 << 0;
    }
}

pub struct Led {
    mapping: *mut u32,
}

unsafe impl Sync for Led {}

impl Led {
    pub const fn new() -> Self {
        Self {
            mapping: 0xcafebab0 as *mut u32,
        }
    }

    pub fn enable(&self, en: bool) {
        let flags = if en { Flags::ENABLE } else { Flags::empty() };
        unsafe {
            self.mapping.write_volatile(flags.bits());
        }
    }
}