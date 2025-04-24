from amaranth import *
from naps import ControlSignal

TIMING = {
    'C17': [(0, 0), (4, 1), (68, 0)],
    'C3': [(0, 0), (80, 1), (88, 0)],
    'C6': [(0, 0), (418, 1), (528, 0)],
    'C8': [(0, 0), (2, 1), (254, 0)],
    'J10': [(0, 0), (4, 1), (52, 0), (422, 1), (494, 0), (868, 1), (884, 0), (892, 1), (908, 0)],
    'J11': [(0, 1), (56, 0), (72, 1)],
    'J12': [(0, 0), (84, 1), (862, 0)],
    'J15': [(0, 0), (84, 1), (110, 0), (418, 1), (858, 0)],
    'J16': [(0, 0), (84, 1), (110, 0), (262, 1), (402, 0)],
    'J17': [(0, 0), (32, 1), (80, 0)],
    'J18': [(0, 0), (32, 1), (80, 0)],
    'J21': [(0, 0), (80, 1), (88, 0)],
    'J8': [(0, 0), (60, 1), (72, 0), (866, 1), (886, 0), (890, 1), (910, 0)],
}

CLOCKS = {
    'J5': [(0, 1), (5, 0), (82, 1), (85, 0), (90, 1)],
    'D6': [(0, 1), (5, 0), (82, 1), (85, 0), (90, 1)],
}

# we actually shifted the pulse 4 counts to the left to make it easier to generate
# the pulse does not look like it is critically aligned with anything else
Y_GATED = {
        "J9": (
            [(0, 1), (1, 0), (388, 1), (389, 0)],  # gating in y direction
            [(0, 0), (48, 1), (84, 0)],  # gating in x direction
        ),
        "C5": (
            [(0, 1), (10, 0)],
            [(0, 1)]
        )
}



class SlothTimingGenerator(Elaboratable):
    def __init__(self, sensor_digital):
        self.line_length = ControlSignal(16, reset=1144)
        self.frame_lines = ControlSignal(16, reset=1400)
        self.sensor_digital = sensor_digital

    def elaborate(self, platform):
        m = Module()

        y_ctr = Signal(16)
        x_ctr = Signal(16)

        with m.If(x_ctr < self.line_length):
            m.d.sync += x_ctr.eq(x_ctr + 1)
        with m.Else():
            m.d.sync += x_ctr.eq(0)
            with m.If(y_ctr < self.frame_lines):
                m.d.sync += y_ctr.eq(y_ctr + 1)
            with m.Else():
                m.d.sync += y_ctr.eq(0)

        for pin_name, changes in TIMING.items():
            pin = Signal(name=pin_name)
            m.d.comb += Value.cast(self.sensor_digital[pin_name].o).eq(pin)
            m.submodules[pin_name] = PulseGenerator(x_ctr, pin, changes)

        for pin_name, changes in CLOCKS.items():
            enable = Signal(name=f"{pin_name}_enable")
            m.submodules[pin_name] = PulseGenerator(x_ctr, enable, changes)
            pin = Signal(name=pin_name)
            m.d.comb += Value.cast(self.sensor_digital[pin_name].o).eq(pin)
            m.d.comb += pin.eq(~x_ctr[0] & enable)

        for pin_name, (gating_y, gating_x) in Y_GATED.items():
            enable_y = Signal(name=f"{pin_name}_enable_y")
            m.submodules[f"{pin_name}_y"] = PulseGenerator(y_ctr, enable_y, gating_y)
            enable_x = Signal(name=f"{pin_name}_enable_x")
            m.submodules[f"{pin_name}_x"] = PulseGenerator(x_ctr, enable_x, gating_x)
            pin = Signal(name=pin_name)
            m.d.comb += Value.cast(self.sensor_digital[pin_name].o).eq(pin)
            m.d.comb += pin.eq(enable_x & enable_y)


        return m


class PulseGenerator(Elaboratable):
    def __init__(
        self, counter: Signal, pin: Signal, transition_points=[], controlable=False
    ):
        self.pin = pin
        self.counter = counter
        self.num_triggers = len(transition_points)
        for i, (time, value) in enumerate(transition_points):
            setattr(
                self,
                f"trig_{i}_time",
                ControlSignal(16, reset=time) if controlable else time,
            )
            setattr(
                self,
                f"trig_{i}_value",
                ControlSignal(1, reset=value) if controlable else value,
            )

    def elaborate(self, platform):
        m = Module()

        for i in range(self.num_triggers):
            time = getattr(self, f"trig_{i}_time")
            value = getattr(self, f"trig_{i}_value")
            with m.If(self.counter >= time):
                m.d.comb += self.pin.eq(value)

        return m
