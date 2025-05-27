from amaranth import *
from amaranth.lib.wiring import Component
from hedgehog_platform import HedgehogPlatform
from naps import PacketizedStream, ControlSignal, StatusSignal, driver_method, driver_property, BufferedSyncStreamFIFO, StreamInfo
from liteeth.gen import UDPCore
from liteeth.phy import LiteEthECP5PHYRGMII
from litex.build.generic_platform import Pins, Subsignal
from litex.build.lattice import LatticePlatform
from litex.soc.integration.builder import Builder
import tempfile
from pathlib import Path

from PacketizedStream2UDP import StreamPacketBuffer


MAC_ADDRESS=0x10e2d5000000
IP_ADDRESS="169.254.1.42"


_io = [
    # Clk / Rst
    ("sys_clock", 0, Pins(1)),
    ("sys_reset", 1, Pins(1)),

    # IP/MAC Address.
    ("mac_address", 0, Pins(48)),
    ("ip_address",  0, Pins(32)),

    # RGMII PHY Pads
    ("rgmii_clocks", 0,
        Subsignal("tx", Pins(1)),
        Subsignal("rx", Pins(1))
    ),
    ("rgmii", 0,
        Subsignal("rst_n",   Pins(1)),
        Subsignal("int_n",   Pins(1)),
        Subsignal("mdio",    Pins(1)),
        Subsignal("mdc",     Pins(1)),
        Subsignal("rx_ctl",  Pins(1)),
        Subsignal("rx_data", Pins(4)),
        Subsignal("tx_ctl",  Pins(1)),
        Subsignal("tx_data", Pins(4))
    ),
]

def generate_liteeth_core():
    core_config = {
        "phy": LiteEthECP5PHYRGMII,
        "phy_tx_delay" : 0e-9,
        "phy_rx_delay" : 0e-9,
        "device"       : "LFE5UM5G-85F-8BG554I",
        "vendor"       : "lattice",
        "toolchain"    : "trellis",

        "clk_freq"        : int(50e6),
        "data_width"      : 32,

        "mac_address"     : MAC_ADDRESS,
        "ip_address"      : IP_ADDRESS,

        "tx_cdc_depth"    : 16,
        "tx_cdc_buffered" : True,
        "rx_cdc_depth"    : 16,
        "rx_cdc_buffered" : True,

        "udp_ports": {
            "udp": {
                "data_width" : 32,
                "mode"       : "streamer",
            }
        }
    }

    platform = LatticePlatform(core_config["device"], io=[], toolchain="trellis")
    platform.add_extension(_io)

    soc = UDPCore(platform, core_config)

    dir = tempfile.mkdtemp(prefix="liteeth")
    builder = Builder(soc, compile_gateware=False, output_dir=dir, gateware_dir=dir)
    builder.build(build_name="liteeth")
    verilog = (Path(dir) / "liteeth.v").read_text()
    print(dir)
    return verilog


class LiteEthStreamSink(Elaboratable):
    def __init__(self, input_stream: PacketizedStream):
        self.input = input_stream

        ip = 0
        for i, byte in enumerate("169.254.83.15".split(".")):
             ip |= int(byte) << ((3-i) * 8)
        self.ip_address = ControlSignal(32, init=ip)
        self.port = ControlSignal(16, init=1234)

    def elaborate(self, platform):
        m = Module()

        # m.submodules.before_buffer = StreamInfo(self.input)
        # stream_packet_buffer = m.submodules.stream_packet_buffer = StreamPacketBuffer(self.input)
        # m.submodules.after_buffer = StreamInfo(stream_packet_buffer.output)


        rgmii = platform.request("eth_rgmii", dir="-")
        rgmii_int = platform.request("eth_int", dir="-")

        platform.add_clock_constraint(rgmii.rx_clk.io, 125e6)
        platform.add_clock_constraint(rgmii.tx_clk.io, 125e6)


        verilog = generate_liteeth_core()
        platform.add_file("liteeth.v", verilog)
        m.submodules.liteeth = Instance("liteeth", 
                i_sys_clock=ClockSignal(),
                i_sys_reset=ResetSignal(),

                o_rgmii_rst_n=rgmii.rst.io,
                i_rgmii_clocks_rx=rgmii.rx_clk.io,
                o_rgmii_clocks_tx=rgmii.tx_clk.io,
                i_rgmii_int_n=rgmii_int.io,
                o_rgmii_mdc=rgmii.mdc.io,
                i_rgmii_mdio=rgmii.mdio.io,
                i_rgmii_rx_ctl=rgmii.rx_ctrl.io,
                i_rgmii_rx_data=rgmii.rx_data.io,
                o_rgmii_tx_ctl=rgmii.tx_ctrl.io,
                o_rgmii_tx_data=rgmii.tx_data.io,

                i_udp_ip_address=self.ip_address,
                i_udp_udp_port=self.port,

                i_udp_sink_data=self.input.payload,
                i_udp_sink_last=self.input.last,
                o_udp_sink_ready=self.input.ready,
                i_udp_sink_valid=self.input.valid,

                # o_udp_source_data=,
                # o_udp_source_error=,
                # o_udp_source_last=,
                i_udp_source_ready=1,
                # o_udp_source_valid=,
        )

        return m
    
    @driver_method
    def set_ip(self, ip_str):
        ip = 0
        for i, byte in enumerate(ip_str.split(".")):
             ip |= int(byte) << ((3-i) * 8)
        self.ip_address = ip

    @driver_property
    def ip(self):
         parts = [(str(self.ip_address >> ((3-i) * 8) & 0xff)) for i in range(4)]
         return ".".join(parts)
