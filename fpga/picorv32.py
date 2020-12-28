import sys, subprocess, os
from typing import Callable, Union
from nmigen import Elaboratable, Module, Signal, Memory, ClockSignal, Instance, ResetSignal
import numpy as np

class Mapping:
    def __init__(self, addr: int, signal: Signal, read: bool, write: Union[None, bool, Callable[[Module, Signal], None]]):
        self.addr = addr
        self.signal = signal
        self.read = read
        self.writing_enabled = (isinstance(write, bool) and write) or callable(write)
        self.write = staticmethod(write) if callable(write) else None

class PicoRV32(Elaboratable):
    def __init__(self, memory_mappings: list[Mapping]):
        self.memory_mappings = memory_mappings

    def elaborate(self, platform):
        if platform is not None:
            platform.add_file("picorv32.v", open("picorv32.v", "r"))

        if not os.path.exists("build"):
            os.makedirs("build")

        subprocess.run(
            ["cargo", "objcopy", "--release", "--", "-O", "binary", "../build/app.bin"],
            cwd="app",
        ).check_returncode()

        with open("build/app.bin", "rb") as f:
            b = bytearray(f.read())
            b.extend([0] * (4 - (len(b) % 4)))
            app = np.frombuffer(b, dtype='<u4').tolist()

        # MEM_SIZE = 256 # words
        RAM_SIZE = 256 # words
        init = ([0] * RAM_SIZE) + app
        MEM_SIZE = len(init)

        mem = Memory(
            width=32,
            depth=MEM_SIZE,
            init=init,
        )

        resetn = Signal()
        mem_valid = Signal()
        mem_ready = Signal()
        mem_addr = Signal(32)
        mem_wdata = Signal(32)
        mem_wstrb = Signal(4)
        mem_rdata = Signal(32)

        m = Module()

        m.d.comb += resetn.eq(~ResetSignal())

        m.submodules.picorv32 = Instance("picorv32",
            p_ENABLE_COUNTERS=0,
            p_LATCHED_MEM_RDATA=1,
            p_TWO_STAGE_SHIFT=0,
            p_TWO_CYCLE_ALU=1,
            p_CATCH_MISALIGN=0,
            p_CATCH_ILLINSN=0,
            p_COMPRESSED_ISA=1,
            p_ENABLE_MUL=1,
            p_PROGADDR_RESET=1024,
            p_PROGADDR_IRQ=1024 + 0x10,

            i_clk=ClockSignal(),
            i_resetn=resetn,
            o_mem_valid=mem_valid,
            i_mem_ready=mem_ready,
            o_mem_addr=mem_addr,
            o_mem_wdata=mem_wdata,
            o_mem_wstrb=mem_wstrb,
            i_mem_rdata=mem_rdata,
        )
        m.submodules.read_port = read_port = mem.read_port(transparent=False)
        m.submodules.write_port = write_port = mem.write_port(granularity=8)

        m.d.sync += mem_ready.eq(0)

        m.d.comb += [
            read_port.addr.eq(mem_addr >> 2),
            mem_rdata.eq(read_port.data),
            read_port.en.eq((~mem_wstrb).bool()),

            write_port.addr.eq(mem_addr >> 2),
            write_port.data.eq(mem_wdata),
            write_port.en.eq(mem_wstrb),
        ]

        with m.If(resetn & mem_valid & ~mem_ready):
            with m.If((mem_addr >> 2) < MEM_SIZE):
                m.d.sync += mem_ready.eq(1)

            for mapping in self.memory_mappings:
                if mapping.writing_enabled:
                    with m.If(mem_wstrb.bool() & (mem_addr == mapping.addr)):
                        if mapping.write is not None:
                            mapping.write(m, mem_wdata)
                        else:
                            m.d.sync += [
                                mapping.signal.eq(mem_wdata),
                                mem_ready.eq(1),
                            ]
                if mapping.read:
                    with m.If((~mem_wstrb).bool() & (mem_addr == mapping.addr)):
                        m.d.comb += mem_rdata.eq(mapping.signal)
                        m.d.sync += mem_ready.eq(1)
                if not mapping.read and not mapping.write:
                    print("mapping doesn't specify read or write", file=sys.stderr)

        return m

class PicoRV32Test(Elaboratable):
    def __init__(self):
        self.led = Signal()
        self.picorv32 = PicoRV32([
            Mapping(
                addr=0xcafebab0,
                signal=self.led,
                write=True,
                read=False,
            )
        ])

    def elaborate(self, platform):
        m = Module()
        m.submodules += self.picorv32

        # led_pin = platform.request("led", dir="-")
        # m.d.comb += led_pin.io.eq(self.led)

        return m
            
if __name__ == "__main__":
    from nmigen.cli import main
    from nmigen.back import verilog
    top = PicoRV32Test()
    verilog.convert(top, name="top", ports=(top.led,))
    # main(top, ports=(top.led,))
    # from nmigen_boards.tinyfpga_bx import TinyFPGABXPlatform

    # platform = TinyFPGABXPlatform()
    # products = platform.build(PicoRV32Test(), do_program=False)