from textwrap import dedent
from amaranth import *
from amaranth.build import *
from amaranth_boards.ecpix5 import ECPIX585Platform
from naps.soc.fatbitstream import File
from naps import program_fatbitstream_local


class HedgehogPlatform(ECPIX585Platform):
    def __init__(self):
        super().__init__()
        self.connect_5d2_pmod()

    def connect_5d2_pmod(self, pmods = (0, 1, 2, 3)):
        # these mappings cmome from the 5d2_pmod/5d2_pmod.pdf schematic
        mapping = [
            # PmodX, PinX, Sensor Pin
            (0, 1,  "D6"),
            (0, 7,  "D4"),
            (0, 2,  "D3"),
            (0, 8,  "C3"),
            (0, 3,  "C4"),
            (0, 9,  "C5"),
            (0, 4,  "C6"),
            (0, 10, "C8"),

            (1, 1,  "C14"),
            (1, 7,  "C15"),
            (1, 2,  "C16"),
            (1, 8,  "C17"),
            (1, 3,  "J22"),
            (1, 9,  "J21"),
            (1, 4,  "J20"),
            (1, 10, "J19"),

            (2, 1,  "J18"),
            (2, 7,  "J17"),
            (2, 2,  "J16"),
            (2, 8,  "J15"),
            (2, 3,  "J14"),
            (2, 9,  "J13"),
            (2, 4,  "J12"),
            (2, 10, "J11"),

            (3, 1,  "J10"),
            (3, 7,  "J9"),
            (3, 2,  "J8"),
            (3, 8,  "J5"),
            (3, 3,  "I3"),
            (3, 9,  "I7"),
            (3, 4,  "I8"),
        ]

        self.add_resources([
                Resource("sensor_digital", 0,
                    *[Subsignal(sensor_pin, Pins(str(pin), dir="o", conn=("pmod", pmod))) for pmod, pin, sensor_pin in mapping],
                    Attrs(IO_TYPE='LVCMOS33'),
                ),
        ])
    
    def generate_openocd_conf(self):
        yield File("openocd.cfg", dedent(r"""
            adapter driver ftdi
            ftdi vid_pid 0x0403 0x6010
            ftdi channel 0
            ftdi layout_init 0xfff8 0xfffb
            reset_config none
            adapter speed 25000
            jtag newtap dut tap -irlen 8 -expected-id 0x81113043
            init
            scan_chain
        """))

    
    def program_fatbitstream(self, name, **kwargs):
        program_fatbitstream_local(name, **kwargs)