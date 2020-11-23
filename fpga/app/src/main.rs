#![no_std]
#![no_main]

extern crate panic_halt;

mod nco;
mod led;

use nco::Nco;
use led::Led;

use picorv32_rt::entry;

const LED: Led = Led::new();
static NCO: Nco = Nco::new();

#[entry]
fn main() -> ! {
    NCO.set_frequency(32_768.5);
    NCO.enable(true);

    LED.enable(true);

    loop {}
}
