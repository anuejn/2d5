from pathlib import Path
from typing import List
from vcd.reader import TokenKind, tokenize
import sys
from collections import defaultdict
from pprint import pformat

FRAMES_TO_CAPTURE = 3
SHIFT = 80  # this is the right amount to lign up the changes of C5 with the start / end of the line
LINE_START = "J21"
FRAME_START = "C5"
CLOCKS = [
    "J5",
    "D6"
]
SIGNALS = [
    "J21",
    "J18",
    "J17",
    "J16",
    "J15",
    "J12",
    "J11",
    "J10",
    "J9",
    "J8",
    "J5",
    "D6",
    "C17",
    "C8",
    "C6",
    "C5",
    "C3",
]

import_path = sys.argv[1]
tokens = tokenize(Path(import_path).open("rb"))


timebase = 1e9 / 48e6

id_to_pin = {}
id_to_idx = {}
pin_to_idx = {}
pin_to_id = {}

current_time = 0
line_start = None
frame_start = None

current_traces = defaultdict(list)
lines = []

lines_since_frame_reset = 0
frame_lengths = []   


for token in tokens:
    if token.kind == TokenKind.TIMESCALE:
        timescale =  {"ps": 1e12, "ns": 1e9}[token.data.unit.value] / token.data.magnitude.value
        timebase = timescale / 48e6
    elif token.kind == TokenKind.VAR:
        id = token.data.id_code
        idx = len(id_to_idx)
        pin = token.data.reference
        if pin in SIGNALS:
            id_to_pin[id] = pin
            id_to_idx[id] = idx
            pin_to_idx[pin] = idx
            pin_to_id[pin] = id
    elif token.kind == TokenKind.CHANGE_TIME:
        current_time = token.data
    elif token.kind == TokenKind.CHANGE_SCALAR:
        value = int(token.data.value)
        id = token.data.id_code
        if not id in id_to_pin:
            continue
        if id == pin_to_id[FRAME_START] and value:
            frame_lengths.append(lines_since_frame_reset)
            lines_since_frame_reset = 0
            if len(frame_lengths) >= FRAMES_TO_CAPTURE:
                break
        if id == pin_to_id[LINE_START] and value:  # we are on a rising edge
            if line_start:
                line_length = current_time - line_start
                lines.append((current_traces, line_length))
                current_traces = defaultdict(list)
                line_start = current_time
                lines_since_frame_reset += 1
            else:
                line_start = current_time
        if line_start:
            time_since_line_start = current_time - line_start
            # time_since_line_start = round(time_since_line_start / timebase)
            current_traces[id_to_pin[id]].append((time_since_line_start, value))

print("frame lengths in lines:", frame_lengths)

# postprocessing:
for i, (traces, line_length) in enumerate(lines):
    # find enable signal for clocks
    for clock in CLOCKS:
        new = []
        last_falling_edge = None
        first = True
        for (time, value) in traces[clock]:
            if value: # rising edge
                if first:
                    new.append((time, 1))
                    first = False
                if last_falling_edge and time - last_falling_edge > timebase * 1.5:
                    new.append((last_falling_edge, 0))
                    last_falling_edge = None
                    new.append((time, 1))
            else: # falling edge
                last_falling_edge = time
        if last_falling_edge and line_length - last_falling_edge > timebase * 1.5:
            new.append((last_falling_edge, 0))
        traces[clock] = new

    # convert from ns to clock cycles
    for pin in traces.keys():
        for ii in range(len(traces[pin])):
            time, value = traces[pin][ii]
            traces[pin][ii] = (round(time / timebase), value)
    line_length = round(line_length / timebase)

    # shift all signals a bit to the left, so that the y-gated signals (J9 & C5) are not spanning multiple lines
    for pin in traces.keys():
        for ii in range(len(traces[pin])):
            time, value = traces[pin][ii]
            time += SHIFT
            if time >= line_length:
                time = time - line_length
            elif time < 0:
                time = line_length - time
            traces[pin][ii] = (time, value)
    
    lines[i] = (traces, line_length)


# generate master waveforms:
# if more than 40% of the waveforms do a certain transition, we take it
master_traces = {}
line_lengths = []
for pin in pin_to_id.keys():
    changes_and_counts = defaultdict(int)
    total_with_changes = 0
    for current_traces, line_length in lines:
        line_lengths.append(line_length)
        if len(current_traces[pin]) > 0:
            total_with_changes += 1
        for change in current_traces[pin]:
            changes_and_counts[change] += 1
    current_traces = [change for change, count in changes_and_counts.items() if count > total_with_changes * 0.4]
    current_traces = sorted(current_traces, key=lambda change: change[0])
    master_traces[pin] = current_traces
line_lengths = sorted(line_lengths)
line_length = line_lengths[len(line_lengths) // 2]
print("line length: ", line_length)


# plot the results for visual sanity check
import matplotlib.pyplot as plt

def plot_trace(changes, line_length, y_offset, **kwargs):
    x = []
    y = []
    for i, (time, value) in enumerate(changes):
        if i == 0:
            x.append(0)
            y.append(y_offset + (1 - value))
        x.append(time)
        x.append(time)
        if value:
            y.append(y_offset + 0)
            y.append(y_offset + 1)
        else:
            y.append(y_offset + 1)
            y.append(y_offset + 0)
    if len(y) > 0:
        x.append(line_length)
        y.append(y[-1])
    plt.plot(x, y, **kwargs)

count = defaultdict(int)
for i, pin in enumerate(pin_to_id.keys()):
    for traces, length in lines:
        trace = traces[pin]
        if not trace or count[pin] > 42:
            continue
        count[pin] += 1
        y_offset = 2*i
        plot_trace(trace, line_length, y_offset, alpha=0.05, c="black")
    plt.text(-10, y_offset, pin, fontsize=10, horizontalalignment="right")

for i, pin in enumerate(pin_to_id.keys()):
    plot_trace(master_traces[pin], line_length, 2*i, c="red")

plt.show()

# preprocess: ensure, that the state at time 0 is explicitly written (our hdl requires this)
for pin, trace in master_traces.items():
    if trace[0][0] != 0:
        trace.insert(0, (0, 1 - trace[0][1]))

# write the results of the analysis
output_file = Path(import_path + ".analysis").write_text(pformat(master_traces, width=200, indent=4))

