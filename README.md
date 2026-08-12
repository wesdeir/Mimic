# Mimic

**Synthetic generation of human mouse-click timing, fitted and validated against captured input data.**

Mimic is a Windows auto-clicker whose interesting half is the model underneath it. Rather than emitting fixed or uniformly-jittered delays, it reproduces the statistical structure of recorded human clicking: the right-skewed interval distribution, the negative lag-1 autocorrelation produced by motor-delay variance, long-range drift in click rate, fatigue decay, and the 1 kHz USB polling grid the original recordings were quantized onto.

The engine's constants are not invented. They are fitted to 60-second recordings of a single operator, captured and analyzed by the tooling in this repo (`click_data/`).

This is the active C++ / Dear ImGui implementation. The original Python/Tkinter version in `python_legacy/` is kept as the reference the C++ engine was ported from and is validated against; it is not under further development.

---

## The measurement side

Everything in the model traces back to a measurement. The capture tooling records raw press/release events and produces a per-session analysis (`click_data/*_STATS.txt`) covering:

- **Hardware double-click separation.** The operator's mouse exhibits switch bounce on ~17% of events, with a 35.2 ms ± 3.7 ms second actuation. These are real hits in-game but are not motor output, so the analyzer reports *effective CPS* (9.06) and *hand-only CPS* (7.55) separately and fits the motor model to the latter — the bounce repeats to under 1 ms, which no hand can do.
- **USB polling-rate inference.** Rayleigh scores across candidate rates (125/250/500/1000 Hz) identify the polling grid; the sample session scores 202.6 at 1000 Hz against <4 elsewhere.
- **Hold-time distribution and coupling.** Mean 39.8 ms ± 25.5 ms, and a consistent **+0.43 correlation between a press's hold time and the interval that follows it** — a structure the model has to reproduce, not just the marginals.
- **Fit diagnostics** — the statistics a detector can compute cheaply: autocorrelation at lags 1–3 (measured −0.111 / +0.134 / −0.117), runs-test *z*, skew (+5.70), kurtosis (+47.1), and coefficient of variation (0.594).

The measured negative lag-1 autocorrelation is the reason the model uses a Wing-Kristofferson decomposition rather than a plain renewal process — see below.

---

## The model

`AdaptiveClickerEngine` composes several layers per interval. Each exists because of something in the data:

| Component | Implementation | Why |
|---|---|---|
| **Long-memory noise** | Truncated ARFIMA(0,*d*,0) innovation filter, *d* ∈ [0.15, 0.45], 100-term MA expansion normalized to unit variance | Click rate wanders on timescales longer than any AR(1) can produce |
| **Wing-Kristofferson** | Central clock interval plus differenced motor delay, `M_k ~ Gamma(2, σ/2)` | Produces the negative lag-1 autocorrelation observed in the recordings |
| **Ex-Gaussian intervals** | Gaussian core plus a mean-shifted exponential tail | Matches the measured right skew (+5.70) that a symmetric distribution cannot |
| **Weber scaling** | `exp(cv · u)` on the interval mean | Timing variability scales with the interval, per the scalar-timing literature |
| **Fatigue** | `1 + f·(1 − exp(−n/λ))`, decaying during idle | Captured sessions show CPS falling from 14.3 to ~7.3 over 60 s |
| **Mean-reverting drift** | Ornstein-Uhlenbeck, ρ = 0.985 | Short-range session drift without an unbounded random walk |
| **Technique states** | 3-state Markov chain (butterfly / jitter / normal) with smoothstep crossfade | Hold-time and double-rate structure differs per technique |
| **Polling quantization** | Snap to the 1 kHz grid plus 0.19 ms jitter | The recordings are quantized; unquantized output is trivially distinguishable |
| **Double-click emulation** | Second actuation at a gap proportional to the interval | Reproduces the operator's hardware bounce signature |

Parameters drift slowly within bounds on every click, so no session is stationary and no two sessions are identical.

---

## Validation

```cmd
cmake --build build --target mimic_tests
build/tests/mimic_tests.exe
```

The Catch2 suite checks the engine three ways:

- **Golden-reference parity** against a frozen run of the Python implementation (`tools/python_reference/golden/`), so the port is provably faithful.
- **Calibration against `click_data/`** — generated moments are compared to the real recordings.
- **Closed-form checks** on the underlying math (log-normal moment matching, preset conversion, risk scoring).

---

## Building

Requires Windows 10/11, MSVC build tools with the Windows SDK, CMake 3.24+, and Git.

```cmd
git submodule update --init --recursive
cmake -S . -B build -G Ninja
cmake --build build --target Mimic
```

Produces `build/src/gui/Mimic.exe`. Catch2 is fetched via `FetchContent`; Dear ImGui is a pinned submodule under `third_party/imgui`.

---

## Using it

| Key | Action |
|-----|--------|
| `F4` | Toggle clicking on/off (global, works unfocused) |
| `Insert` | Show/hide the panel |
| Hold `LEFT CLICK` | Auto-click while enabled |
| `Up` / `Down` | Move between the mode toggle and presets |
| `Enter` | Apply the highlighted setting |

---

## Project layout

```
src/
  core/    headless engine, config, risk assessment (no GUI dependencies)
    engine/    AdaptiveClickerEngine, RNG pool, ring buffers, state params
    config/    fitted presets, tuning constants, risk assessor
    mouse/     synthetic input
  app/     click thread, physical-hold input hook, global hotkeys
  gui/     Dear ImGui panel, Win32/DX11 entry point
tests/     Catch2 suite (golden parity, calibration, closed-form)
tools/python_reference/    frozen reference output from python_legacy/
click_data/                captured recordings + per-session analysis
python_legacy/             original Python implementation (reference only)
```

---

## Current scope and known issues

**Scope.** v1 is the clicker, live stats, and three fitted presets in one compact panel. The Python version's fuller analytics surface — graphs, session history, differential comparison against a human baseline — is deferred, not designed out.

**Known issues**, kept here rather than in an issue tracker because they are model-correctness problems worth being explicit about:

- The FGN innovation ring initializes to zeros, so output variance ramps from ~86% to 100% over the first ~100 clicks. This is a reproducible start-of-session artifact that real data does not contain.
- `softReflect()` advances the FGN innovation state on every rejected redraw, perturbing the autocorrelation structure during boundary events. Impact scales sharply with target CPS.
- `simulateStream()` has diverged from `click()` in how it derives the double-click gap, so the offline validation path no longer models the live path exactly.
- Introducing a fixed target CPS made the Markov chain's contribution to interval *mean* inert; `phi_` and `sigma_` now only affect hold times and outlier counting. This is a design question, not a bug, but the code does not yet reflect the decision.
- `pollPhaseDrift_` is accumulated and never read; the effective grid drift scales with lifetime click count rather than elapsed time.

**Next.** The natural counterpart to a generator is a detector. Building a classifier that separates this engine's output from `click_data/` — and reporting where it succeeds — would turn the fit diagnostics above from a target into a measurement.

---

## Disclaimer

For educational and research purposes. Using automation in online games generally violates their Terms of Service and can result in account bans. Use on your own account at your own risk; the author accepts no responsibility for damages arising from use of this tool.
