# An experiment that glues everything together and tries to get a full sensor -> ethernet flow working on the micro
import os
from amaranth import *
from naps import *

from hmcad1511.s7_phy import HMCAD1511Phy
from packetizer import StreamPacketizer
from prjsloth_platform import PrjSlothPlatform


class Top(Elaboratable):
    runs_on=[PrjSlothPlatform]

    def __init__(self):
        self.adc_pwr = ControlSignal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += platform.request("power_ctl").en_adc_1v8.o.eq(self.adc_pwr)

        platform.ps7.fck_domain(100e6, "axi_hp")
        platform.ps7.fck_domain(50e6, "sync")

        p = Pipeline(m)
        p += HMCAD1511Phy()
        m.submodules.phy_output_info = StreamInfo(p.output)
        p += BufferedAsyncStreamFIFO(p.output, 2048, o_domain="axi_hp")
        p += StreamPacketizer(p.output, default_length=2048)
        p += DramPacketRingbufferStreamWriter(p.output, max_packet_size=0x800000, n_buffers=4)
        p += DramPacketRingbufferCpuReader(p.last)

        return m

if __name__ == "__main__":
    cli(Top)
