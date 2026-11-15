"""First-burst windows from the local raw fs_usage trace, from the first read's issue time to the last completion.

The raw trace is not public (it names Apple's protected asset paths), so this script needs your own trace:
sudo fs_usage -w -f filesys,diskio on the inference process, saved as text, during the same four prompts.
Run from the repository root: python3 analysis/burst_windows.py PATH_TO_TRACE
Writes results/burst_windows.json. The file in this repository is the output on the author's trace.
"""

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
READS = ROOT / "measurements" / "data" / "plots" / "ifp_reads.csv"
BLOCK = 294_912
PHASES = ("code", "math", "french", "japanese")


def first_read_durations(trace: Path) -> list[float]:
    """Duration in seconds of every pread of one block, in trace order."""
    out = []
    for line in trace.open(errors="replace"):
        if re.search(r"\bpread\b", line) and "B=0x48000" in line:
            out.append(float(re.findall(r"(\d+\.\d{6})", line)[-1]))
    return out


def main() -> None:
    reads = list(csv.DictReader(READS.open()))
    durations = first_read_durations(Path(sys.argv[1]))
    assert len(durations) == len(reads)
    out = {}
    for phase in PHASES:
        idx = [i for i, r in enumerate(reads) if r["phase"] == phase]
        t = [float(reads[i]["seconds_into_phase"]) for i in idx]
        n = 1
        while n < len(t) and t[n] - t[n - 1] < 0.12:
            n += 1
        window = t[n - 1] - t[0] + durations[idx[0]]
        out[phase] = {"reads": n, "ms": round(window * 1000, 1), "gib_s": round(n * BLOCK / 2**30 / window, 2)}
    wrapped = [int(r["offset_low32_bytes"]) for r in reads if int(r["offset_low32_bytes"]) % BLOCK == 0]
    out["max_wrapped_offset"] = max(wrapped)
    out["bytes_beyond_2_32"] = 4_948_197_376 - 2**32
    (ROOT / "results" / "burst_windows.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
