from amaranth import *
from naps import StatusSignal, ControlSignal, PulseReg

class PatternMatchCounter(Elaboratable):
    def __init__(self, input: Signal):
        self.input = input

        self.current = StatusSignal(len(input))
        self.pattern = ControlSignal(len(input))
        self.reset = PulseReg(1)

        self.match_count = StatusSignal(32)
        self.mismatch_count = StatusSignal(32)

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.current.eq(self.input)

        with m.If(self.input == self.pattern):
            m.d.sync += self.match_count.eq(self.match_count + 1)
        with m.Else():
            m.d.sync += self.mismatch_count.eq(self.mismatch_count + 1)

        m.submodules += self.reset
        with m.If(self.reset.pulse):
            m.d.sync += [
                self.match_count.eq(0),
                self.mismatch_count.eq(0)
            ]

        return m