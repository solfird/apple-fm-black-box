"""Figures and derived numbers of the report, computed from the files in measurements/data/ only (no model, no network).

Run from the repository root: uv run --with matplotlib==3.9.2 --with numpy python analysis/make_figures.py
Writes figures/fig_reads.pdf, figures/fig_reads.png, figures/fig_latency.pdf and results/derived_numbers.json.
"""

import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
matplotlib.rcParams.update(
    {"font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 9, "pdf.fonttype": 42}
)
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "measurements" / "data"
BLOCK = 294_912
FILE_BYTES = 4_948_197_376
HEADER = 163_840


def rows(name: str) -> list[dict[str, str]]:
    with open(DATA / "plots" / name, newline="") as f:
        return list(csv.DictReader(f))


def fig_reads() -> None:
    reads = rows("ifp_reads.csv")
    phases = {r["phase"]: r for r in rows("ifp_phase_summary.csv")}
    fig, axes = plt.subplots(2, 1, figsize=(6.4, 3.4), constrained_layout=True)
    for ax, phase, limit in zip(axes, ("code", "essay"), (9.5, 91.5), strict=True):
        t = np.array([float(r["seconds_into_phase"]) for r in reads if r["phase"] == phase])
        ax.hist(t, bins=np.arange(0, limit + 0.1, 0.1), color="#333333", edgecolor="#333333", linewidth=0.6)
        ax.set_xlim(0, limit)
        ax.set_ylabel("reads per 100 ms")
        p = phases[phase]
        ax.set_title(f"{phase} prompt: {p['output_tokens']} tokens, {p['expert_reads']} reads", loc="left", fontsize=9)
    axes[1].set_xlabel("seconds into the prompt")
    fig.savefig(ROOT / "figures" / "fig_reads.pdf")
    fig.savefig(ROOT / "figures" / "fig_reads.png", dpi=220)  # shown in the README


def fig_latency() -> dict[str, float]:
    c = rows("ctx_profile.csv")
    n = np.array([float(r["prompt_tokens"]) for r in c])
    ttft = np.array([float(r["ttft_s"]) for r in c])
    speed = np.array([float(r["decode_tok_s"]) for r in c])
    fits = {}
    for degree in (1, 2, 3):
        p = np.polyfit(n, ttft, degree)
        rss = float(((np.polyval(p, n) - ttft) ** 2).sum())
        fits[degree] = (p, rss, 1 - rss / float(((ttft - ttft.mean()) ** 2).sum()))
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.4), constrained_layout=True)
    grid = np.linspace(0, n.max(), 200)
    axes[0].scatter(n, ttft, s=12, color="#333333")
    axes[0].plot(grid, np.polyval(fits[2][0], grid), color="#999999")
    axes[0].set_xlabel("prompt tokens")
    axes[0].set_ylabel("time to first token (s)")
    counting = np.array([r["output_is_counting_task"] == "1" for r in c])
    axes[1].scatter(n[counting], speed[counting], s=12, color="#333333", label="same answer")
    axes[1].scatter(n[~counting], speed[~counting], s=12, facecolors="none", edgecolors="#333333", label="different answer")
    axes[1].legend(fontsize=8, frameon=False, loc="lower left")
    axes[1].set_xlabel("prompt tokens")
    axes[1].set_ylabel("writing speed (tokens/s)")
    axes[1].set_ylim(0, None)
    fig.savefig(ROOT / "figures" / "fig_latency.pdf")
    return {
        "quad_a": float(fits[2][0][0]),
        "quad_b": float(fits[2][0][1]),
        "quad_c": float(fits[2][0][2]),
        "r2_linear": fits[1][2],
        "r2_quadratic": fits[2][2],
        "r2_cubic": fits[3][2],
        "rss_ratio_linear_over_quadratic": fits[1][1] / fits[2][1],
    }


def lattice() -> dict[str, float]:
    """Read offsets against the block size, in both traces; offsets are stored as their low 32 bits."""
    out: dict[str, float] = {"low32_step_mod_block": 2**32 % BLOCK}
    for name in ("ifp_reads.csv", "ifp_cadence_reads.csv"):
        offsets = [int(r["offset_low32_bytes"]) for r in rows(name)]
        residues = {x % BLOCK for x in offsets}
        assert residues == {HEADER, 0}, residues  # 0 is HEADER after the wrap at 2^32
        assert all(x % 32_768 == 0 for x in offsets)
        out[f"{name}_reads"] = len(offsets)
    out["units_after_header"] = (FILE_BYTES - HEADER) / BLOCK
    reads = rows("ifp_reads.csv")
    out["distinct_units_ten_prompts"] = len({r["offset_low32_bytes"] for r in reads})
    out["share_of_units_touched"] = out["distinct_units_ten_prompts"] / out["units_after_header"]
    return out


def derived() -> dict[str, float]:
    phases = rows("ifp_phase_summary.csv")
    reads = sum(int(p["expert_reads"]) for p in phases)
    tokens = sum(int(p["output_tokens"]) for p in phases)
    seconds = sum(float(p["seconds"]) for p in phases)
    e8 = json.loads((DATA / "compare" / "energy_results.json").read_text())["models"]
    e4 = json.loads((DATA / "compare" / "energy_results_4bit.json").read_text())["models"]
    best = {}
    for name, e in (("8bit", e8), ("4bit", e4)):
        opened = [v["energy_above_idle_j"] for k, v in e.items() if k != "apple"]
        solved = [v["j_per_solved_above_idle"] for k, v in e.items() if k != "apple"]
        best[f"apple_share_of_best_open_total_{name}"] = e["apple"]["energy_above_idle_j"] / min(opened)
        best[f"apple_share_of_best_open_per_solved_{name}"] = e["apple"]["j_per_solved_above_idle"] / min(solved)
    return {
        "reads": reads,
        "tokens": tokens,
        "seconds": seconds,
        "mib_read": reads * BLOCK / 2**20,
        "bytes_per_token": reads * BLOCK / tokens,
        "mib_per_second": reads * BLOCK / 2**20 / seconds,
        "weights_per_block_at_2_bits": BLOCK * 8 / 2,
        "file_weights_billions_at_2_bits": FILE_BYTES * 8 / 2 / 1e9,
        "file_blocks": FILE_BYTES / BLOCK,
        "file_gib": FILE_BYTES / 2**30,
        "resident_mib": 40_680 * 16 / 1024,
        "resident_weights_billions_at_2_bits": 40_680 * 16_384 * 8 / 2 / 1e9,
        "cache_bytes_per_token": 293_601_280 / 8_192,
        **best,
    }


def main() -> None:
    fig_reads()
    out = {**fig_latency(), **derived(), **lattice()}
    (ROOT / "results" / "derived_numbers.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
