from amaranth import *
from amaranth.lib.cdc import PulseSynchronizer
from naps import *
from naps.vendor.xilinx_s7.clocking import Pll

from hmcad1511.s7_phy import HMCAD1511Phy
from sloth_hedgehog_platform import SlothHedgehogPlatform
from spi import SpiController
from timing_generator import SlothTimingGenerator
from hedgehog_platform import HedgehogPlatform

class Top(Elaboratable):
    runs_on=[SlothHedgehogPlatform]

    def elaborate(self, platform: HedgehogPlatform):
        m = Module()

        platform.ps7.fck_domain(200e6, "pll_input")
        mmcm = m.submodules.mmcm = Pll(100e6, 10, 1, "pll_input")
        mmcm.output_domain("sync", 100)
        mmcm.output_domain("clk_spi", 100)
        mmcm.output_domain("axi_hp", 10)


        sensor_digital = platform.request("sensor_digital")

        # timed pins
        timing_generator = m.submodules.timing_generator = SlothTimingGenerator(sensor_digital)

        start_of_frame = Signal()
        m.d.comb += start_of_frame.eq((timing_generator.y_ctr == 0) & (timing_generator.x_ctr == 0))

        # always on pins
        for pin_name in ["J20"]:
            m.d.comb += getattr(sensor_digital, pin_name).o.eq(1)

        # spi pins
        spi = m.submodules.spi = DomainRenamer("clk_spi")(SpiController())
        m.d.comb += [
            sensor_digital.C16.o.eq(spi.spi_cs),
            sensor_digital.C15.o.eq(spi.spi_clk),
            sensor_digital.C14.o.eq(spi.spi_copi),
            spi.fire.eq(start_of_frame),
        ]

        # adc pipeline
        m.d.comb += platform.request("power_ctl").en_adc_1v8.o.eq(1)


        p = Pipeline(m)
        p += HMCAD1511Phy()
        p.output.last = Signal() @ DOWNWARDS
        psync = m.submodules.pulse_sync = PulseSynchronizer("sync", "frame_clk")
        m.d.comb += [
            psync.i.eq(start_of_frame),
            p.output.last.eq(psync.o)
        ]
        m.submodules.adc_stream_info = DomainRenamer("frame_clk")(StreamInfo(p.output))
        p += BufferedAsyncStreamFIFO(p.output, 2048, o_domain="axi_hp")
        p += DramPacketRingbufferStreamWriter(p.output, max_packet_size=0x800000, n_buffers=4)
        p += DramPacketRingbufferCpuReader(p.last)


        return m

    @driver_method
    def start_server(self):
        from http.server import BaseHTTPRequestHandler
        from http.server import HTTPServer
        import os, mmap
        import time

        outer = self

        class RequestHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.send_header("Content-type", "application/octet-stream")
                self.end_headers()

                buf = (outer.dram_packet_ringbuffer_cpu_reader.current_write_buffer - 1) % outer.dram_packet_ringbuffer_cpu_reader.n_buffers
                base = getattr(outer.dram_packet_ringbuffer_cpu_reader, f"buffer{buf}_base")
                length = getattr(outer.dram_packet_ringbuffer_cpu_reader, f"buffer{buf}_level")

                fd = os.open("/dev/mem", os.O_RDONLY)
                with mmap.mmap(fd, length, prot=mmap.PROT_READ, offset=base) as mm:
                    start = time.time()
                    cpy = mm.read()
                    print(f"took {time.time() - start}s")
                os.close(fd)
                self.wfile.write(cpy)

        webServer = HTTPServer(("0.0.0.0", 8080), RequestHandler)

        try:
            webServer.serve_forever()
        except KeyboardInterrupt:
            pass

        webServer.server_close()
        print("Server stopped.")


if __name__ == "__main__":
    cli(Top)
