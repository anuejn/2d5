from amaranth import *
from naps import *
from naps.cores.peripherals.soc_memory import SocMemory

class SpiController(Elaboratable):
    """A simple SPI controller that can write 16 bit words to the 5D2 image sensor."""

    def __init__(self):
        self.length = ControlSignal(8, reset=5)
        self.fire = Signal()
        self.mem = Memory(width=16, depth=256, init=[
            0x0203, 0x1c00, 0x240e, 0x3005, 0x4242, 0x5c01
        ])

        self.spi_clk = Signal()
        self.spi_copi = Signal()
        self.spi_cs = Signal()

    def elaborate(self, platform):
        m = Module()

        fire_last = Signal()
        m.d.sync += fire_last.eq(self.fire)

        self.current_word = Signal.like(self.length)

        read_port = m.submodules.read_port = self.mem.read_port(domain="comb")

        with m.FSM():
            with m.State("IDLE"):
                m.d.sync += self.current_word.eq(0)
                m.d.comb += self.spi_clk.eq(1)
                with m.If(self.fire & ~fire_last):
                    m.next = "PREAMBLE_0"
            for i in range(20):
                with m.State(f"PREAMBLE_{i}"):
                    m.d.comb += self.spi_clk.eq(0)
                    if i >= 10:
                        m.d.comb += self.spi_cs.eq(1)
                    if i < 19:
                        m.next = f"PREAMBLE_{i + 1}"
                    else:
                        m.next = "WRITE_0_HIGH"
            for i in range(17):
                with m.State(f"WRITE_{i}_HIGH"):
                    m.d.comb += self.spi_cs.eq(1)
                    m.d.comb += self.spi_clk.eq(1)
                    m.d.comb += self.spi_copi.eq(read_port.data[max(15 - i, 0)])
                    if i >= 15:
                        m.d.comb += self.spi_clk.eq(1)
                    if i >= 16:
                        m.d.comb += self.spi_copi.eq(0)
                    m.next = f"WRITE_{i}_LOW"
                with m.State(f"WRITE_{i}_LOW"):
                    m.d.comb += self.spi_cs.eq(1)
                    m.d.comb += self.spi_clk.eq(0)
                    m.d.comb += self.spi_copi.eq(read_port.data[max(15 - i - 1, 0)])
                    if i >= 15:
                        m.d.comb += self.spi_clk.eq(1)
                        m.d.comb += self.spi_copi.eq(0)
                    if i < 16:
                        m.next = f"WRITE_{i + 1}_HIGH"
                    else:
                        with m.If(self.current_word == 0):
                            m.next = "POSTAMBLE_0"
                        with m.Else():
                            m.next = "POSTAMBLE_5"
                        m.d.sync += read_port.addr.eq(self.current_word + 1)
            for i in range(21):
                with m.State(f"POSTAMBLE_{i}"):
                    m.d.comb += self.spi_cs.eq(i < 17)
                    if i < 20:
                        m.next = f"POSTAMBLE_{i + 1}"
                    else:
                        with m.If(self.current_word < self.length):
                            m.d.sync += self.current_word.eq(self.current_word + 1)
                            m.next = "PREAMBLE_12"
                        with m.Else():
                            m.next = "IDLE"
                            m.d.sync += read_port.addr.eq(0)
                

        return m

    @driver_method
    def write(self, data):
        for i, v in enumerate(data):
            self.mem[i] = v
        self.fire = 1
        self.fire = 0
