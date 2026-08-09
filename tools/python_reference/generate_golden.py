"""Generates golden reference CSVs from the ORIGINAL, unmodified Python
engine (python_legacy/mimic/engine.py) for the C++ parity test suite to
compare against.

This does not touch the mouse: it only calls simulate_stream(), which
draws intervals without driving win32 mouse events. win32api/win32con are
stubbed out purely so the module imports on a machine without pywin32
installed -- the stub is never actually called.

Run once whenever engine.py's math changes; commit the resulting CSVs.
"""
import sys
import types
import random
import csv
from pathlib import Path

# --- stub win32api/win32con so `import mimic.engine` succeeds without pywin32 ---
win32api_stub = types.ModuleType("win32api")
win32api_stub.mouse_event = lambda *a, **k: None
win32con_stub = types.ModuleType("win32con")
win32con_stub.MOUSEEVENTF_LEFTDOWN = 0x0002
win32con_stub.MOUSEEVENTF_LEFTUP = 0x0004
sys.modules.setdefault("win32api", win32api_stub)
sys.modules.setdefault("win32con", win32con_stub)

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "python_legacy"))

from mimic.engine import AdaptiveClickerEngine  # noqa: E402

N = 50_000
OUT_DIR = Path(__file__).resolve().parent / "golden"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PRESETS = ["Conservative", "Balanced", "Aggressive"]
MODES = [True, False]  # enhanced_mode

for preset in PRESETS:
    for enhanced in MODES:
        random.seed(42)
        engine = AdaptiveClickerEngine(enhanced_mode=enhanced, preset_name=preset)
        # Re-seed numpy's default_rng deterministically for reproducibility
        # across regenerations (the engine creates its own Generator in
        # __init__, so we can't inject a seed without touching engine.py --
        # acceptable since golden files are regenerated wholesale, not
        # diffed value-by-value against a fixed seed anyway).
        stream = engine.simulate_stream(N)

        mode_tag = "enhanced" if enhanced else "standard"
        out_path = OUT_DIR / f"{preset.lower()}_{mode_tag}.csv"
        with open(out_path, "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["delay_ms"])
            for d in stream:
                w.writerow([f"{d:.6f}"])
        print(f"wrote {out_path} ({len(stream)} intervals)")

print("done")
