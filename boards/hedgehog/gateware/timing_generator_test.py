import unittest
from amaranth import *
from naps import SimPlatform
from timing_generator import SlothTimingGenerator


class TimingGeneratorTest(unittest.TestCase):
    def test_sim_basic(self):
        platform = SimPlatform()

        dut = SlothTimingGenerator()

        def time_process():
            for i in range(10_000_000):
                yield

        platform.add_sim_clock("sync", 48e6)
        platform.add_process(time_process, "sync")
        platform.sim(dut)
