from nmigen import Elaboratable, Module, Signal

class SigmaDeltaDAC(Elaboratable):
    def __init__(self, width: int):
        self.width = width
        self.out = Signal()
        self.waveform = Signal(width)

    def elaborate(self, platform):
        m = Module()

        acc = Signal(self.width+1)

        m.d.sync += acc.eq(acc[:self.width] + self.waveform)
        m.d.comb += self.out.eq(acc[-1])

        return m
