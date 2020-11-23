# If the design does not create a "sync" clock domain, it is created by the nMigen build system
# using the platform default clock (and default reset, if any).

from nmigen import Elaboratable, Module, Signal
from nmigen.build.dsl import Resource, Pins
from nmigen_boards.tinyfpga_bx import TinyFPGABXPlatform
from ice40_pll import ICE40_PLL


class Blinky(Elaboratable):
    def elaborate(self, platform):
        timer = Signal(23)

        m = Module()

        m.d.sync += timer.eq(timer + 1)

        if platform is not None:
            led = platform.request("led", 0)
            m.d.comb += led.o.eq(timer[-1])

        return m


if __name__ == "__main__":
    platform = TinyFPGABXPlatform()
    products = platform.build(Blinky(), do_program=True)
