# Prototype: offcut-matching backtest (synthetic data)

**Run:** `python3 offcut_backtest.py` (Python 3 standard library only, no install needed).

**What it proves:** the Gate 2 test from the case study works as a protocol. It replays the same project stream in date order through two policies and compares virgin plate use, with a feasibility check on every suggestion.

- **Baseline (assumed manual practice):** uses an offcut only if the whole job fits on it.
- **Matcher:** fills any compatible offcut (same grade and thickness, parts fit), partial fills allowed, then buys virgin plate for the rest.

**Result (20 synthetic runs of 60 projects):**

| | Baseline | Matcher |
|---|---|---|
| Plate waste, mean | 19.4% | 13.6% |
| Virgin plate per tonne of parts | 1.241 | 1.157 |
| Offcut stock left idle (t per run) | 187.7 | 7.4 |
| Infeasible suggestions | n/a | 0 |

Improvement is 5.8 points on average (range 5.3 to 6.7).

## Read this before trusting the number
- **The data is invented.** The baseline waste (about 19%) was tuned to a plausible manual plate waste, nothing more.
- **The baseline rule is my guess** about manual practice. A weak baseline makes the gain look large. The real gain could be much smaller, so a real target should be more modest.
- Parts are rectangles with no rotation, and packing is simple shelf packing. Real nesting uses true shapes.
- No kerf, no mill certificates or heat numbers, no project cost-loading, and no human rejections. All of these reduce the gain in practice.
- It shows the **test protocol and feasibility checks work**. It does not show the real saving. The real number comes from client data at Gate 1 and Gate 2.
