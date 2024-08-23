from pathlib import Path
from typing import List
from yaml import safe_load
from vcd.reader import TokenKind, tokenize
import sys

import_path = sys.argv[1]

setup = safe_load(Path("extract_cfg.yaml").read_text())
start: int = setup["start"]
stop: int = setup["stop"]
out_frequency: int = setup["out_frequency"]
out_period_ns = 1e9 / out_frequency
signals: List[str] = setup["signals"]

output_file = Path(import_path + ".extracted.bin").open("wb")
tokens = tokenize(Path(import_path).open("rb"))

id_to_idx = {}
active = False
current_word = 0
last_written = None

for token in tokens:
    if token.kind == TokenKind.VAR:
        if token.data.reference in signals:
            id_to_idx[token.data.id_code] = signals.index(token.data.reference)
    elif token.kind == TokenKind.CHANGE_SCALAR:
        if token.data.id_code in id_to_idx:
            idx = id_to_idx[token.data.id_code]
            current_word = current_word & (0xffffffff ^ (1 << idx)) | (int(token.data.value) << idx)

    if not active:
        if token.kind == TokenKind.CHANGE_TIME and token.data >= start:
            active = True
    else:
        if token.kind == TokenKind.CHANGE_TIME:
            repeat = 1
            if last_written:
                delta_t = token.data - last_written
                repeat = delta_t / out_period_ns
            for i in range(round(repeat)):
                as_bytes = current_word.to_bytes(8, byteorder="little") 
                output_file.write(as_bytes)
                print(" ".join([f"{x:08b}" for x in as_bytes]))
            if token.data > stop:
                break
            last_written = token.data
