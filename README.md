# Black-Box Measurements of a Flash-Routed Mixture-of-Experts Language Model on a Mac

Solfird AI Technical Report 2026-01, November 2026. Julien Simon, Solfird AI.

**Report:** [`apple-fm-black-box.pdf`](apple-fm-black-box.pdf) (13 pages). DOI: [10.5281/zenodo.24244064](https://doi.org/10.5281/zenodo.24244064). Web version: <https://solfird.ai/reports/apple-fm-black-box/>.

## What the report shows

Apple says its on-device model AFM 3 Core Advanced stores 20 billion parameters in flash, activates 1 to 4 billion at a
time, and routes per prompt instead of per token. Apple has published no technical report on it. This report measures
the shipped model from outside, on one M3 Max MacBook Pro, without opening any model file. The measurements support
Apple's description on every point they reach, and they give the costs that Apple has not published.

| Result | Value | Basis |
|---|---|---|
| Expert store | One 4.95 GB file, read only in blocks of exactly 294,912 bytes, all on one grid | Measured |
| Size of one block | Three 1536 x 256 matrices at 2 bits per weight | Derived, inferred |
| First burst of a prompt | 152 to 228 blocks at 2.5 to 3.3 GiB/s for 15 to 24 ms; mean load 3.0 MiB/s | Measured |
| Reselection | Bursts every 31 to 32 tokens on three prompts, irregular on a long one | Measured, derived |
| Memory | Apple's two processes hold 2.0 to 3.4 GiB, against 14 to 16 GiB for a 4-bit open mixture-of-experts build | Measured |
| Attention cache | 35,840 bytes per token, which excludes a uniform cache of 12 key-value heads | Derived, inferred |
| Tokenizer | Token counts match Gemma 3's tokenizer on 429 of 429 strings | Measured |
| Energy on 20 math problems | 35 to 36% of the lowest open build, without SSD and DRAM power (preliminary) | Measured |

Every statement in the report is labeled measured, derived or inferred. All results come from one machine.

## What is in this repository

| Path | Content |
|---|---|
| `apple-fm-black-box.pdf` | The report |
| `measurements/` | The full measurements: 263 files with the raw tables, the logs, the scripts that took them, and one record per finding. Start with `measurements/findings/INDEX.md` |
| `measurements/scripts/check_numbers.py` | Recomputes the main measured numbers from `measurements/data/` |
| `analysis/make_figures.py` | Computes the two data figures and every derived number of the report from `measurements/data/` |
| `analysis/burst_windows.py` | Computes the first-burst windows from a raw `fs_usage` trace |
| `results/` | Outputs of the two analysis scripts: `derived_numbers.json` and `burst_windows.json` (the second one from the author's trace) |
| `figures/` | The two data figures of the report |

`measurements/` is a copy, without change, of [`juliensimon/apple-fm-mac`](https://github.com/juliensimon/apple-fm-mac/tree/v1.0)
at tag v1.0, which the report cites. Those measurements were first published with an article, so the README and the
finding records in that folder refer to "the article". The report uses the same data.

## Reproduce the numbers and the figures

No model, no network access and no Mac are needed. You need Python 3.10 or later and [`uv`](https://docs.astral.sh/uv/).

```sh
uv run --with matplotlib==3.9.2 --with numpy python analysis/make_figures.py
(cd measurements && python3 scripts/check_numbers.py)
git diff results/ figures/
```

`results/derived_numbers.json` must not change. The figures are rebuilt as PDF files, so `git` reports them as changed
when your font files differ from the author's. `measurements/README.md` has the commands that take the measurements
again on your own Mac.

## Where each result comes from

Section numbers are those of the report. All paths are in this repository; `m/` stands for `measurements/`.

| Result | Section | Evidence |
|---|---|---|
| First bursts and mean load | 4.1 | `m/data/plots/ifp_reads.csv`, `m/data/plots/ifp_phase_summary.csv`, `results/burst_windows.json`, `figures/fig_reads.pdf`, `m/findings/02-expert-reads` |
| File size, block size, read grid, weights in memory | 4.2 | `m/data/plots/ifp_reads.csv`, `m/data/plots/ifp_cadence_reads.csv`, `m/data/plots/parameter_budget.csv`, `results/derived_numbers.json`, `m/findings/03-loaded-pages-and-bit-width` |
| Reselection period | 4.3 | `m/data/plots/ifp_cadence_reads.csv`, `m/findings/02-expert-reads` |
| Memory of the two processes and of the open builds | 4.4 | `m/data/plots/footprint_categories.csv`, `m/data/compare/memory_protocol.json`, `m/data/compare/run_moe_footprint.log`, `m/findings/04-memory` |
| Energy | 4.5 | `m/data/compare/energy_results.json`, `m/data/compare/energy_results_4bit.json`, `m/findings/05-power-and-energy` |
| Accuracy on the same questions | 4.6 | `m/data/card_inputs/evals.json`, `m/data/compare/results_*.json`, `m/findings/09-same-questions` |
| Time to first token and writing speed against prompt length | 4.7 | `m/data/plots/ctx_profile.csv`, `figures/fig_latency.pdf`, `m/findings/10-speed-and-time-to-first-token` |
| Attention cache per token | 4.8 | `m/data/plots/iosurface_exact_sizes.csv`, `m/findings/16-attention-cache-shape` |
| Tokenizer match | 4.9 | `m/data/tokenizer_test/counts_all_429.csv`, `m/findings/07-tokenizer-and-google-endpoint` |
| Decode time by kind of text | 4.10 | `m/REPORT.md`, `m/data/plots/decode_bucket_fit.csv` |

## What you cannot reproduce from this repository

- **The root traces.** The reads from flash and the memory of Apple's processes were traced as root with `fs_usage`,
  `footprint` and memory-map listings. To repeat them you need the same machine class and macOS build: an Apple
  silicon Mac with macOS 27.0.1 (build 26A434) and Apple Intelligence on. The measurement repository has the commands.
- **The raw `fs_usage` trace.** It names Apple's protected asset paths, so it is not public. `measurements/data/plots/ifp_reads.csv`
  holds its reads (phase, time, offset, size) without those paths. `analysis/burst_windows.py` runs on a trace that
  you take yourself.
- **Apple's model files.** No model file was opened for this report, and none is here.

## Limits

One machine (MacBook Pro, Apple M3 Max, 48 GB), one macOS build, one model (Core Advanced, the larger of Apple's two
on-device models). The energy comparison is preliminary: it has no SSD and no DRAM power. The report's section on
limits has the full list.

## Cite

```bibtex
@techreport{simon2026applefm,
  author      = {Simon, Julien},
  title       = {Black-Box Measurements of a Flash-Routed Mixture-of-Experts Language Model on a {Mac}},
  institution = {Solfird AI},
  number      = {2026-01},
  year        = {2026},
  month       = nov,
  doi         = {10.5281/zenodo.24244064},
  url         = {https://github.com/solfird/apple-fm-black-box},
}
```

## Licenses

- The report, the figures and the data: CC BY 4.0, with the exceptions listed in [`LICENSE-DATA.md`](LICENSE-DATA.md) and in [`measurements/LICENSE-DATA.md`](measurements/LICENSE-DATA.md).
- The code: MIT, in [`LICENSE`](LICENSE).

This work had no funding from Apple or Google, and neither reviewed it. Contact: julien@solfird.ai.
