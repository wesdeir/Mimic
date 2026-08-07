"""Adaptive clicking engine: Markov state model + log-normal delay draw.

Part of Mimic. Split out of the original single-file Mimic.py.
"""

import csv
import time
import math
import random
from datetime import datetime
from dataclasses import dataclass, field
from collections import deque

import numpy as np
import win32api
import win32con

from .config import Config, ClickEnginePresets


# * Still need to figure out why the analysis returns seemingly wrong CPS
#   values. In game CPS mods and online CPS tests give me results different 
#   than what I calculate, but even AI agrees my logic is sound? What the fuck.
# ═════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class StateParams:
    """Mathematical preset values for specific clicking profiles."""
    name: str
    base_rate: float
    sigma: float
    phi: float
    sigma_shock: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not -1.0 < self.phi < 1.0:
            raise ValueError(f"{self.name}: phi must satisfy |phi| < 1")
        if self.sigma < 0.0:
            raise ValueError(f"{self.name}: sigma must be >= 0")
        object.__setattr__(
            self, "sigma_shock", self.sigma * float(np.sqrt(1.0 - self.phi ** 2))
        )


# base_rate is the MEDIAN period; sigma is now a RELATIVE (log-scale) spread,
# because delays are drawn log-normally -- real click data is right-skewed
# (clean sessions: mean 110.8ms vs median 94.0ms), which additive Gaussian
# noise cannot reproduce no matter how it is tuned.
STATES: dict[str, StateParams] = {
    "butterfly": StateParams("butterfly", base_rate=84.0,  sigma=0.30, phi=0.02),
    "jitter":    StateParams("jitter",    base_rate=93.0,  sigma=0.36, phi=0.06),
    "normal":    StateParams("normal",    base_rate=101.0, sigma=0.40, phi=0.10),
}

STATE_NAMES: list[str] = list(STATES.keys())
STATE_INDEX: dict[str, int] = {n: i for i, n in enumerate(STATE_NAMES)}

# Row-Stochastic Markov transition matrix for clicking styles
TRANSITION_MATRIX: np.ndarray = np.array([
    [0.985, 0.012, 0.003],  # from Butterfly
    [0.008, 0.984, 0.008],  # from Jitter
    [0.002, 0.010, 0.988],  # from Normal
], dtype=float)


# ═════════════════════════════════════════════════════════════════════════════
# OPTIMIZED BATCH RNG POOL
# ═════════════════════════════════════════════════════════════════════════════
class _Pool:
    """Amortizes numpy thread overhead down to nanoseconds to keep clicks smooth"""
    __slots__ = ("_rng", "_kind", "_block", "_buf", "_i")

    def __init__(self, rng: np.random.Generator, kind: str, block: int = 8192):
        self._rng = rng
        self._kind = kind
        self._block = int(block)
        self._buf = np.empty(0)
        self._i = 0

    def _refill(self) -> None:
        self._buf = (
            self._rng.standard_normal(self._block)
            if self._kind == "normal"
            else self._rng.random(self._block)
        )
        self._i = 0

    def next(self) -> float:
        if self._i >= self._buf.size:
            self._refill()
        value = self._buf[self._i]
        self._i += 1
        return float(value)


