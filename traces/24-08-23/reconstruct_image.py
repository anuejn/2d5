from wave import WaveParser
import numpy as np
import matplotlib.pyplot as plt
import sys

parser = WaveParser({"verbose": False})
parser.parse(sys.argv[1])
sample_period = parser.waveforms[0]['header'].x_increment
frame_start, ap, an, clk = [wfm['data'] for wfm in parser.waveforms]
analog = ap - an


# find the lines by the absence of the clock
clk_thresholded =  (clk > (3.3 / 2))
last_high = 0
seperators = []
for i, sample in enumerate(clk_thresholded):
    if sample:
        run_length = i - last_high
        if run_length > 50:
            seperators.append((last_high + 1))
        last_high = i

len(seperators)


# do some analysis of the lines
lines = []
for start, end in zip(seperators, seperators[1:]):
    last = False
    count = 0
    start_of_current_clock = 0
    line = []
    for i, sample in enumerate(clk_thresholded[start:end]):
        if last and not sample:  # falling edge
            samples = analog[start+start_of_current_clock:start+i]
            px_value = np.mean(samples)
            line.append(px_value)
            count += 1
            start_of_current_clock = i
        last = sample
    lines.append(line)

    if False:
        x = np.arange((end - start) * sample_period, step=sample_period)
        plt.scatter(x, (clk_thresholded[start:end] - 0.5) / 2)
        plt.scatter(x, analog[start:end])
        plt.show()


max_length = max(len(line) for line in lines)
for line in lines:
    while len(line) < max_length:
        line.append(0)
image = np.array(lines)
plt.imshow(image, aspect='auto')
plt.show()