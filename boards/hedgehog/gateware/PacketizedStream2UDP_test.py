import unittest
from naps import *
from PacketizedStream2UDP import StreamPacketBuffer

class TestStreamPacketBuffer(unittest.TestCase):
    def test_basic(self):
        platform = SimPlatform()

        input = PacketizedStream(32, name="input")
        dut = StreamPacketBuffer(input, buffer_size=16)
        

        def write_process():
            yield from write_packet_to_stream(input, list(range(8)))
            yield from write_packet_to_stream(input, list(range(8)))
            yield from write_packet_to_stream(input, list(range(8)))
        platform.add_process(write_process, "sync")

        def read_process():
            yield from wait_for(dut.output.valid)
            for i in range(3):
                while True:
                    payload, last, length = (yield from read_from_stream(dut.output, extract=("payload", "last", "length"), timeout=1))
                    assert length == 32
                    if last:
                        break
        platform.add_process(read_process, "sync")


        platform.add_sim_clock("sync", 100e6)
        platform.sim(dut)


    def test_overflow_drop(self):
        platform = SimPlatform()

        input = PacketizedStream(32, name="input")
        dut = StreamPacketBuffer(input, buffer_size=16)
        

        def write_process():
            yield from write_packet_to_stream(input, list(range(128)))
            yield from write_packet_to_stream(input, list(range(87)))
            yield from write_packet_to_stream(input, list(range(8)))
        platform.add_process(write_process, "sync")

        def read_process():
            yield from wait_for(dut.output.valid, timeout=1000)
            pkt = []
            while True:
                payload, last, length = (yield from read_from_stream(dut.output, extract=("payload", "last", "length"), timeout=1))
                pkt.append(payload)
                assert length == 32
                if last:
                    break
            assert pkt == list(range(8))
            assert (yield dut.dropped_too_long) == 2
        platform.add_process(read_process, "sync")


        platform.add_sim_clock("sync", 100e6)
        platform.sim(dut)
