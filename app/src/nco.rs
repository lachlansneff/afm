use bitflags::bitflags;

const NCO_CLOCK_FREQUENCY: f64 = 16_000_000.; // 16 Mhz

bitflags! {
    #[repr(transparent)]
    struct Ctrl: u32 {
        const ENABLE = 1 << 0;
    }
}

#[repr(C)]
struct Mapping {
    ctrl: u32,
    phase_step: u32,
}

pub struct Nco {
    mapping: *mut Mapping,
}

unsafe impl Sync for Nco {}

impl Nco {
    pub const fn new() -> Self {
        Self {
            mapping: 0xf000_0000 as *mut Mapping,
        }
    }

    pub fn enable(&self, en: bool) {
        unsafe {
            let mut flags = Ctrl::from_bits_unchecked((&(*self.mapping).ctrl as *const u32).read_volatile());
            flags.set(Ctrl::ENABLE, en);
            (&mut (*self.mapping).ctrl as *mut u32).write_volatile(flags.bits());
        }
    }

    pub fn set_frequency(&self, freq: f32) {
        let freq = freq as f64;
        let phase_step = libm::round(((u32::max_value() as f64) + 1.) * freq / NCO_CLOCK_FREQUENCY) as u32;
        unsafe {
            (&mut (*self.mapping).phase_step as *mut u32).write_volatile(phase_step);
        }
    }
}
