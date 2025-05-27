from amaranth import *
from naps import *
from naps.vendor.lattice_ecp5 import Pll
from hedgehog_platform import HedgehogPlatform
from liteeth_wrapper import LiteEthStreamSink

class Top(Elaboratable):
    runs_on = [HedgehogPlatform]

    def elaborate(self, platform: HedgehogPlatform):
        m = Module()

        pll = m.submodules.pll = Pll(100e6, 5, 1, input_domain="sync", reset_less_input=True)
        pll.output_domain("clk125", 10)

        m.submodules.clocking = ClockDebug("clk125")

        stream_source = m.submodules.stream_source = CounterStreamSource(32)
        fifo = m.submodules.fifo = BufferedAsyncStreamFIFO(stream_source.output, 128, o_domain="clk125")

        m.submodules.ethernet_sink = DomainRenamer("clk125")(LiteEthStreamSink(fifo.output))

        return m


if __name__ == "__main__":
    import os
    os.environ["AMARANTH_nextpnr_opts"] = "--timing-allow-fail"
    cli(Top)
