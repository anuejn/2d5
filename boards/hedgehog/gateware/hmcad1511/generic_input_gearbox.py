from amaranth import *
from amaranth.lib import stream
from amaranth.lib.io import PortLike, DDRBuffer
from amaranth.lib.wiring import Component, Out
from naps import driver_method, ControlSignal


class ISerdes(Component):
    """The interface of a generic input gearbox.
    The goal is to be able to implement this on different FPGA architectures to be able to write higher level interfaces
    like HDMI, MIPI or the HMCAD1511 PHY in a platform-agnostic fashion.

    The API is only the output stream and the @drivermethod's. These can be used to implement link-training.
    Everything else is an implementation detail.

    This module requires two clock domains:
    * the `sync` domain. This is the domain in which the output data is produced.
    * the ddr_domain. At each edge of this clock domain the input data is sampled
    This core expects that freq_sync * input_width >= freq_ddr / 2 and that the clocks are related
    (no clock drift, generated from the same source)

    This is also the pure-amaranth reference implementation, that does not use any platform dependent primitives. It is not
    optimal and does not support delay but can be used as a baseline. Different platforms may provide their own
    implementation that can support higher data rates and bit alignment.
    """

    def __init__(self, port: PortLike, *, width: int, ddr_domain: str):
        super().__init__({
            "output": Out(stream.Signature(width, always_ready=True)),
        })
        self.width = width
        self.ddr_domain = ddr_domain
        self.port = port
        self.slip_toggle = ControlSignal()

        self.current_word_level_alignment = 0  # driver only


    def elaborate(self, platform):
        m = Module()

        slip = Signal()
        last_slip_toggle = Signal()
        with m.If(last_slip_toggle != self.slip_toggle):
            m.d.sync += last_slip_toggle.eq(self.slip_toggle)
            m.d.comb += slip.eq(1)

        write_index = Signal(range(self.width))
        m.d.sync += write_index.eq((write_index + 2 + slip) % self.width)

        ddr_buffer = m.submodules.ddr_buffer = DDRBuffer("i", self.port, i_domain=self.ddr_domain)

        output = Signal(self.width)
        m.d.sync += output.bit_select(write_index, 1).eq(ddr_buffer.i[0])
        m.d.sync += output.bit_select((write_index + 1) % self.width, 1).eq(ddr_buffer.i[0])

        with m.If((write_index == self.width - 1) | (write_index == self.width - 2)):
            m.d.comb += [
                self.output.valid.eq(1),
                self.output.p.eq(output)
            ]

        return m


    @driver_method
    def get_delay_range(self) -> range:
        """Returns the range of the underlying hardware primitive in hardware dependent taps"""
        return range(1)

    @driver_method
    def set_delay(self, delay: int):
        """Sets the delay tap (bit level alignment). should be in the range returned by `get_delay_range`"""
        assert delay in self.get_delay_range()

    @driver_method
    def get_delay(self):
        """Returns the delay tap (bit level alignment)."""
        return 0

    @driver_method
    def increase_delay(self):
        """Increases the delay by one unit. This might be faster than setting it directly with `set_delay`
        When the delay control is already at its maximum, nothing happens.
        """
        pass

    @driver_method
    def decrease_delay(self):
        """Decreases the delay by one unit. This might be faster than setting it directly with `set_delay`
        When the delay control is already at its minimum, nothing happens.
        """
        pass

    @driver_method
    def slip_bit(self):
        """skips one bit and thus changes the word level alignment."""
        self.current_word_level_alignment = (self.current_word_level_alignment + 1) % self.width
        self.slip_toggle = not self.slip_toggle

    @driver_method
    def get_word_level_alignment(self, word_level_alignment: int):
        """Returns the word level alignment. It is in range(self.width)"""
        return self.current_word_level_alignment

    @driver_method
    def set_word_level_alignment(self, word_level_alignment: int):
        """Sets the word level alignment directly. It should be in range(self.width)"""
        assert word_level_alignment in range(self.width)
        while self.get_word_level_alignment(word_level_alignment) != word_level_alignment:
            self.slip_bit()
