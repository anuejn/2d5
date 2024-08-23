from pathlib import Path
from typing import List
from vcd.reader import TokenKind, tokenize
import sys
from collections import defaultdict

J9_PULSES = 5
LINE_START = "J21"
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
    "C3",
]

import_path = sys.argv[1]
tokens = tokenize(Path(import_path).open("rb"))


timebase = 1e9 / 48e6

id_to_name = {}
id_to_idx = {}
name_to_idx = {}
name_to_id = {}

current_time = 0
line_start = None
frame_start = None

changes = defaultdict(list)
changes_list = []
lines_since_j9 = 0
j9_lengths = []


def postprocessing(changes, length):
    # postprocessing: find enable signal for clocks
    for clock in CLOCKS:
        new = []
        last_falling_edge = None
        first = True
        for (time, value) in changes[clock]:
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
        if last_falling_edge and length - last_falling_edge > timebase * 1.5:
            new.append((last_falling_edge, 0))
        changes[clock] = new

    # postprocessing: convert from ns to clock cycles
    for name in changes.keys():
        for i in range(len(changes[name])):
            time, value = changes[name][i]
            changes[name][i] = (round(time / timebase), value)
    length = round(length / timebase)

    return changes, length


for token in tokens:
    if token.kind == TokenKind.TIMESCALE:
        timescale =  {"ps": 1e12, "ns": 1e9}[token.data.unit.value] / token.data.magnitude.value
        timebase = timescale / 48e6
    elif token.kind == TokenKind.VAR:
        id = token.data.id_code
        idx = len(id_to_idx)
        name = token.data.reference
        if name in SIGNALS:
            id_to_name[id] = name
            id_to_idx[id] = idx
            name_to_idx[name] = idx
            name_to_id[name] = id
    elif token.kind == TokenKind.CHANGE_TIME:
        current_time = token.data
    elif token.kind == TokenKind.CHANGE_SCALAR:
        value = int(token.data.value)
        id = token.data.id_code
        if not id in id_to_name:
            continue
        if id == name_to_id["J9"] and value:
            j9_lengths.append(lines_since_j9)
            lines_since_j9 = 0
            if len(j9_lengths) >= J9_PULSES:
                break
        if id == name_to_id[LINE_START] and value:  # we are on a rising edge
            if line_start:
                changes_list.append(postprocessing(changes, current_time - line_start))
                changes = defaultdict(list)
                line_start = current_time
                lines_since_j9 += 1
            else:
                line_start = current_time
        if line_start:
            time_since_line_start = current_time - line_start
            # time_since_line_start = round(time_since_line_start / timebase)
            changes[id_to_name[id]].append((time_since_line_start, value))

print("J9 lengths in lines:", j9_lengths)

# generate master waveforms:
# if more than 40% of the waveforms do a certain transition, we take it
master_changes = {}
length_list = []
for name in name_to_id.keys():
    changes_and_counts = defaultdict(int)
    total_with_changes = 0
    for changes, length in changes_list:
        length_list.append(length)
        if len(changes[name]) > 0:
            total_with_changes += 1
        for change in changes[name]:
            changes_and_counts[change] += 1
    changes = [change for change, count in changes_and_counts.items() if count > total_with_changes * 0.4]
    changes = sorted(changes, key=lambda change: change[0])
    master_changes[name] = changes
length_list = sorted(length_list)
print("line length: ", length_list[len(length_list) // 2])


# plot the results for visual sanity check
import matplotlib.pyplot as plt

def plot_trace(changes, i, **kwargs):
    x = []
    y = []
    for ii, (time, value) in enumerate(changes):
        if ii == 0:
            x.append(0)
            y.append(2*i + (1 - value))
        x.append(time)
        x.append(time)
        if value:
            y.append(2*i + 0)
            y.append(2*i + 1)
        else:
            y.append(2*i + 1)
            y.append(2*i + 0)
    if len(y) > 0:
        x.append(length)
        y.append(y[-1])
    plt.plot(x, y, **kwargs)

count = defaultdict(int)
for i, name in enumerate(name_to_id.keys()):
    for changes, length in changes_list:
        c = changes[name]
        if not c or count[name] > 42:
            continue
        count[name] += 1
        plot_trace(c, i, alpha=0.05, c="black")
    plt.text(-10, 2*i, name, fontsize=10, horizontalalignment="right")

for i, name in enumerate(name_to_id.keys()):
    plot_trace(master_changes[name], i, c="red")

plt.show()

# preprocess: ensure, that the state at time 0 is explicitly written (our hdl requires this)
for name, changes in master_changes.items():
    if changes[0][0] != 0:
        changes.insert(0, (0, 1 - changes[0][1]))

# write the results of the analysis
output_file = Path(import_path + ".analysis").write_text(str(master_changes))

