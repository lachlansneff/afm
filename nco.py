from nmigen import Elaboratable, Module, Signal, Instance, Memory, Mux, Cat, signed, Const
import math

def trunc_add(signal, n):
    return (signal + n)[:len(signal)]

class SinCosLookup(Elaboratable):
    def __init__(self, out_width: int, samples: int):
        M = 1 << (out_width - 1)

        amplitudes = [int(M * math.sin((math.pi / 2) * (i/samples))) for i in range(samples)]

        self.quarter_sin_mem = Memory(
            width=(out_width - 1),
            depth=samples,
            init=amplitudes,
        )

        self.addr = Signal(range(samples * 4))
        self.sin = Signal(out_width)
        self.cos = Signal(out_width)

    def elaborate(self, platform):
        m = Module()
        m.submodules.sin_rdport = sin_rdport = self.quarter_sin_mem.read_port()
        m.submodules.cos_rdport = cos_rdport = self.quarter_sin_mem.read_port()

        def sinewave(rdport, addr):
            m.d.comb += rdport.addr.eq(Mux(addr[-2], ~addr[:-2], addr[:-2]))
            return Mux(addr[-1],
                Cat(~rdport.data, 0),
                Cat(rdport.data, 1),
            )
        m.d.comb += [
            self.sin.eq(sinewave(sin_rdport, self.addr)),
            self.cos.eq(sinewave(cos_rdport, trunc_add(self.addr, self.quarter_sin_mem.depth)))
        ]

        return m

class NCO(Elaboratable):
    def __init__(self, width: int, samples: int):
        self.width = width
        self.samples = samples

        self.enable = Signal()
        self.sin = Signal(width)
        self.cos = Signal(width)
        self.phase_step = Signal(32)
        # self.phase_step = int(round((2 ** 32) * frequency / clk_frequency))

    def elaborate(self, platform):
        m = Module()
        m.submodules.sincos_lookup = sincos_lookup = SinCosLookup(out_width=self.width, samples=self.samples)

        phase_acc = Signal(32)

        m.d.comb += [
            sincos_lookup.addr.eq(phase_acc[-sincos_lookup.addr.width:]), # last `sincos_lookup.addr.width` bits of the phase accumulator
            self.sin.eq(sincos_lookup.sin),
            self.cos.eq(sincos_lookup.cos),
        ]

        # with m.If(self.enable):
        m.d.sync += phase_acc.eq(phase_acc + self.phase_step)

        return m

    @staticmethod
    def calculate_phase_step(clk_frequency: float, frequency: float):
        return int(round((2 ** 32) * frequency / clk_frequency))


if __name__ == "__main__":
    # from nmigen_boards.tinyfpga_bx import TinyFPGABXPlatform
    # platform = TinyFPGABXPlatform()
    # products = platform.build(Top(), do_program=True)
    
    from nmigen.sim import Simulator, Tick

    dut = NCO(width=8, samples=1024)
    sim = Simulator(dut)
    sim.add_clock(1 / 1e6)

    def proc():
        yield dut.phase_step.eq(NCO.calculate_phase_step(clk_frequency=1e6, frequency=440))
        for i in range(3000):
            yield Tick()

    sim.add_process(proc)
    with sim.write_vcd("dds.vcd"):
        sim.run()
