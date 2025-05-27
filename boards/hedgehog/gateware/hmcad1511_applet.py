from amaranth import *
from naps import *
from naps.vendor.lattice_ecp5 import Pll

from hmcad1511.hmcad1511 import HMCAD1511
from hedgehog_platform import HedgehogPlatform

class Top(Elaboratable):
    runs_on=[HedgehogPlatform]

    def elaborate(self, platform: HedgehogPlatform):
        platform.connect_hmcad1511_pmod()

        m = Module()

        pll = m.submodules.pll = Pll(100e6, 4, 1, input_domain="sync", reset_less_input=True)
        pll.output_domain("clk25", 16)

        self.hmcad = m.submodules.hmcad = DomainRenamer("clk25")(HMCAD1511())

        return m


if __name__ == "__main__":
    cli(Top)
