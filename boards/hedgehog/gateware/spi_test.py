import unittest
from amaranth import *
from naps import SimPlatform
from spi import SpiController


class SPITest(unittest.TestCase):
    def test_sim_basic(self):
        platform = SimPlatform()

        dut = SpiController()

        def time_process():
            # liveview mode is 020f 1c00 240e 3005 4242 5c01
            yield dut.mem[0].eq(0x020f)
            yield dut.mem[1].eq(0x1c00)
            yield dut.mem[2].eq(0x240e)
            yield dut.mem[3].eq(0x3005)
            yield dut.mem[4].eq(0x4242)
            yield dut.mem[5].eq(0x5c01)
            yield dut.length.eq(5)
            yield dut.fire.eq(1)
            yield
            yield dut.fire.eq(0)
            for i in range(1000):
                yield

        platform.add_sim_clock("sync", 48e6)
        platform.add_process(time_process, "sync")
        platform.sim(dut)

    def test_sim_original_data(self):
        platform = SimPlatform()
        dut = SpiController()

        def time_process():
            # liveview mode is 020f 1c00 240e 3005 4242 5c01
            yield dut.fire.eq(1)
            yield
            yield dut.fire.eq(0)
            for i in range(1000):
                yield

        platform.add_sim_clock("sync", 48e6)
        platform.add_process(time_process, "sync")
        platform.sim(dut)