# ═════════════════════════════════════════════════════════════════════════════
# ADAPTIVE CLICKER ENGINE (CORE LOGIC)
# ═════════════════════════════════════════════════════════════════════════════
class AdaptiveClickerEngine:
    """Enhanced with integrated Markov matrix and smoothstep boundary crossfading"""

    def __init__(self, enhanced_mode=True, preset_name="Balanced"):
        self.enhanced_mode = enhanced_mode
        self.preset_name = preset_name
        self.total_clicks = 0
        self.session_start = datetime.now()
        self.combat_start = None
        self.click_history = deque(maxlen=50)
        self.recent_click_times = deque(maxlen=20)

        # Bounded: this used to be an unbounded list that the GUI re-summed and
        # re-plotted in full on every 500ms refresh, so cost grew all session.
        # 3000 delays is ~5 minutes of clicking -- plenty for a histogram.
        self.all_delays = deque(maxlen=3000)

        # Running moments so variance/std are O(1) per refresh instead of O(n).
        # These cover the whole session, not just the retained window.
        self._n = 0
        self._mean = 0.0
        self._m2 = 0.0          # Welford sum of squared deviations

        # User baseline parameters
        self.user_baseline = random.uniform(0.88, 1.12)
        self.drift = 0.0
        self.rhythm_phase = 0.0
        self.consecutive_clicks = 0
        self.pattern_breaks = 0
        self.last_click_wall = None   # for idle-based fatigue recovery

        # Event counters. The v4.0 Markov model replaced the old explicit
        # burst/pause/outlier machinery, but the analytics page and exports
        # still report these, so they are tracked as their modern equivalents:
        #   burst  = entries into the fastest state
        #   pause  = injected long-tail pauses
        #   outlier= delays beyond 2.5 sigma of the current state
        self.burst_count = 0
        self.pause_count = 0
        self.outlier_count = 0
        self.peak_cps = 0.0
        self.double_count = 0    # emulated hardware doubles this session

        # UI Graph tracking pipelines
        self.cps_history = deque(maxlen=60)
        self.cps_timestamps = deque(maxlen=60)

        # Crossfade settings (20 clicks is the optimal blending target)
        self.blend_steps = 20
        self._cdf = np.cumsum(TRANSITION_MATRIX, axis=1)
        self._cdf[:, -1] = 1.0  # float guard

        self._rng = np.random.default_rng()
        self._normals = _Pool(self._rng, "normal")
        self._uniforms = _Pool(self._rng, "uniform")

        # Per-instance copy so a preset can retune this engine without
        # mutating the module-level defaults shared by every other instance.
        self.states = dict(STATES)

        self.is_actively_clicking = False
        self.reset_state("normal")
        if preset_name:
            self.set_preset(preset_name)

    def set_preset(self, preset_name: str) -> None:
        """Retune the three states from a ClickEnginePresets entry.

        Presets are authored as absolute mean/std in milliseconds, but the
        engine draws log-normally from (median, relative sigma). These are the
        exact moment-matching conversions, so a preset's stated mean and std
        come out as the mean and std actually produced.
        """
        preset = ClickEnginePresets.PRESETS.get(preset_name)
        if not preset:
            return

        rebuilt = {}
        for name in STATE_NAMES:
            mean = float(preset.get(f"{name}_mean", STATES[name].base_rate))
            std = float(preset.get(f"{name}_std", 0.0))

            cv = (std / mean) if mean > 0 else 0.0
            sigma = math.sqrt(math.log(1.0 + cv * cv)) if cv > 0 else 0.0
            median = mean / math.exp(0.5 * sigma * sigma)

            rebuilt[name] = StateParams(
                name, base_rate=median, sigma=sigma, phi=STATES[name].phi
            )

        self.states = rebuilt
        self.preset_name = preset_name
        self.reset_state(STATE_NAMES[self._idx])

    def export_to_csv(self, filepath: str) -> int:
        """Write the retained delay buffer as CSV. Returns rows written.

        Schema matches MimicBenchmarkTool's export so the differential
        analysis page can compare a bot session against a human one.
        """
        delays = list(self.all_delays)
        with open(filepath, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["click_number", "relative_time_ms", "delay_ms",
                        "button", "click_type"])
            t = 0.0
            for i, d in enumerate(delays, start=1):
                t += d
                w.writerow([i, round(t, 3), round(d, 3), "left", "single-click"])
        return len(delays)

    def reset_state(self, initial_state: str = "normal") -> None:
        """Wipes and sets up current mathematical parameters cleanly"""
        if initial_state in STATE_INDEX:
            idx = STATE_INDEX[initial_state]
        else:
            idx = 2  # default to normal

        self._idx = idx
        params = self.states[STATE_NAMES[idx]]

        self._phi = params.phi
        self._sigma = params.sigma
        self._base = params.base_rate

        self._from_phi = params.phi
        self._from_sigma = params.sigma
        self._from_base = params.base_rate
        self._blend_remaining = 0

        # Stationary unit-variance seeding to break burn-in signatures
        self._u = self._normals.next()
        self.consecutive_clicks = 0

    @staticmethod
    def precise_sleep(duration_seconds: float):
        """Sleep with sub-millisecond accuracy without pegging a CPU core.

        The original spun on perf_counter() for the whole interval, holding one
        core at 100% for the entire session -- wasteful, and an odd load
        signature for something that is supposed to look like a person resting
        a finger on a mouse. Python 3.11+ backs time.sleep() with a
        high-resolution waitable timer on Windows, so coarse-sleeping to within
        a hair of the deadline and spinning only the last stretch gives the
        same precision at a fraction of the cost.
        """
        if duration_seconds <= 0:
            return

        deadline = time.perf_counter() + duration_seconds
        coarse = duration_seconds - 0.0015          # leave 1.5ms to spin
        if coarse > 0:
            time.sleep(coarse)
        while time.perf_counter() < deadline:
            pass

    def start_clicking(self):
        """Session re-randomization for tracking diversity"""
        if not self.is_actively_clicking:
            self.is_actively_clicking = True
            self.user_baseline = random.uniform(0.88, 1.12)
            self.drift = random.uniform(-0.15, 0.15)
            self.rhythm_phase = random.uniform(0, 2 * math.pi)

            # Flush AR(1) and blend states at the start of a combat session
            self.reset_state("normal")

            startup_delay = abs(random.gauss(0.09, 0.025))
            self.precise_sleep(startup_delay)

    def stop_clicking(self):
        if self.is_actively_clicking:
            self.is_actively_clicking = False
            self.reset_state("normal")

    def _advance_state(self) -> None:
        """Draws the next state using fast inverse-CDF searchsorted math"""
        row = self._cdf[self._idx]
        nxt = int(np.searchsorted(row, self._uniforms.next(), side="right"))
        if nxt >= row.size:
            nxt = row.size - 1
        if nxt == self._idx:
            return

        # Prepare smooth continuous crossfade origin metrics
        self._from_phi = self._phi
        self._from_sigma = self._sigma
        self._from_base = self._base
        self._idx = nxt
        self._blend_remaining = self.blend_steps
        self.pattern_breaks += 1
        if STATE_NAMES[nxt] == "butterfly":
            self.burst_count += 1

    def _advance_blend(self) -> None:
        """Advances parameters along an organic mathematical Smoothstep slope"""
        target = self.states[STATE_NAMES[self._idx]]
        if self._blend_remaining <= 0:
            self._phi = target.phi
            self._sigma = target.sigma
            self._base = target.base_rate
            return

        done = self.blend_steps - self._blend_remaining + 1
        alpha = done / self.blend_steps
        w = alpha * alpha * (3.0 - 2.0 * alpha)  # Smoothstep execution

        self._phi = (1.0 - w) * self._from_phi + w * target.phi
        self._sigma = (1.0 - w) * self._from_sigma + w * target.sigma
        self._base = (1.0 - w) * self._from_base + w * target.base_rate
        self._blend_remaining -= 1

    def check_cps(self) -> float:
        """Protects sustained network safety windows"""
        current_time = time.time()
        while self.recent_click_times and current_time - self.recent_click_times[0] > 5.0:
            self.recent_click_times.popleft()

        if len(self.recent_click_times) >= 2:
            recent_1s = [t for t in self.recent_click_times if current_time - t <= 1.0]
            if len(recent_1s) >= 16:
                return 0.08

            time_span = current_time - self.recent_click_times[0]
            avg_cps = len(self.recent_click_times) / time_span if time_span > 0 else 0
            if avg_cps > Config.SUSTAINED_CPS_CAP:
                return 0.05
        return 0.0

    def calculate_delay(self) -> float:
        """Consolidated pipeline utilizing Opus 5 biometric data mapping"""
        self._advance_state()
        self._advance_blend()

        # 1. Update unit-variance core noise line
        self._u = self._phi * self._u + math.sqrt(1.0 - self._phi * self._phi) * self._normals.next()

        # Formulate base interval from the smoothly crossfading targets.
        # Log-normal: base_rate is the median, sigma is relative spread. This
        # gives the right-skewed shape real clicking has (occasional long
        # intervals, a hard-ish floor) instead of a symmetric bell.
        base = self._base * math.exp(self._sigma * self._u)

        # 2. Continuous Exponential Fatigue Decay.
        # consecutive_clicks now decays while idle (see click()), so this
        # recovers during pauses instead of staying pinned at 1.22 all session.
        lambda_rate = 12.0
        max_fatigue_slowdown = 0.22
        fatigue_multiplier = 1.0 + (max_fatigue_slowdown * (1.0 - math.exp(-self.consecutive_clicks / lambda_rate)))
        base *= fatigue_multiplier

        # 3. User baseline multiplier and mean-reverting drift.
        # This used to be an unbounded random walk clamped at +-40%, which
        # never returned to centre and so stamped a persistent offset onto
        # every delay. That showed up as autocorrelation at *every* lag
        # (~+0.19 flat, vs a human 0.10 -> ~0 by lag 2) and as a runs-test
        # z of -11.7. An Ornstein-Uhlenbeck process drifts the same way but
        # decays back, leaving only short-range structure.
        base *= self.user_baseline
        rho = Config.DRIFT_REVERSION
        shock = Config.DRIFT_SIGMA * math.sqrt(1.0 - rho * rho)
        self.drift = rho * self.drift + shock * self._normals.next()
        base *= (1.0 + self.drift)

        # 4. Rhythmic Sinusoidal Oscillation Waves.
        # The phase step used to be 0.20-0.60 rad, a slow wave that dominated
        # the output's lag-1 autocorrelation (realized acf1 hit +0.95 against a
        # human +0.10). Stepping most of the way around the circle each click
        # keeps the rhythm texture without the memory.
        self.rhythm_phase = (self.rhythm_phase + random.uniform(1.1, 2.6)) % (2 * math.pi)
        rhythm_amount = 0.055 if self.enhanced_mode else 0.038
        base *= (1.0 + math.sin(self.rhythm_phase) * rhythm_amount)

        # 5. Occasional long pause. Real sessions put 1.85% of clicks past
        # 250ms and reach 475ms; the old engine emitted exactly zero of these,
        # so its distribution had no right tail at all.
        if self._uniforms.next() < 0.018:
            base += abs(random.gauss(0, 95.0))
            self.pause_count += 1

        if self._sigma > 0 and abs(self._u) > 2.5:
            self.outlier_count += 1

        # 6. Reflect at the boundaries rather than clamp. Clamping piles
        # probability mass onto the exact bound, which is a visible spike in a
        # delay histogram; reflecting folds it back and keeps the shape smooth.
        lo = Config.ENHANCED_MIN_DELAY_MS if self.enhanced_mode else Config.ABSOLUTE_MIN_DELAY_MS
        hi = Config.ENHANCED_MAX_DELAY_MS if self.enhanced_mode else Config.ABSOLUTE_MAX_DELAY_MS

        final = base
        for _ in range(4):
            if final < lo:
                final = lo + (lo - final)
            elif final > hi:
                final = hi - (final - hi)
            else:
                break
        final = min(hi, max(lo, final))

        # 7. Snap onto the USB polling grid.
        # A real mouse can only raise an event on a polling boundary, so human
        # inter-click intervals cluster near whole milliseconds (measured on
        # the clean recordings: 40% of intervals land within 0.1ms of an
        # integer, chi2=60 against uniform). A busy-wait loop has no such
        # constraint and produces a dead-flat sub-millisecond distribution,
        # which is a free synthetic-vs-hardware discriminator. Quantize, then
        # re-jitter by the amount real hardware jitters.
        if Config.POLL_RATE_HZ:
            grid = 1000.0 / Config.POLL_RATE_HZ
            final = round(final / grid) * grid + random.gauss(0.0, Config.POLL_JITTER_MS)
            final = min(hi, max(lo, final))

        self.click_history.append(final)
        self.all_delays.append(final)

        # Welford update -- keeps whole-session variance available in O(1)
        self._n += 1
        d = final - self._mean
        self._mean += d / self._n
        self._m2 += d * (final - self._mean)

        return final

    def click(self):
        """Executes click events with sub-millisecond precision clocks"""
        if self.combat_start is None:
            self.combat_start = datetime.now()

        safety = self.check_cps()
        if safety > 0:
            self.precise_sleep(safety)

        now = time.time()

        # Fatigue recovery: if the user stopped swinging for a moment, the hand
        # relaxes. Previously consecutive_clicks only reset on start/stop, so
        # the fatigue multiplier saturated at 1.22 and stayed there all session.
        if self.last_click_wall is not None:
            idle = now - self.last_click_wall
            if idle > 0.35:
                self.consecutive_clicks = int(self.consecutive_clicks * math.exp(-idle / 2.5))
        self.last_click_wall = now

        # Pull interval directly from the crossfaded math matrix.
        # This is the FULL press-to-press period, matching how
        # MimicBenchmarkTool records training data (on `pressed` only).
        delay_ms = self.calculate_delay()

        # Isolate pressure times to separate sub-millisecond structures
        pressure_ms = abs(random.gauss(26, 8))
        if pressure_ms < 15:
            pressure_ms = 15
        pressure_ms = min(pressure_ms, delay_ms * 0.6)

        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self.precise_sleep(pressure_ms / 1000.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)

        self.recent_click_times.append(now)
        self.total_clicks += 1
        self.consecutive_clicks += 1

        # Log results for graph callbacks
        current_cps = self.get_current_cps()
        self.cps_history.append(current_cps)
        self.cps_timestamps.append(time.time())

        # Optional hardware-double emulation. A double-clicking mouse fires a
        # second actuation a few ms after the real press; the game counts it as
        # a hit. Reproducing it keeps the synthetic click stream consistent
        # with what this account's hardware has always produced.
        consumed = pressure_ms
        if Config.DOUBLE_CLICK_EMULATION and self._uniforms.next() < Config.DOUBLE_RATE:
            gap = random.gauss(Config.DOUBLE_GAP_MS, Config.DOUBLE_GAP_STD_MS)
            need = gap + Config.DOUBLE_HOLD_MS
            # Only if the double fits inside the interval with room to spare.
            if gap > pressure_ms and need < delay_ms * 0.75:
                self.precise_sleep((gap - pressure_ms) / 1000.0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                self.precise_sleep(Config.DOUBLE_HOLD_MS / 1000.0)
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                consumed = need
                self.total_clicks += 1
                self.double_count += 1

        # The hold is PART of the interval, not additional to it. Sleeping the
        # full delay here on top of pressure_ms was inflating every period by
        # ~26ms, which is why in-game CPS mods always read lower than Mimic did.
        self.precise_sleep(max(0.0, delay_ms - consumed) / 1000.0)

    def get_current_cps(self) -> float:
        """Short-window CPS from the modelled press-to-press period."""
        if len(self.click_history) < 5:
            return 0.0
        recent = list(self.click_history)[-10:]
        avg_delay = sum(recent) / len(recent)
        return 1000.0 / avg_delay if avg_delay > 0 else 0.0

    def get_measured_cps(self) -> float:
        """Ground-truth CPS from real wall-clock press timestamps.

        This is what an in-game CPS counter sees. It should now agree with
        get_current_cps(); a persistent gap means the timing pipeline drifted.
        """
        if len(self.recent_click_times) < 2:
            return 0.0
        span = self.recent_click_times[-1] - self.recent_click_times[0]
        return (len(self.recent_click_times) - 1) / span if span > 0 else 0.0

    # ── statistics ────────────────────────────────────────────────────────
    # Restored: the v4.0 rewrite dropped these, but update_display() calls
    # them every 500ms. Now O(1) via Welford instead of O(n) over all_delays.

    def calculate_variance(self) -> float:
        """Variance over the recent window (short-term consistency)."""
        if len(self.click_history) < 2:
            return 0.0
        w = list(self.click_history)
        m = sum(w) / len(w)
        return sum((x - m) ** 2 for x in w) / len(w)

    def calculate_overall_variance(self) -> float:
        """Whole-session variance, O(1)."""
        return self._m2 / self._n if self._n > 1 else 0.0

    def calculate_std_dev(self) -> float:
        """Whole-session standard deviation, O(1)."""
        return math.sqrt(self.calculate_overall_variance())

    def get_detailed_stats(self) -> dict:
        """Snapshot consumed by RiskAssessor and the analytics page."""
        if self._n < 2:
            return {}

        var = self.calculate_overall_variance()
        std = math.sqrt(var)
        window = list(self.click_history)
        elapsed = (datetime.now() - self.session_start).total_seconds()

        cur = self.get_current_cps()
        self.peak_cps = max(self.peak_cps, cur)

        return {
            "total": self._n,
            "mean": self._mean,
            "avg_delay": self._mean,
            "variance": var,
            "std_dev": std,
            "min_delay": min(window) if window else 0.0,
            "max_delay": max(window) if window else 0.0,
            "avg_cps": 1000.0 / self._mean if self._mean > 0 else 0.0,
            "current_cps": cur,
            "max_cps": self.peak_cps,
            "peak_cps": self.peak_cps,
            "measured_cps": self.get_measured_cps(),
            "session_duration": elapsed,
            "session_seconds": elapsed,
            "state": STATE_NAMES[self._idx],
            "pattern_breaks": self.pattern_breaks,
            "burst_count": self.burst_count,
            "double_count": self.double_count,
            # What the game and anti-cheat actually count, doubles included.
            "effective_cps": (1000.0 / self._mean if self._mean > 0 else 0.0)
                             * (1.0 + (self.double_count / self._n if self._n else 0.0)),
            "pause_count": self.pause_count,
            "outlier_count": self.outlier_count,
            "enhanced_mode": self.enhanced_mode,
        }
