from collections import namedtuple
from typing import Tuple
import warnings

from nmigen import Elaboratable, Module, Instance, Signal, ClockDomain, ClockSignal, Const
from nmigen.hdl.ast import ResetSignal
from nmigen.lib.cdc import ResetSynchronizer
from nmigen.cli import main

# original code https://github.com/kbob/nmigen-examples/blob/master/lib/pll.py

class ICE40_PLL(Elaboratable):

    """
    Instantiate the iCE40's phase-locked loop (PLL).
    """

    def __init__(self, freq_out_mhz: int, domain_name: str):
        self.freq_out = freq_out_mhz

        self.domain_name = domain_name
        # self.pll_domain = ClockDomain(domain_name)

    def _calc_freq_coefficients(self, f_in, f_req):
        # cribbed from Icestorm's icepll.
        # f_in, f_req = self.freq_in, self.freq_out
        assert 10 <= f_in <= 160
        assert 16 <= f_req <= 275
        coefficients = namedtuple('coefficients', 'divr divf divq')
        divf_range = 128        # see comments in icepll.cc
        best_fout = float('inf')
        fouts = []
        best: coefficients = coefficients(0, 0, 0)
        for divr in range(16):
            pfd = f_in / (divr + 1)
            if 10 <= pfd <= 133:
                for divf in range(divf_range):
                    vco = pfd * (divf + 1)
                    if 533 <= vco <= 1066:
                        for divq in range(0, 8):
                            fout = vco * 2**-divq
                            fouts.append(fout)
                            if abs(fout - f_req) < abs(best_fout - f_req):
                                best_fout = fout
                                best = coefficients(divr, divf, divq)
        if best_fout != f_req:
            warnings.warn(
                f'PLL: requested {f_req} MHz, got {best_fout} MHz)',
                stacklevel=3)
        #print(sorted(fouts, key=lambda v: -abs(v-f_req)))
        return best

    def elaborate(self, platform):
        m = Module()

        if platform is not None:
            # platform.default_clk_frequency is in Hz
            coeff = self._calc_freq_coefficients(platform.default_clk_frequency / 1_000_000, self.freq_out)
            # clk_pin = platform.request(platform.default_clk)

            lock = Signal()

            pll = Instance("SB_PLL40_CORE",
                p_FEEDBACK_PATH='SIMPLE',
                p_DIVR=coeff.divr,
                p_DIVF=coeff.divf,
                p_DIVQ=coeff.divq,
                p_FILTER_RANGE=0b001,
                p_DELAY_ADJUSTMENT_MODE_FEEDBACK='FIXED',
                p_FDA_FEEDBACK=0b0000,
                p_DELAY_ADJUSTMENT_MODE_RELATIVE='FIXED',
                p_FDA_RELATIVE=0b0000,
                p_SHIFTREG_DIV_MODE=0b00,
                p_PLLOUT_SELECT='GENCLK',
                p_ENABLE_ICEGATE=0b0,

                i_REFERENCECLK=ClockSignal(),
                o_PLLOUTCORE=ClockSignal(self.domain_name),
                i_RESETB=ResetSignal(),
                i_BYPASS=Const(0),
                o_LOCK=lock,
            )
            rs = ResetSynchronizer(~lock, domain=self.domain_name)

            m.submodules += [pll, rs]
        
        m.domains += ClockDomain(self.domain_name)

        return m
