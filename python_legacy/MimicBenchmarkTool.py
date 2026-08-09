

import csv
import time
import os
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field
import math
import statistics
from pathlib import Path

try:
    from pynput import mouse
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False
    print("⚠️ pynput not installed. Install with: pip install pynput")

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False

@dataclass
class ClickEvent:
    """Represents a single click event with timing data"""
    click_number: int
    timestamp: float
    delay_ms: float = 0.0
    button: str = "LEFT"
    hold_ms: float = 0.0    # press-to-release duration, filled in on release

    def to_dict(self):
        return {
            'click_number': self.click_number,
            'timestamp': self.timestamp,
            'delay_ms': round(self.delay_ms, 3),
            'button': self.button,
            'hold_ms': round(self.hold_ms, 3)
        }

@dataclass
class ClickSession:
    """Manages a complete click tracking session"""
    session_name: str
    duration_seconds: int
    clicks: List[ClickEvent] = field(default_factory=list)
    start_time: float = 0.0
    end_time: float = 0.0
    is_active: bool = False
    double_click_threshold: float = 0.05  # 50ms threshold
    technique: str = "unlabelled"   # butterfly / jitter / normal -- lets the
                                    # clicker fit each style as its own state

    def add_click(self, button: str = "LEFT"):
        """Record a click event"""
        current_time = time.time()
        click_num = len(self.clicks) + 1
        delay_ms = 0.0
        if self.clicks:
            delay_ms = (current_time - self.clicks[-1].timestamp) * 1000

        click_event = ClickEvent(
            click_number=click_num,
            timestamp=current_time,
            delay_ms=delay_ms,
            button=button
        )
        self.clicks.append(click_event)
        return True

    def close_click(self):
        """Stamp the hold duration onto the most recent click, on release.

        Button hold time is a first-class anti-cheat signal and was previously
        never captured -- the listener ignored release events entirely, so the
        clicker's hold model had no measured data behind it at all.
        """
        if self.clicks and self.clicks[-1].hold_ms == 0.0:
            self.clicks[-1].hold_ms = (time.time() - self.clicks[-1].timestamp) * 1000
            return True
        return False

    def get_cps(self) -> float:
        """Calculate clicks per second"""
        if self.end_time == 0 or self.start_time == 0:
            return 0.0
        elapsed = self.end_time - self.start_time
        if elapsed > 0:
            return len(self.clicks) / elapsed
        return 0.0

    def count_double_clicks(self) -> int:
        """Count number of double-clicks"""
        double_click_count = 0
        for i in range(1, len(self.clicks)):
            if self.clicks[i].delay_ms < (self.double_click_threshold * 1000):
                double_click_count += 1
        return double_click_count

    def _calculate_fatigue_analysis(self, segment_size: int) -> Dict:
        """Analyze CPS trend over time segments"""
        if not self.clicks or len(self.clicks) < 2:
            return {}
        duration = self.end_time - self.start_time
        segment_count = max(1, int(duration / segment_size))
        fatigue_data = []

        for segment in range(segment_count):
            segment_start = self.start_time + (segment * segment_size)
            segment_end = segment_start + segment_size
            segment_clicks = [c for c in self.clicks if segment_start <= c.timestamp < segment_end]
            if segment_clicks:
                segment_cps = len(segment_clicks) / segment_size
                fatigue_data.append({
                    'segment': segment + 1,
                    'time_range': f"{segment * segment_size}s-{(segment + 1) * segment_size}s",
                    'clicks': len(segment_clicks),
                    'cps': round(segment_cps, 2)
                })
        return fatigue_data

    def _calculate_interval_distribution(self, delays: List[float]) -> Dict:
        """Categorize click intervals into buckets"""
        if not delays:
            return {}
        buckets = {
            '0-30ms': 0,
            '30-50ms': 0,
            '50-100ms': 0,
            '100-150ms': 0,
            '150-200ms': 0,
            '200-300ms': 0,
            '300ms+': 0
        }

        for delay in delays:
            if delay < 30:
                buckets['0-30ms'] += 1
            elif delay < 50:
                buckets['30-50ms'] += 1
            elif delay < 100:
                buckets['50-100ms'] += 1
            elif delay < 150:
                buckets['100-150ms'] += 1
            elif delay < 200:
                buckets['150-200ms'] += 1
            elif delay < 300:
                buckets['200-300ms'] += 1
            else:
                buckets['300ms+'] += 1
        return buckets

    def _calculate_percentiles(self, delays: List[float]) -> Dict:
        """Calculate percentile delays"""
        if not delays:
            return {}
        sorted_delays = sorted(delays)

        def percentile(data, p):
            index = int(len(data) * p / 100)
            return round(data[min(index, len(data) - 1)], 3)

        return {
            'p10': percentile(sorted_delays, 10),
            'p25': percentile(sorted_delays, 25),
            'p50_median': percentile(sorted_delays, 50),
            'p75': percentile(sorted_delays, 75),
            'p90': percentile(sorted_delays, 90)
        }

    def _calculate_burst_info(self, delays: List[float]) -> Dict:
        """Detect burst clicking"""
        if not delays:
            return {}
        burst_threshold = 50
        bursts = []
        current_burst = []

        for i, delay in enumerate(delays):
            if delay < burst_threshold:
                current_burst.append((i + 2, delay))
            else:
                if len(current_burst) >= 2:
                    bursts.append(current_burst)
                current_burst = []

        if len(current_burst) >= 2:
            bursts.append(current_burst)

        return {
            'total_bursts': len(bursts),
            'avg_burst_length': round(statistics.mean([len(b) for b in bursts]), 2) if bursts else 0,
            'fastest_burst_length': max([len(b) for b in bursts]) if bursts else 0
        }

    def _calculate_consistency(self, delays: List[float]) -> str:
        """Rate clicking consistency"""
        if not delays or len(delays) < 2:
            return "N/A"
        std_dev = statistics.stdev(delays)
        avg = statistics.mean(delays)
        cv = (std_dev / avg * 100) if avg > 0 else 0

        if cv < 15:
            return "Excellent"
        elif cv < 25:
            return "Good"
        elif cv < 40:
            return "Fair"
        else:
            return "Inconsistent"

    # ── data quality ──────────────────────────────────────────────────────
    # A recording is only worth fitting an engine to if it is actually the
    # human doing the clicking. These checks exist because a session that
    # reported 14.25 CPS turned out to be 8.14 CPS plus a faulty mouse.

    CHATTER_MAX_MS = 50.0      # below this, an event is a double-actuation candidate
    CHATTER_MAX_STD = 8.0      # mechanical bounce is far tighter than human timing.
                               # Was 4.0, which missed a real doubling session
                               # measured at 34.60ms +/- 4.31. Human fast
                               # intervals scatter by tens of ms, so 8ms still
                               # leaves a wide margin against false positives.

    def detect_chatter(self, delays: List[float]) -> Dict:
        """Identify mouse switch chatter -- phantom clicks from switch bounce.

        A worn switch re-actuates a fixed few milliseconds after a real press.
        The tell is the spread, not the speed: a human's fastest intervals
        still scatter by tens of ms, while bounce repeats to well under 1ms.
        Chatter is counted as a real click by every CPS meter, so it silently
        inflates the measured rate and corrupts any model fitted to it.
        """
        fast = [d for d in delays if d < self.CHATTER_MAX_MS]
        result = {
            'chatter_detected': False,
            'chatter_count': 0,
            'chatter_pct': 0.0,
            'chatter_mean_ms': 0.0,
            'chatter_std_ms': 0.0,
            'corrected_delays': list(delays),
        }
        if len(fast) < 3 or not delays:
            return result

        spread = statistics.pstdev(fast)
        if spread > self.CHATTER_MAX_STD:
            return result            # fast, but human-fast -- genuine burst clicking

        # Fold each phantom event back into the interval that preceded it.
        corrected = []
        for d in delays:
            if d < self.CHATTER_MAX_MS and corrected:
                corrected[-1] += d
            else:
                corrected.append(d)

        result.update(
            chatter_detected=True,
            chatter_count=len(fast),
            chatter_pct=round(100.0 * len(fast) / len(delays), 1),
            chatter_mean_ms=round(statistics.mean(fast), 3),
            chatter_std_ms=round(spread, 3),
            corrected_delays=corrected,
        )
        return result

    @staticmethod
    def estimate_poll_rate(delays: List[float]) -> Dict:
        """Infer the mouse's USB polling rate from interval quantization.

        A mouse can only raise an event on a polling boundary, so intervals
        cluster near multiples of 1000/rate ms. Scoring each candidate rate by
        the circular concentration of the residuals recovers the rate, which
        is what the clicker needs for Config.POLL_RATE_HZ.
        """
        out = {'poll_rate_hz': None, 'poll_confidence': 0.0, 'poll_scores': {}}
        if len(delays) < 30:
            return out

        best, best_score = None, 0.0
        for hz in (125, 250, 500, 1000):
            grid = 1000.0 / hz
            ang = [2.0 * math.pi * (d / grid) for d in delays]
            c = sum(math.cos(a) for a in ang) / len(ang)
            s = sum(math.sin(a) for a in ang) / len(ang)
            r = math.sqrt(c * c + s * s)          # mean resultant length, 0..1
            z = len(delays) * r * r               # Rayleigh statistic
            out['poll_scores'][hz] = round(z, 1)
            if z > best_score:
                best, best_score = hz, z

        # Rayleigh z above ~10 is strong evidence against uniform scatter.
        if best_score >= 10.0:
            out['poll_rate_hz'] = best
            out['poll_confidence'] = round(min(1.0, best_score / 50.0), 2)
        return out

    @staticmethod
    def fit_diagnostics(delays: List[float]) -> Dict:
        """The statistics an anti-cheat can compute for free.

        Reported so a recording can be judged, and so engine output can be
        held against the same yardstick as the human it is imitating.
        """
        n = len(delays)
        if n < 20:
            return {}

        mean = statistics.mean(delays)
        sd = statistics.pstdev(delays)

        def acf(lag):
            den = sum((x - mean) ** 2 for x in delays)
            if not den:
                return 0.0
            return sum((delays[i] - mean) * (delays[i + lag] - mean)
                       for i in range(n - lag)) / den

        med = statistics.median(delays)
        seq = [d > med for d in delays if d != med]
        runs = 1 + sum(1 for i in range(len(seq) - 1) if seq[i] != seq[i + 1])
        n1, n2 = sum(seq), len(seq) - sum(seq)
        z = 0.0
        if n1 and n2:
            exp = 1 + 2 * n1 * n2 / (n1 + n2)
            var = (exp - 1) * (exp - 2) / (n1 + n2 - 1)
            if var > 0:
                z = (runs - exp) / math.sqrt(var)

        return {
            'acf_lag1': round(acf(1), 3),
            'acf_lag2': round(acf(2), 3),
            'acf_lag3': round(acf(3), 3),
            'runs_z': round(z, 2),
            'skew': round(sum(((x - mean) / sd) ** 3 for x in delays) / n, 3) if sd else 0.0,
            'kurtosis': round(sum(((x - mean) / sd) ** 4 for x in delays) / n - 3, 3) if sd else 0.0,
            'mean_over_median': round(mean / med, 3) if med else 0.0,
            'cv': round(sd / mean, 3) if mean else 0.0,
        }

    def get_hold_stats(self) -> Dict:
        """Button hold duration -- a first-class anti-cheat signal."""
        holds = [c.hold_ms for c in self.clicks if c.hold_ms > 0]
        if len(holds) < 5:
            return {'hold_samples': len(holds)}

        # Does hold length predict the interval that follows? The clicker
        # currently assumes it does not; if it does, that is itself a tell.
        pairs = [(c.hold_ms, self.clicks[i + 1].delay_ms)
                 for i, c in enumerate(self.clicks[:-1]) if c.hold_ms > 0]
        corr = 0.0
        if len(pairs) >= 10:
            hs = [p[0] for p in pairs]
            ds = [p[1] for p in pairs]
            mh, md = statistics.mean(hs), statistics.mean(ds)
            num = sum((h - mh) * (d - md) for h, d in pairs)
            den = math.sqrt(sum((h - mh) ** 2 for h in hs) * sum((d - md) ** 2 for d in ds))
            corr = num / den if den else 0.0

        return {
            'hold_samples': len(holds),
            'hold_mean_ms': round(statistics.mean(holds), 3),
            'hold_std_ms': round(statistics.pstdev(holds), 3),
            'hold_min_ms': round(min(holds), 3),
            'hold_max_ms': round(max(holds), 3),
            'hold_median_ms': round(statistics.median(holds), 3),
            'hold_delay_corr': round(corr, 3),
        }

    def get_stats(self) -> dict:
        """Calculate detailed statistics"""
        if not self.clicks:
            return {}

        delays = [c.delay_ms for c in self.clicks[1:]]
        double_clicks = self.count_double_clicks()
        single_clicks = len(self.clicks) - double_clicks
        duration = self.end_time - self.start_time
        segment_size = max(1, int(duration / 10))

        fatigue_analysis = self._calculate_fatigue_analysis(segment_size)
        interval_distribution = self._calculate_interval_distribution(delays)
        percentiles = self._calculate_percentiles(delays)
        burst_info = self._calculate_burst_info(delays)

        chatter = self.detect_chatter(delays)
        corrected = chatter['corrected_delays']
        duration_s = self.end_time - self.start_time

        # True CPS counts intentional presses only, discarding switch bounce.
        true_clicks = len(corrected) + 1
        true_cps = (true_clicks / duration_s) if duration_s > 0 else 0.0

        verdict, reasons = "USABLE", []
        if chatter['chatter_detected']:
            # NOT a fault. A double-clicking mouse is standard kit in Minecraft
            # PvP -- each physical press registers twice, which is the point.
            # The game counts both, so both are real hits. They are excluded
            # here only because they are the SWITCH's timing, not the hand's,
            # and the motor model has to be fitted to the hand.
            verdict = "DOUBLE-CLICK MOUSE"
            reasons.append(
                f"{chatter['chatter_pct']}% of events are hardware doubles "
                f"({chatter['chatter_mean_ms']}ms +/- {chatter['chatter_std_ms']}ms) -- "
                f"expected on a double-clicking mouse, and they count as real "
                f"hits in game. Effective CPS {round(self.get_cps(), 2)}, "
                f"hand-only CPS {round(true_cps, 2)}. Motor stats below use "
                f"hand-only; the doubles are the switch, not you."
            )
        if len(corrected) < 200:
            if verdict == "USABLE":
                verdict = "THIN"
            reasons.append(
                f"Only {len(corrected)} clean intervals. Shape statistics (skew, "
                f"kurtosis) need ~500+ to be worth trusting; ~1000 to separate "
                f"clicking techniques."
            )

        return {
            'total_clicks': len(self.clicks),
            'single_clicks': single_clicks,
            'double_clicks': double_clicks,
            'duration_seconds': round(duration_s, 3),
            'cps': round(self.get_cps(), 2),
            'min_delay_ms': round(min(delays), 3) if delays else 0,
            'max_delay_ms': round(max(delays), 3) if delays else 0,
            'avg_delay_ms': round(statistics.mean(delays), 3) if delays else 0,
            'std_dev_ms': round(statistics.stdev(delays), 3) if len(delays) > 1 else 0,
            'consistency': self._calculate_consistency(delays),
            'fatigue_analysis': fatigue_analysis,
            'interval_distribution': interval_distribution,
            'percentiles': percentiles,
            'burst_info': burst_info,

            # data quality
            'technique': self.technique,
            'verdict': verdict,
            'verdict_reasons': reasons,
            'true_cps': round(true_cps, 2),
            'clean_intervals': len(corrected),
            'corrected_avg_delay_ms': round(statistics.mean(corrected), 3) if corrected else 0,
            'corrected_std_dev_ms': round(statistics.pstdev(corrected), 3) if len(corrected) > 1 else 0,
            **{k: v for k, v in chatter.items() if k != 'corrected_delays'},
            **self.estimate_poll_rate(corrected),
            **self.get_hold_stats(),
            'diagnostics': self.fit_diagnostics(corrected),
        }

    @staticmethod
    def _format_quality_report(stats: dict) -> str:
        """Front-load the verdict: is this recording safe to fit against?"""
        d = stats.get('diagnostics') or {}
        mark = {"USABLE": "[OK]", "THIN": "[THIN]", "CONTAMINATED": "[BAD]"}
        lines = [
            "═══════════════════════════════════════════════════════════════════════",
            "DATA QUALITY  --  read this before using the session",
            "═══════════════════════════════════════════════════════════════════════",
            "",
            f"Verdict: {mark.get(stats.get('verdict'), '[?]')} {stats.get('verdict', 'UNKNOWN')}",
            f"Technique: {stats.get('technique', 'unlabelled')}",
            "",
        ]
        for r in stats.get('verdict_reasons', []):
            lines.append(f"  ! {r}")
        if not stats.get('verdict_reasons'):
            lines.append("  Clean recording. Safe to fit engine parameters against.")
        lines.append("")

        if stats.get('chatter_detected'):
            lines += [
                "DOUBLE-CLICK MOUSE DETECTED  (this is normal kit for MC PvP)",
                f"  Hardware doubles: {stats['chatter_count']} ({stats['chatter_pct']}% of all clicks)",
                f"  Double interval : {stats['chatter_mean_ms']} ms +/- {stats['chatter_std_ms']} ms",
                f"  EFFECTIVE CPS   : {stats.get('cps')}   <-- what the game and anti-cheat see",
                f"  HAND-ONLY CPS   : {stats.get('true_cps')}   <-- what your fingers actually do",
                "",
                "  Both figures are real and both matter. Effective CPS is your",
                "  combat output and the number an anti-cheat thresholds on.",
                "  Hand-only CPS is what a human motor model must be fitted to,",
                "  since the switch bounce repeats to under 1ms and no hand can.",
                "  The motor statistics below deliberately exclude the doubles.",
                "",
            ]
        else:
            lines += [f"No hardware doubling in this session. CPS: {stats.get('true_cps')}", ""]

        rate = stats.get('poll_rate_hz')
        if rate:
            lines += [
                f"USB POLLING RATE: ~{rate} Hz (confidence {stats.get('poll_confidence')})",
                f"  Rayleigh scores: {stats.get('poll_scores')}",
                f"  -> set Config.POLL_RATE_HZ = {rate} in the clicker.",
                "",
            ]
        else:
            lines += ["USB POLLING RATE: indeterminate (need more clicks, or",
                      "  timestamps too jittery to see the grid).", ""]

        if stats.get('hold_samples', 0) >= 5:
            lines += [
                "BUTTON HOLD TIME",
                f"  mean {stats['hold_mean_ms']} ms +/- {stats['hold_std_ms']} ms   "
                f"median {stats['hold_median_ms']} ms",
                f"  range {stats['hold_min_ms']} - {stats['hold_max_ms']} ms   "
                f"(n={stats['hold_samples']})",
                f"  correlation with next interval: {stats['hold_delay_corr']:+.3f}",
                "",
            ]
        else:
            lines += ["BUTTON HOLD TIME: not captured (older recording).", ""]

        if d:
            lines += [
                "FIT DIAGNOSTICS  (what an anti-cheat can compute for free)",
                f"  autocorrelation  lag1 {d['acf_lag1']:+.3f}  lag2 {d['acf_lag2']:+.3f}  lag3 {d['acf_lag3']:+.3f}",
                f"  runs-test z      {d['runs_z']:+.2f}   (0 = human-like; large |z| = streaky)",
                f"  skew {d['skew']:+.3f}   kurtosis {d['kurtosis']:+.3f}   mean/median {d['mean_over_median']:.3f}",
                f"  coeff. variation {d['cv']:.3f}",
                f"  clean intervals  {stats.get('clean_intervals')}   "
                f"corrected mean {stats.get('corrected_avg_delay_ms')} ms "
                f"+/- {stats.get('corrected_std_dev_ms')} ms",
                "",
            ]
        return "\n".join(lines)

    def _export_stats_to_txt(self, stats: dict, filename: str):
        """Export detailed statistics to text file"""
        base, _ = os.path.splitext(filename)
        stats_filename = f"{base}_STATS.txt"

        quality_report = self._format_quality_report(stats)

        stats_content = f"""
{quality_report}
╔════════════════════════════════════════════════════════════════════╗
║ MIMIC CLICKING BENCHMARK ║
║ SESSION ANALYSIS REPORT ║
╚════════════════════════════════════════════════════════════════════╝

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

═══════════════════════════════════════════════════════════════════════
SESSION OVERVIEW
═══════════════════════════════════════════════════════════════════════

Total Clicks: {stats['total_clicks']}
├─ Single-clicks: {stats['single_clicks']} ({round(stats['single_clicks']/stats['total_clicks']*100, 1)}%)
└─ Double-clicks: {stats['double_clicks']} ({round(stats['double_clicks']/stats['total_clicks']*100, 1)}%)

Duration: {stats['duration_seconds']}s
CPS (Average): {stats['cps']} clicks/sec

═══════════════════════════════════════════════════════════════════════
CLICK TIMING ANALYSIS
═══════════════════════════════════════════════════════════════════════

Min Delay: {stats['min_delay_ms']} ms
Max Delay: {stats['max_delay_ms']} ms
Avg Delay: {stats['avg_delay_ms']} ms
Std Deviation: {stats['std_dev_ms']} ms
Consistency Rating: {stats['consistency']}

═══════════════════════════════════════════════════════════════════════
PERCENTILE ANALYSIS
═══════════════════════════════════════════════════════════════════════

P10 (Bottom 10%): {stats['percentiles'].get('p10', 'N/A')} ms
P25 (Lower Quarter): {stats['percentiles'].get('p25', 'N/A')} ms
P50 (MEDIAN): {stats['percentiles'].get('p50_median', 'N/A')} ms ★ Your comfort zone
P75 (Upper Quarter): {stats['percentiles'].get('p75', 'N/A')} ms
P90 (Top 10%): {stats['percentiles'].get('p90', 'N/A')} ms

═══════════════════════════════════════════════════════════════════════
CLICK INTERVAL DISTRIBUTION
═══════════════════════════════════════════════════════════════════════

0-30ms: {stats['interval_distribution'].get('0-30ms', 0):>4} clicks ({round(stats['interval_distribution'].get('0-30ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%)
30-50ms: {stats['interval_distribution'].get('30-50ms', 0):>4} clicks ({round(stats['interval_distribution'].get('30-50ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%) ← Primary zone
50-100ms: {stats['interval_distribution'].get('50-100ms', 0):>4} clicks ({round(stats['interval_distribution'].get('50-100ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%)
100-150ms: {stats['interval_distribution'].get('100-150ms', 0):>4} clicks ({round(stats['interval_distribution'].get('100-150ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%)
150-200ms: {stats['interval_distribution'].get('150-200ms', 0):>4} clicks ({round(stats['interval_distribution'].get('150-200ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%)
200-300ms: {stats['interval_distribution'].get('200-300ms', 0):>4} clicks ({round(stats['interval_distribution'].get('200-300ms', 0)/(stats['total_clicks']-1)*100, 1):>5}%)
300ms+: {stats['interval_distribution'].get('300ms+', 0):>4} clicks ({round(stats['interval_distribution'].get('300ms+', 0)/(stats['total_clicks']-1)*100 if stats['total_clicks']-1 > 0 else 0, 1):>5}%)

═══════════════════════════════════════════════════════════════════════
BURST ANALYSIS
═══════════════════════════════════════════════════════════════════════

Total Bursts Detected: {stats['burst_info'].get('total_bursts', 0)}
Avg Burst Length: {stats['burst_info'].get('avg_burst_length', 0)} clicks
Longest Burst: {stats['burst_info'].get('fastest_burst_length', 0)} consecutive clicks

═══════════════════════════════════════════════════════════════════════
FATIGUE ANALYSIS
═══════════════════════════════════════════════════════════════════════
"""

        if stats['fatigue_analysis']:
            for segment in stats['fatigue_analysis']:
                stats_content += f"\n{segment['time_range']:12} │ {segment['cps']:>5} CPS │ {segment['clicks']:>3} clicks"

        stats_content += f"""

═══════════════════════════════════════════════════════════════════════
FILES GENERATED
═══════════════════════════════════════════════════════════════════════

Location: Desktop/click_data/

• ClickData_YYYYMMDD_HHMMSS.csv (detailed click-by-click data)
• ClickData_YYYYMMDD_HHMMSS_STATS.txt (this analysis)

═══════════════════════════════════════════════════════════════════════
"""

        try:
            with open(stats_filename, 'w', encoding='utf-8') as f:
                f.write(stats_content)
            return stats_filename
        except (PermissionError, IOError) as e:
            print(f"Warning: Could not save stats to {stats_filename}: {e}")
            return None

    def export_to_csv(self, filename: str = None):
        """Export click data to CSV and generate stats"""
        if filename is None:
            desktop_path = Path.home() / "Desktop" / "click_data"
            try:
                desktop_path.mkdir(parents=True, exist_ok=True)
                data_dir = str(desktop_path)
                print(f"📁 Using folder: {data_dir}")
            except PermissionError:
                print(f"⚠️ Permission denied, using local directory...")
                data_dir = "click_data"
                os.makedirs(data_dir, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"ClickData_{timestamp}"
            csv_filename = os.path.join(data_dir, f"{base_filename}.csv")

            counter = 1
            while os.path.exists(csv_filename):
                csv_filename = os.path.join(data_dir, f"ClickData_{timestamp}_{counter}.csv")
                counter += 1

            filename = csv_filename

        fieldnames = ['click_number', 'timestamp', 'relative_time_ms', 'delay_ms', 'hold_ms', 'button', 'click_type']

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                session_start = self.clicks[0].timestamp if self.clicks else 0

                for click in self.clicks:
                    click_type = "double-click" if click.delay_ms < (self.double_click_threshold * 1000) and click.click_number > 1 else "single-click"
                    writer.writerow({
                        'click_number': click.click_number,
                        'timestamp': round(click.timestamp, 6),
                        'relative_time_ms': round((click.timestamp - session_start) * 1000, 3),
                        'delay_ms': round(click.delay_ms, 3),
                        'hold_ms': round(click.hold_ms, 3),
                        'button': click.button,
                        'click_type': click_type
                    })
        except (PermissionError, IOError) as e:
            print(f"❌ Error saving to {filename}: {e}")
            return None, None

        stats = self.get_stats()
        stats_file = self._export_stats_to_txt(stats, filename)

        return filename, stats_file

class ClickTrackerGUI:
    """Graphical interface for click tracking"""

    def __init__(self, root):
        if not PYNPUT_AVAILABLE:
            messagebox.showerror("Error", "pynput is required. Install with: pip install pynput")
            root.destroy()
            return

        self.root = root
        self.root.title("MIMIC Clicking Benchmark")
        self.root.geometry("900x900")

        # ════════════════════════════════════════════════════════════════
        # MIMIC v3.7 COLOR SCHEME - EXACT DASHBOARD MATCH
        # ════════════════════════════════════════════════════════════════

        # Primary Colors
        self.bgcolor = "#0D0D0D"         # Pure black background
        self.panel_color = "#1E1E1E"     # Charcoal panels
        self.header_color = "#1A1A1A"    # Slightly lighter header
        self.fg_color = "#CCCCCC"        # Light grey text (MIMIC STANDARD)
        self.accent_color = "#32B8C6"    # Teal accent (MIMIC PRIMARY)
        self.secondary_color = "#8D2D91" # Purple for secondary actions
        self.tech_accent = "#00E5FF"     # Cyan for tech elements
        self.button_color = "#252525"    # Dark button background
        self.button_hover = "#303030"    # Button hover state
        self.border_color = "#2A2A2A"    # Subtle borders
        self.inactive_color = "#888888"  # Disabled/inactive elements

        # Status Colors
        self.success_color = "#32B8C6"   # Teal for success
        self.warning_color = "#FFA500"   # Orange for warnings
        self.error_color = "#FF5555"     # Red for errors

        # Apply dark theme
        self.root.configure(bg=self.bgcolor)

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background=self.bgcolor, foreground=self.fg_color)
        style.configure('TFrame', background=self.bgcolor)
        style.configure('TButton', background=self.button_color, foreground=self.fg_color)

        self.session = None
        self.listener = None
        self.is_testing = False

        self.setup_ui()
        self.root.deiconify()

    def setup_ui(self):
        """Setup the GUI interface with MIMIC styling"""

        # ════════════════════════════════════════════════════════════════
        # TITLE SECTION
        # ════════════════════════════════════════════════════════════════

        title = tk.Label(
            self.root,
            text="🎯 MIMIC Clicking Benchmark",
            font=("Arial", 18, "bold"),
            bg=self.bgcolor,
            fg=self.fg_color
        )
        title.pack(pady=15)

        # ════════════════════════════════════════════════════════════════
        # DURATION SELECTION SECTION
        # ════════════════════════════════════════════════════════════════

        duration_frame = tk.Frame(self.root, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        duration_frame.pack(padx=15, pady=10, fill="x")

        duration_label = tk.Label(
            duration_frame,
            text="⏱️ Test Duration (seconds)",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        )
        duration_label.pack(pady=(8, 5))

        self.duration_var = tk.IntVar(value=5)
        durations = [1, 5, 10, 30, 60, 100]

        button_frame = tk.Frame(duration_frame, bg=self.panel_color)
        button_frame.pack(pady=8)

        for duration in durations:
            rb = tk.Radiobutton(
                button_frame,
                text=str(duration),
                variable=self.duration_var,
                value=duration,
                bg=self.panel_color,
                fg=self.fg_color,
                selectcolor=self.accent_color,
                activebackground=self.button_hover,
                activeforeground=self.fg_color,
                font=("Arial", 10)
            )
            rb.pack(side="left", padx=8)

        # Technique label. Without it every recording pools together, and the
        # clicker cannot fit butterfly/jitter/normal as separate states -- it
        # has to interpolate them, which is guesswork dressed up as data.
        tk.Label(
            duration_frame,
            text="🖱️ Clicking Technique (label your recording)",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))

        self.technique_var = tk.StringVar(value="normal")
        technique_frame = tk.Frame(duration_frame, bg=self.panel_color)
        technique_frame.pack(pady=(0, 6))

        for tech in ("butterfly", "jitter", "normal"):
            tk.Radiobutton(
                technique_frame,
                text=tech.capitalize(),
                variable=self.technique_var,
                value=tech,
                bg=self.panel_color,
                fg=self.fg_color,
                selectcolor=self.accent_color,
                activebackground=self.button_hover,
                activeforeground=self.fg_color,
                font=("Arial", 10)
            ).pack(side="left", padx=10)

        tk.Label(duration_frame, text="", bg=self.panel_color, height=1).pack()

        # ════════════════════════════════════════════════════════════════
        # CONTROL BUTTONS SECTION
        # ════════════════════════════════════════════════════════════════

        control_frame = tk.Frame(self.root, bg=self.bgcolor)
        control_frame.pack(pady=15, fill="x", padx=15)

        self.start_btn = tk.Button(
            control_frame,
            text="▶ Start Test",
            command=self.start_test,
            width=18,
            bg=self.accent_color,
            fg="#000000",
            activebackground="#2AA4B0",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold")
        )
        self.start_btn.pack(side="left", padx=5)

        self.stop_btn = tk.Button(
            control_frame,
            text="⏹ Stop Test",
            command=self.stop_test,
            state="disabled",
            width=18,
            bg=self.secondary_color,
            fg="#ffffff",
            activebackground="#6A3AD9",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold")
        )
        self.stop_btn.pack(side="left", padx=5)

        self.export_btn = tk.Button(
            control_frame,
            text="💾 Export Results",
            command=self.export_session,
            state="disabled",
            width=18,
            bg=self.tech_accent,
            fg="#000000",
            activebackground="#00C7D9",
            relief=tk.FLAT,
            cursor="hand2",
            font=("Arial", 10, "bold")
        )
        self.export_btn.pack(side="left", padx=5)

        # ════════════════════════════════════════════════════════════════
        # LIVE STATUS SECTION
        # ════════════════════════════════════════════════════════════════

        status_label = tk.Label(
            self.root,
            text="📊 Live Status",
            font=("Arial", 12, "bold"),
            bg=self.bgcolor,
            fg=self.accent_color
        )
        status_label.pack(pady=(15, 5))

        self.status_frame = tk.Frame(self.root, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        self.status_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.status_text = tk.Text(
            self.status_frame,
            height=8,
            width=100,
            wrap="word",
            state="disabled",
            bg=self.header_color,
            fg="#CCCCCC",
            font=("Courier", 9),
            insertbackground=self.accent_color
        )
        self.status_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        scrollbar = tk.Scrollbar(
            self.status_frame,
            orient="vertical",
            command=self.status_text.yview,
            bg=self.panel_color,
            activebackground=self.accent_color
        )
        scrollbar.pack(side="right", fill="y")
        self.status_text.config(yscrollcommand=scrollbar.set)

        # ════════════════════════════════════════════════════════════════
        # SESSION RESULTS SECTION
        # ════════════════════════════════════════════════════════════════

        results_label = tk.Label(
            self.root,
            text="📈 Session Results",
            font=("Arial", 12, "bold"),
            bg=self.bgcolor,
            fg=self.accent_color
        )
        results_label.pack(pady=(15, 5))

        self.results_frame = tk.Frame(self.root, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        self.results_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.results_text = tk.Text(
            self.results_frame,
            height=15,
            width=100,
            wrap="word",
            state="disabled",
            bg=self.header_color,
            fg="#CCCCCC",
            font=("Courier", 9),
            insertbackground=self.accent_color
        )
        self.results_text.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        results_scroll = tk.Scrollbar(
            self.results_frame,
            orient="vertical",
            command=self.results_text.yview,
            bg=self.panel_color,
            activebackground=self.accent_color
        )
        results_scroll.pack(side="right", fill="y")
        self.results_text.config(yscrollcommand=results_scroll.set)

    def log_status(self, message: str):
        """Add message to status display"""
        self.status_text.config(state="normal")
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")
        self.status_text.config(state="disabled")
        self.root.update()

    def start_test(self):
        """Start a click test session"""
        try:
            duration = self.duration_var.get()
            if duration < 1 or duration > 300:
                messagebox.showerror("Error", "Duration must be between 1 and 300 seconds")
                return

            self.session = ClickSession(
                session_name=datetime.now().strftime("%H%M%S"),
                duration_seconds=duration,
                technique=self.technique_var.get()
            )

            self.is_testing = True
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
            self.export_btn.config(state="disabled")

            self.status_text.config(state="normal")
            self.status_text.delete("1.0", "end")
            self.status_text.config(state="disabled")

            self.results_text.config(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.config(state="disabled")

            self.log_status(f"Starting {duration}-second test...")
            self.log_status("Click to start the timer!")
            self.log_status("(Timer begins on your first click)")
            self.log_status("")

            first_click_detected = False

            def on_click(x, y, button, pressed):
                nonlocal first_click_detected
                if pressed and self.is_testing:
                    if not first_click_detected:
                        first_click_detected = True
                        self.session.start_time = time.time()
                        self.root.after(0, self.log_status, "Timer started!")

                    elapsed = time.time() - self.session.start_time

                    if elapsed >= duration:
                        self.is_testing = False
                        self.session.end_time = time.time()
                        self.root.after(0, self.finish_test)
                        return False

                    self.session.add_click(button=str(button).split('.')[-1])

                    if len(self.session.clicks) % 5 == 0 or len(self.session.clicks) <= 1:
                        cps = len(self.session.clicks) / elapsed if elapsed > 0 else 0
                        remaining = duration - elapsed

                        if remaining > 0:
                            status_msg = f"Clicks: {len(self.session.clicks)} | CPS: {cps:.2f} | {remaining:.1f}s remaining"
                        else:
                            status_msg = f"Clicks: {len(self.session.clicks)} | CPS: {cps:.2f} | COMPLETE"

                        self.root.after(0, self.log_status, status_msg)

                    return self.is_testing

                if not pressed and self.is_testing:
                    # Release: close out the hold duration on the open click.
                    self.session.close_click()

            self.listener = mouse.Listener(on_click=on_click)
            self.listener.start()

            def check_test_completion():
                if self.is_testing and self.session.start_time > 0:
                    elapsed = time.time() - self.session.start_time
                    if elapsed >= duration:
                        self.is_testing = False
                        self.session.end_time = time.time()
                        self.finish_test()
                        return

                    if self.is_testing:
                        self.root.after(100, check_test_completion)

            self.root.after(100, check_test_completion)

        except ValueError:
            messagebox.showerror("Error", "Invalid duration")

    def finish_test(self):
        """Finish the test and clean up"""
        if self.listener:
            self.listener.stop()
            self.listener = None

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.export_btn.config(state="normal")

        self.display_results()

    def stop_test(self):
        """Stop the current test"""
        if not self.is_testing or self.session is None:
            return

        self.is_testing = False
        self.session.end_time = time.time()
        self.finish_test()

    def display_results(self):
        """Display test results"""
        if not self.session or not self.session.clicks:
            self.results_text.config(state="normal")
            self.results_text.delete("1.0", "end")
            self.results_text.insert("end", "No clicks recorded!")
            self.results_text.config(state="disabled")
            return

        stats = self.session.get_stats()

        _mark = {"USABLE": "[OK]", "THIN": "[THIN]", "CONTAMINATED": "[BAD]"}
        _verdict = f"{_mark.get(stats.get('verdict'), '[?]')} {stats.get('verdict', 'UNKNOWN')}"
        _warnings = "".join(f"\n  ! {r}\n" for r in stats.get('verdict_reasons', []))
        _truecps = ""
        if stats.get('chatter_detected'):
            _truecps = (f"\nHAND-ONLY CPS (hardware doubles excluded): {stats.get('true_cps')}"
                        f"\n  ^ fit motor models to this; the CPS above is combat output\n")

        results_str = f"""
═════════════════════════════════════════════════

SESSION RESULTS

═════════════════════════════════════════════════

DATA QUALITY: {_verdict}   [technique: {stats.get('technique', 'unlabelled')}]
{_warnings}
Total Clicks: {stats['total_clicks']}

Single-clicks: {stats['single_clicks']}

Double-clicks: {stats['double_clicks']}

Duration: {stats['duration_seconds']}s

CPS (Average): {stats['cps']} clicks/sec
{_truecps}
CLICK TIMING ANALYSIS:

Min Delay: {stats['min_delay_ms']} ms

Max Delay: {stats['max_delay_ms']} ms

Avg Delay: {stats['avg_delay_ms']} ms

Std Deviation: {stats['std_dev_ms']} ms

Consistency: {stats['consistency']}

PERCENTILE ANALYSIS:

P10: {stats['percentiles'].get('p10', 'N/A')} ms

P25: {stats['percentiles'].get('p25', 'N/A')} ms

P50 (Median): {stats['percentiles'].get('p50_median', 'N/A')} ms

P75: {stats['percentiles'].get('p75', 'N/A')} ms

P90: {stats['percentiles'].get('p90', 'N/A')} ms

CLICK INTERVAL DISTRIBUTION:

0-30ms: {stats['interval_distribution'].get('0-30ms', 0)} clicks

30-50ms: {stats['interval_distribution'].get('30-50ms', 0)} clicks

50-100ms: {stats['interval_distribution'].get('50-100ms', 0)} clicks

100-150ms: {stats['interval_distribution'].get('100-150ms', 0)} clicks

150-200ms: {stats['interval_distribution'].get('150-200ms', 0)} clicks

200-300ms: {stats['interval_distribution'].get('200-300ms', 0)} clicks

300ms+: {stats['interval_distribution'].get('300ms+', 0)} clicks

BURST ANALYSIS:

Total Bursts: {stats['burst_info'].get('total_bursts', 0)}

Avg Burst Length: {stats['burst_info'].get('avg_burst_length', 0)} clicks

Longest Burst: {stats['burst_info'].get('fastest_burst_length', 0)} clicks

FATIGUE ANALYSIS (CPS by time segment):

"""

        if stats['fatigue_analysis']:
            for segment in stats['fatigue_analysis']:
                results_str += f" {segment['time_range']:15} {segment['cps']} CPS ({segment['clicks']} clicks)\n"

        results_str += "═════════════════════════════════════════════════"

        self.results_text.config(state="normal")
        self.results_text.delete("1.0", "end")
        self.results_text.insert("end", results_str)
        self.results_text.config(state="disabled")

        self.log_status("\nTest completed! Click 'Export Results' to save files.")

    def export_session(self):
        """Export session to CSV + Stats TXT"""
        if not self.session:
            messagebox.showwarning("No Session", "No session to export")
            return

        try:
            csv_file, stats_file = self.session.export_to_csv()

            if csv_file and stats_file:
                messagebox.showinfo("Success", f"✓ Data exported to:\n{csv_file}\n\n✓ Stats exported to:\n{stats_file}")
                self.log_status(f"Exported CSV: {csv_file}")
                self.log_status(f"Exported STATS: {stats_file}")
            else:
                messagebox.showerror("Export Error", "Failed to export files. Check console for details.")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

def main():
    """Main entry point - GUI only"""
    if not TKINTER_AVAILABLE:
        print("ERROR: tkinter not available on this system")
        print("Please reinstall Python with tkinter support")
        return

    try:
        root = tk.Tk()
        root.withdraw()
        app = ClickTrackerGUI(root)
        root.mainloop()

    except Exception as e:
        print(f"GUI Error: {e}")

if __name__ == "__main__":
    main()
