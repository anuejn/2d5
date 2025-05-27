#!/usr/bin/env python3

from amaranth.build import Resource, Subsignal, Pins, DiffPairs, Attrs, PinsN
from amaranth_boards.zturn_lite_z010 import ZTurnLiteZ010Platform
from amaranth_boards.resources import SPIResource, I2CResource

__all__ = ["SlothHedgehogPlatform"]


class SlothHedgehogPlatform(ZTurnLiteZ010Platform):
    def __init__(self):
        super().__init__()
        self.add_resources([
            Resource("hmcad1511", 0,
                        Subsignal("d", DiffPairs("4 10 14 22 32 36 42 52", "6 12 16 24 34 38 44 54", dir='i', conn=("expansion", 0)), Attrs(IOSTANDARD="LVDS_25", DIFF_TERM="TRUE")),
                        Subsignal("lclk", DiffPairs("26", "28", dir='i', conn=("expansion", 0)), Attrs(IOSTANDARD="LVDS_25", DIFF_TERM="TRUE")),
                        Subsignal("fclk", DiffPairs("46", "48", dir='i', conn=("expansion", 0)), Attrs(IOSTANDARD="LVDS_25", DIFF_TERM="TRUE")),
                        Subsignal("clk", DiffPairs("56", "58", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVDS_25")),
                        Subsignal("reset", PinsN("3", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                        Subsignal("power_down", Pins("9", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     ),

            # hmcad
            SPIResource("hmcad1511_spi", 0,
                        cs_n="13", clk="5", copi="11", cipo="35",
                        attrs=Attrs(IOSTANDARD="LVCMOS25"),
                        conn=("expansion", 0)
            ),
            Resource("power_ctl", 0,
                     Subsignal("en_sensor_1v3", Pins("15", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_sensor_1v5", Pins("21", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_sensor_2v0", Pins("23", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_sensor_3v3", Pins("25", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_sensor_5v0", Pins("27", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_sensor_hv", Pins("31", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     Subsignal("en_adc_1v8", Pins("33", dir='o', conn=("expansion", 0)), Attrs(IOSTANDARD="LVCMOS25")),
                     ),

            Resource("sensor_digital", 0,
                     Subsignal("C17", Pins("73", dir="o", conn=("expansion", 0))),
                     Subsignal("C3", Pins("78", dir="o", conn=("expansion", 0))),
                     Subsignal("C6", Pins("84", dir="o", conn=("expansion", 0))),
                     Subsignal("C8", Pins("86", dir="o", conn=("expansion", 0))),
                     Subsignal("J10", Pins("108", dir="o", conn=("expansion", 0))),
                     Subsignal("J11", Pins("98", dir="o", conn=("expansion", 0))),
                     Subsignal("J12", Pins("87", dir="o", conn=("expansion", 0))),
                     Subsignal("J15", Pins("89", dir="o", conn=("expansion", 0))),
                     Subsignal("J16", Pins("95", dir="o", conn=("expansion", 0))),
                     Subsignal("J17", Pins("85", dir="o", conn=("expansion", 0))),
                     Subsignal("J18", Pins("103", dir="o", conn=("expansion", 0))),
                     Subsignal("J21", Pins("93", dir="o", conn=("expansion", 0))),
                     Subsignal("J8", Pins("104", dir="o", conn=("expansion", 0))),

                     Subsignal("J20", Pins("64", dir="o", conn=("expansion", 0))),

                     Subsignal("J5", Pins("100", dir="o", conn=("expansion", 0))),
                     Subsignal("D6", Pins("76", dir="o", conn=("expansion", 0))),

                     Subsignal("J9", Pins("106", dir="o", conn=("expansion", 0))),
                     Subsignal("C5", Pins("80", dir="o", conn=("expansion", 0))),

                     Subsignal("C16", Pins("75", dir="o", conn=("expansion", 0))),
                     Subsignal("C15", Pins("63", dir="o", conn=("expansion", 0))),
                     Subsignal("C14", Pins("61", dir="o", conn=("expansion", 0))),
                     Attrs(IOSTANDARD='LVCMOS33'),
            ),
        ])
