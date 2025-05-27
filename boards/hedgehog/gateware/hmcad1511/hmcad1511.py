from amaranth import *
from amaranth.lib import io
from amaranth.lib.io import PortLike
from naps import ControlSignal, BasicStream, driver_method, ClockDebug

from .generic_input_gearbox import ISerdes
from .pattern_match_counter import PatternMatchCounter
from .spi import HMCAD1511SPI


class HMCAD1511(Elaboratable):
    def __init__(self):
        """A receiver for the HMCAD1511 serial bitstream
        """
        self.reset = ControlSignal()
        self.power_down = ControlSignal()

        self.output = BasicStream(64)
        self.output_domain = "frame_clk"
        self.pwr_en = ControlSignal(init=1)

    def elaborate(self, platform):
        m = Module()

        adc = platform.request("hmcad1511", dir='-')

        m.submodules.pwr_en = pwr_en = io.Buffer("o", adc.pwr_en)
        m.d.comb += pwr_en.o.eq(self.pwr_en)

        m.submodules.reset = reset = io.Buffer("o", adc.reset)
        m.d.comb += reset.o.eq(self.reset)

        m.submodules.power_down = power_down = io.Buffer("o", adc.power_down)
        m.d.comb += power_down.o.eq(self.power_down)

        m.submodules.clk = clk = io.Buffer("o", adc.clk)
        m.d.comb += clk.o.eq(ClockSignal())

        m.domains.bit_clk = ClockDomain(local=True)
        m.submodules.lclk = lclk = io.Buffer("i", adc.lclk)
        m.d.comb += ClockSignal("bit_clk").eq(lclk.i)

        #m.domains.frame_clk = ClockDomain()
        #m.submodules.fclk = fclk = io.Buffer("i", adc.fclk)
        #m.d.comb += ClockSignal("frame_clk").eq(fclk.i)

        m.submodules.clk_bit = ClockDebug("bit_clk")
        # m.submodules.clk_frame = ClockDebug("frame_clk")
        m.submodules.clk_sync = ClockDebug("sync")

        self.spi = m.submodules.spi = HMCAD1511SPI()

        for i, port in enumerate(adc.d):
            lane = m.submodules[f"lane_{i}"] = HMCAD1511Lane(port, "bit_clk")

        return m

    @driver_method
    def init(self):
        self.reset = 1
        self.reset = 0
        self.power_down = 1
        self.power_down = 0

        self.spi.set_test_pattern("sync")
        for i in range(8):
            lane = getattr(self, f"lane_{i}")
            print(f"training lane {i}...")
            lane.train()

    @driver_method
    def init(self):
        self.reset = 1
        self.reset = 0
        self.power_down = 1
        self.power_down = 0

        self.spi.set_test_pattern("sync")
        for i in range(8):
            lane = getattr(self, f"lane_{i}")
            print(f"training lane {i}...")
            lane.train()



class HMCAD1511Lane(Elaboratable):
    def __init__(self, port: PortLike, ddr_domain: str):
        self.port = port
        self.ddr_domain = ddr_domain


    def elaborate(self, platform):
        m = Module()

        self.iserdes = m.submodules.iserdes = ISerdes(self.port, width=8, ddr_domain=self.ddr_domain)
        self.pattern_match_counter = m.submodules.pattern_match_counter = PatternMatchCounter(self.iserdes.output.p)

        return m

    @driver_method
    def train(self, timeout=20):
        for _ in range(timeout):
            if self.pattern_match_counter.current == 0b11110000:
                return
            self.iserdes.slip_bit()
        raise TimeoutError("lane did not train")
