from amaranth import *
from naps import *
from naps.vendor.lattice_ecp5 import Pll
from spi import SpiController
from timing_generator import SlothTimingGenerator
from hedgehog_platform import HedgehogPlatform

class Top(Elaboratable):
    def elaborate(self, platform: HedgehogPlatform):
        m = Module()

        m.domains += ClockDomain("clk100")
        m.d.comb += ResetSignal("clk100").eq(platform.request("rst").i)
        m.d.comb += ClockSignal("clk100").eq(platform.request("clk100").i)

        pll = m.submodules.pll = Pll(100e6, 4, 1, input_domain="clk100")
        pll.output_domain("clk50", 8)
        pll.output_domain("clk25", 40)

        sensor_digital = platform.request("sensor_digital")

        # timed pins
        m.submodules.timing_generator = DomainRenamer("clk50")(SlothTimingGenerator(sensor_digital))

        # always on pins
        for pin_name in ["J20"]:
            m.d.comb += sensor_digital[pin_name].o.eq(1)

        # spi pins
        spi = m.submodules.spi = DomainRenamer("clk25")(SpiController())
        m.d.comb += [
            sensor_digital["C16"].o.eq(spi.spi_cs),
            sensor_digital["C15"].o.eq(spi.spi_clk),
            sensor_digital["C14"].o.eq(spi.spi_copi),
            spi.fire.eq(sensor_digital["C5"].o),
        ]

        return m


if __name__ == "__main__":
    cli(Top, runs_on=(HedgehogPlatform,), possible_socs=(JTAGSocPlatform,))
