from pathlib import Path
import sys

import RigolWFM.wfm1000z as wfm1000z
from vcd import VCDWriter
from yaml import safe_load
from tqdm import tqdm



LENGTH = 12_000_000
variable_part = sys.argv[1].removesuffix(".vcd")
OFFSET = { # positive means 1 is later
    "exp30_iso100_lv": 16,
    "exp50_iso100_lv": 26,
    "exp100_iso100_photo": -9,
    "exp100_iso100_fhd": -12,
    "exp30_iso100_fhd": 1,
    "exp50_iso100_fhd": 8,
}.get(variable_part, 0)

setup1 = safe_load(Path("setup1.yaml").read_text())
setup2 = safe_load(Path("setup2.yaml").read_text())

sample_rate = 0
def load_raw_data(filename: str):
    data = wfm1000z.Wfm1000z.from_file(filename)
    assert data.header.la_offset == 0
    assert len(data.data.raw) == LENGTH * 2 + 512
    global sample_rate
    sample_rate = int(data.header.sample_rate_hz)
    return data.data.raw

data1 = load_raw_data(f"setup1_{variable_part}.wfm")
data2 = load_raw_data(f"setup2_{variable_part}.wfm")
if OFFSET > 0:
    data1 = data1[OFFSET*2:]
    LENGTH -= OFFSET
else:
    data2 = data2[-OFFSET*2:]
    LENGTH -= -OFFSET
# LENGTH //= 100


out_file = open(f"{variable_part}.vcd", "w")
vcd_writer = VCDWriter(out_file, timescale="1 ns", check_values=False)
vcd_signals1 = {
    i: vcd_writer.register_var(scope="", name=f"{name}_(setup1_{i})", var_type="wire", size=1, init=0)
    for i, name in setup1.items()
}
vcd_signals2 = {
    i: vcd_writer.register_var(scope="", name=f"{name}_(setup2_{i})", var_type="wire", size=1, init=0)
    for i, name in setup2.items()
}
for cycle in tqdm(range(LENGTH)):
    timestamp = cycle * 1_000_000_000 // sample_rate

    word = (data1[cycle * 2] << 8) | data1[cycle * 2 + 1]
    for i, signal in vcd_signals1.items():
        value = word >> i & 0b1
        vcd_writer.change(signal, timestamp, value)

    word = (data2[cycle * 2] << 8) | data2[cycle * 2 + 1]
    for i, signal in vcd_signals2.items():
        value = word >> i & 0b1
        vcd_writer.change(signal, timestamp, value)
vcd_writer.close(timestamp)
