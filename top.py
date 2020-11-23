from nmigen import Module, Elaboratable, DomainRenamer, Signal, Record
from nmigen.build.dsl import Resource, Pins

import typing

# from cordic import CORDIC
from blinky import Blinky
from ice40_pll import ICE40_PLL
from nco import NCO
from sigma_delta_dac import SigmaDeltaDAC
from picorv32 import PicoRV32, Mapping

class Top(Elaboratable):
    def __init__(self):
        # self.pll = ICE40_PLL(
        #     50, # Mhz
        #     "pll",
        # )

        # self.cordic = DomainRenamer("pll")(CORDIC(width=12))
        # self.nco = DomainRenamer("pll")(NCO(width=12, samples=1024))
        # self.dac = DomainRenamer("pll")(SigmaDeltaDAC(width=12))
        self.nco = NCO(width=12, samples=1024)
        self.dac = SigmaDeltaDAC(width=12)
        # self.blinky = Blinky()

        self.nco_ctrl = Record([
            ("enable", 1),
        ])

        self.led = Signal()

        self.picorv32 = PicoRV32([
            Mapping(
                addr=0xcafebab0,
                signal=self.led,
                write=True,
                read=False,
            ),
            Mapping(
                addr=0xf000_0000,
                signal=self.nco_ctrl,
                read=True,
                write=True,
            ),
            Mapping(
                addr=0xf000_0004, # offset by 1 word
                signal=self.nco.phase_step,
                read=True,
                write=True,
            ),
        ])

    def elaborate(self, platform):
        m = Module()

        m.submodules += [self.nco, self.dac, self.picorv32]

        m.d.comb += [
            # self.dds.phase_step.eq(DDS.calculate_phase_step(clk_frequency=50e6, frequency=32_768)),
            self.dac.waveform.eq(self.nco.sin),
            self.nco.enable.eq(self.nco_ctrl.enable),
        ]

        if platform is not None:
            platform.add_resources([Resource("dac", 0, Pins("13", dir="o", conn=("gpio", 0)))])
            dac_pin = platform.request("dac")
            m.d.comb += dac_pin.o.eq(self.dac.out)

            led_pin = platform.request("led")
            m.d.comb += led_pin.o.eq(self.led)

        return m

if __name__ == "__main__":
    from nmigen_boards.tinyfpga_bx import TinyFPGABXPlatform
    import sys

    if len(sys.argv) != 2:
        print("top.py <program|simulate>")
    elif sys.argv[1] == "build":
        platform = TinyFPGABXPlatform()
        products = platform.build(Top(), do_program=False)
    elif sys.argv[1] == "program":
        platform = TinyFPGABXPlatform()
        products = platform.build(Top(), do_program=True)
    elif sys.argv[1] == "generate":
        from nmigen.back import verilog
        top = Top()
        print(verilog.convert(top, name="top", ports=(top.led,)))
    # elif sys.argv[1] == "simulate":
    #     from nmigen.sim import Simulator, Tick

    #     dut = Top()
    #     sim = Simulator(dut, engine="cxxsim")
    #     sim.add_clock(1 / 16e6, domain="sync")
    #     sim.add_clock(1 / 50e6, domain="pll")

    #     def proc():
    #         for i in range(2000):
    #             yield Tick()

    #     sim.add_process(proc)
    #     with sim.write_vcd("top.vcd"):
    #         sim.run()
