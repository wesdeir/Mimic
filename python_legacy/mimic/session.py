"""Session persistence and human click capture.

Part of Mimic. Split out of the original single-file Mimic.py.
"""

import os
import csv
import json
import math
import time
import statistics
from datetime import datetime
from collections import deque

from tkinter import messagebox

from .config import Config, RiskAssessor


# ═════════════════════════════════════════════════════════════════════════════
# SESSION MANAGER - TRACKS ALL TRAINING/CLICKER SESSIONS
# ═════════════════════════════════════════════════════════════════════════════

class SessionManager:
    """Manages session history and persistence"""
    
    def __init__(self):
        self.sessions_file = Config.get_sessions_file()
        self.sessions = self.load_sessions()
    
    def load_sessions(self):
        """Load session history from JSON"""
        try:
            if os.path.exists(self.sessions_file):
                with open(self.sessions_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"training": [], "clicker": []}
        except Exception as e:
            print(f"[WARNING] Could not load sessions: {e}")
            return {"training": [], "clicker": []}
    
    def save_sessions(self):
        """Save session history to JSON"""
        try:
            os.makedirs(os.path.dirname(self.sessions_file), exist_ok=True)
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[ERROR] Could not save sessions: {e}")
            return False
    
    def add_training_session(self, stats, filepath):
        """Add training session to history"""
        session = {
            "timestamp": datetime.now().isoformat(),
            "type": stats.get('training_type', 'unknown'),
            "total_clicks": stats.get('total', 0),
            "avg_cps": stats.get('avg_cps', 0),
            "variance": stats.get('variance', 0),
            "std_dev": stats.get('std_dev', 0),
            "filepath": filepath
        }
        self.sessions["training"].append(session)
        self.save_sessions()
        return session
    
    def add_clicker_session(self, stats, filepath):
        """Add clicker session to history"""
        risk_assessment = RiskAssessor.assess(stats)
        session = {
            "timestamp": datetime.now().isoformat(),
            "mode": "enhanced" if stats.get('enhanced_mode') else "standard",
            "total_clicks": stats.get('total', 0),
            "avg_cps": stats.get('avg_cps', 0),
            "variance": stats.get('variance', 0),
            "std_dev": stats.get('std_dev', 0),
            "risk": risk_assessment['risk'],
            "score": risk_assessment['score'],
            "filepath": filepath
        }
        self.sessions["clicker"].append(session)
        self.save_sessions()
        return session
    
    def get_training_sessions(self, click_type=None):
        """Get training sessions, optionally filtered by type"""
        sessions = self.sessions.get("training", [])
        if click_type:
            return [s for s in sessions if s.get('type') == click_type]
        return sessions
    
    def get_clicker_sessions(self, mode=None):
        """Get clicker sessions, optionally filtered by mode"""
        sessions = self.sessions.get("clicker", [])
        if mode:
            return [s for s in sessions if s.get('mode') == mode]
        return sessions


# HUMAN CLICK TRACKER - WITH SESSION INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════

class HumanClickTracker:
    """Tracks legitimate clicks for baseline analysis"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.is_tracking = False
        self.click_times = []
        self.click_delays = []
        self.session_start = None
        self.last_click_time = None
        self.total_clicks = 0
        self.training_type = "normal"
        
        # Win32 hook variables
        self.hook_id = None
        self.hook_callback = None
    
    def start_tracking(self, training_type="normal"):
        self.is_tracking = True
        self.training_type = training_type
        self.session_start = datetime.now()
        self.click_times = []
        self.click_delays = []
        self.last_click_time = None
        self.total_clicks = 0
        
        self._install_mouse_hook()
        print(f"\n[TRAINING MODE: {training_type.upper()}] Recording with Win32 hook (high-precision)...\n")
    
    def stop_tracking(self):
        self.is_tracking = False
        self._uninstall_mouse_hook()
        print(f"\n[TRAINING MODE: {self.training_type.upper()}] Stopped recording.\n")
    
    def _install_mouse_hook(self):
        """Install low-level mouse hook for precise click tracking"""
        import ctypes
        from ctypes import wintypes
        
        HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
        
        def mouse_hook_proc(nCode, wParam, lParam):
            if nCode >= 0 and self.is_tracking:
                if wParam == 0x0201:  # WM_LBUTTONDOWN
                    self._record_click_precise()
            
            return ctypes.windll.user32.CallNextHookEx(self.hook_id, nCode, wParam, lParam)
        
        self.hook_callback = HOOKPROC(mouse_hook_proc)
        
        self.hook_id = ctypes.windll.user32.SetWindowsHookExA(
            14,  # WH_MOUSE_LL
            self.hook_callback,
            ctypes.windll.kernel32.GetModuleHandleW(None),
            0
        )
        
        if not self.hook_id:
            print("[WARNING] Failed to install mouse hook - falling back to manual tracking")
    
    def _uninstall_mouse_hook(self):
        """Remove mouse hook"""
        if self.hook_id:
            import ctypes
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook_id)
            self.hook_id = None
            self.hook_callback = None
    
    def _record_click_precise(self):
        """High-precision click recording via Win32 hook"""
        current_time = time.perf_counter()
        self.click_times.append(current_time)
        self.total_clicks += 1
        
        if self.last_click_time is not None:
            delay_ms = (current_time - self.last_click_time) * 1000
            # FIX: Lowered to 1ms to capture ultra-fast butterfly clicks
            if 1 <= delay_ms < 2000:
                self.click_delays.append(delay_ms)
        
        self.last_click_time = current_time
    
    def record_click(self):
        """Fallback method if hook fails"""
        if not self.is_tracking:
            return
        current_time = time.perf_counter()
        self.click_times.append(current_time)
        self.total_clicks += 1
        if self.last_click_time is not None:
            delay_ms = (current_time - self.last_click_time) * 1000
            if 1 <= delay_ms < 2000:
                self.click_delays.append(delay_ms)
        self.last_click_time = current_time
    
    def get_rolling_cps(self, window_seconds=1.0):
        """Calculate CPS using rolling window (like Minecraft mods)"""
        if len(self.click_times) < 2:
            return 0.0
        
        # FIX: Use last click time, not current time
        last_click = self.click_times[-1]
        cutoff_time = last_click - window_seconds
        
        recent_clicks = sum(1 for t in self.click_times if t >= cutoff_time)
        
        return recent_clicks / window_seconds
    
    def get_max_rolling_cps(self, window_seconds=1.0):
        """Get peak CPS during session using rolling window"""
        if len(self.click_times) < 10:
            return 0.0
        
        max_cps = 0.0
        
        for i in range(len(self.click_times)):
            timestamp = self.click_times[i]
            cutoff = timestamp - window_seconds
            
            clicks_in_window = sum(1 for t in self.click_times if cutoff <= t <= timestamp)
            cps = clicks_in_window / window_seconds
            max_cps = max(max_cps, cps)
        
        return max_cps
    
    def calculate_variance(self):
        if len(self.click_delays) < 10:
            return 0
        mean = sum(self.click_delays) / len(self.click_delays)
        return sum((x - mean) ** 2 for x in self.click_delays) / len(self.click_delays)
    
    def get_stats(self):
        """Generate statistics for training session"""
        if len(self.click_delays) < 10:
            return None
        
        delays = self.click_delays
        avg_delay = sum(delays) / len(delays)
        sorted_delays = sorted(delays)
        p10 = sorted_delays[int(len(sorted_delays) * 0.10)]
        p50 = sorted_delays[int(len(sorted_delays) * 0.50)]
        p90 = sorted_delays[int(len(sorted_delays) * 0.90)]
        session_duration = (datetime.now() - self.session_start).total_seconds()
        
        capture_rate = len(delays) / self.total_clicks if self.total_clicks > 0 else 0
        
        # Calculate rolling window CPS
        max_rolling_cps = self.get_max_rolling_cps(1.0)
        
        # FIX: Calculate average CPS from total clicks and time, not from delays
        avg_cps = len(self.click_times) / session_duration if session_duration > 0 else 0
        
        return {
            "total": self.total_clicks,
            "valid_delays": len(delays),
            "capture_rate": capture_rate,
            "avg_cps": avg_cps,  # FIXED: Now uses total clicks / time
            "min_cps": 1000.0 / max(delays),
            "max_cps": 1000.0 / min(delays),
            "median_cps": 1000.0 / p50,
            "peak_cps": max_rolling_cps,
            "variance": self.calculate_variance(),
            "std_dev": math.sqrt(self.calculate_variance()),
            "session_duration": session_duration,
            "p10_delay": p10,
            "p50_delay": p50,
            "p90_delay": p90,
            "min_delay": min(delays),
            "max_delay": max(delays),
            "avg_delay": avg_delay,
            "training_type": self.training_type
        }
    
    def export_to_csv(self, filename):
        """Export training data to CSV with UTF-8 encoding"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Click_Number', 'Delay_MS', 'CPS', 'Training_Type'])
                
                for i, delay in enumerate(self.click_delays, 1):
                    cps = 1000.0 / delay if delay > 0 else 0
                    writer.writerow([i, f"{delay:.2f}", f"{cps:.2f}", self.training_type])
            
            return True
        except Exception as e:
            print(f"[ERROR] CSV export failed: {e}")
            return False
    
    def export_human_stats(self):
        """Export complete human clicking statistics with session tracking"""
        stats = self.get_stats()
        
        if not stats:
            print(f"\n[!] Not enough data. Need at least 10 clicks! (Current: {self.total_clicks})\n")
            messagebox.showwarning("Insufficient Data", f"Need at least 10 valid clicks!\n\nCurrent clicks: {self.total_clicks}")
            return
        
        if stats['capture_rate'] < 0.95:
            capture_pct = stats['capture_rate'] * 100
            missed_clicks = stats['total'] - stats['valid_delays']
            print(f"[WARNING] Capture rate: {capture_pct:.1f}% ({missed_clicks} clicks missed/filtered)\n")
        
        training_type = stats['training_type'].upper()
        # So tedious :(
        report = f""" 
══════════════════════════════════════════════════════════════════════════════
MIMIC - HUMAN CLICK ANALYSIS - {training_type} CLICKING PATTERN
══════════════════════════════════════════════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Training Mode: {training_type}
Click Type: {"Butterfly (2 fingers alternating)" if stats['training_type'] == 'butterfly' else "Jitter (rapid wrist/arm)" if stats['training_type'] == 'jitter' else "Normal (single finger)" if stats['training_type'] == 'normal' else "Mixed Techniques"}


SESSION OVERVIEW
──────────────────────────────────────────────────────────────────────────────
Total Clicks Recorded:     {stats['total']}
Valid Click Intervals:     {stats['valid_delays']}
Capture Rate:              {stats['capture_rate']*100:.1f}%
Session Duration:          {stats['session_duration']:.1f} seconds


Peak CPS (1s window):      {stats['peak_cps']:.2f}  
Session Average CPS:       {stats['avg_cps']:.2f}
Median CPS:                {stats['median_cps']:.2f}


CPS STATISTICS
──────────────────────────────────────────────────────────────────────────────
Peak 1-Second CPS:         {stats['peak_cps']:.2f}
Session Average CPS:       {stats['avg_cps']:.2f}
Median CPS:                {stats['median_cps']:.2f}
Minimum CPS:               {stats['min_cps']:.2f}
Maximum CPS (instant):     {stats['max_cps']:.2f}
CPS Range:                 {stats['min_cps']:.2f} - {stats['max_cps']:.2f}


DELAY STATISTICS (milliseconds)
──────────────────────────────────────────────────────────────────────────────
Average Delay:             {stats['avg_delay']:.2f} ms
Median Delay (P50):        {stats['p50_delay']:.2f} ms
10th Percentile (P10):     {stats['p10_delay']:.2f} ms
90th Percentile (P90):     {stats['p90_delay']:.2f} ms
Min Delay:                 {stats['min_delay']:.2f} ms
Max Delay:                 {stats['max_delay']:.2f} ms


HUMAN BEHAVIOR METRICS
──────────────────────────────────────────────────────────────────────────────
Variance:                  {stats['variance']:.0f}
Standard Deviation:        {stats['std_dev']:.2f}
Consistency:               {'High' if stats['variance'] < 200 else 'Moderate' if stats['variance'] < 400 else 'Variable' if stats['variance'] < 1500 else 'Highly Variable'}


══════════════════════════════════════════════════════════════════════════════
CLICK TYPE CHARACTERISTICS - {training_type}
══════════════════════════════════════════════════════════════════════════════
"""
        
        if stats['training_type'] == 'butterfly':
            report += """
BUTTERFLY CLICKING PATTERN:
- Expected: High CPS (10-20+), very high variance (1,800-3,500)
- Two-finger alternating technique
- Common variance: 1,800-3,500
- Burst patterns with occasional pauses
"""
        elif stats['training_type'] == 'jitter':
            report += """
JITTER CLICKING PATTERN:
- Expected: Moderate-High CPS (8-14), moderate variance (800-1,800)
- Rapid wrist/arm tension technique
- More consistent than butterfly
- Sustained clicking without bursts
"""
        elif stats['training_type'] == 'normal':
            report += """
NORMAL CLICKING PATTERN:
- Expected: Lower CPS (5-9), low-moderate variance (400-900)
- Single finger tapping
- Most consistent pattern
- Natural rhythm with occasional variation
"""
        else:
            report += """
MIXED CLICKING PATTERN:
- Combination of multiple techniques
- Varied CPS and variance depending on switching
- Adaptive clicking style
"""
        
        report += f"""


YOUR {training_type} PATTERN ANALYSIS:
──────────────────────────────────────────────────────────────────────────────
Your Peak CPS (1s):        {stats['peak_cps']:.2f}
Your Average CPS:          {stats['avg_cps']:.2f}
Your Variance:             {stats['variance']:.0f}
Your Std Deviation:        {stats['std_dev']:.2f}
Pattern Consistency:       {'Very Consistent' if stats['variance'] < 300 else 'Moderate' if stats['variance'] < 1000 else 'Highly Variable'}


RECOMMENDATION FOR MIMIC:
──────────────────────────────────────────────────────────────────────────────
"""
        
        if stats['variance'] > 2000:
            report += "✅ Use Enhanced Mode - Your variance matches butterfly clicking\n"
        elif stats['variance'] > 800:
            report += "✅ Use Enhanced Mode - Good for jitter-style clicking\n"
        else:
            report += "⚠️  Your variance is low for this technique - May need more practice\n"
        
        report += """
══════════════════════════════════════════════════════════════════════════════
FILE SAVED TO DESKTOP
══════════════════════════════════════════════════════════════════════════════
"""
        
        print(report)
        
        training_type_safe = stats['training_type'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_filename = f"{training_type_safe}_baseline_{timestamp}.txt"
        csv_filename = f"{training_type_safe}_baseline_{timestamp}.csv"
        
        folder_path = os.path.join(Config.get_training_data_path(), training_type_safe)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            
            txt_full_path = os.path.join(folder_path, txt_filename)
            with open(txt_full_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"[SUCCESS] TXT report saved to: {txt_full_path}\n")
            
            csv_full_path = os.path.join(folder_path, csv_filename)
            self.export_to_csv(csv_full_path)
            print(f"[SUCCESS] CSV data saved to: {csv_full_path}\n")
            
            self.session_manager.add_training_session(stats, txt_full_path)
            
            messagebox.showinfo("Export Successful", f"Training data exported!\n\n📁 {folder_path}")
        
        except Exception as e:
            print(f"[ERROR] Export failed: {e}\n")
            messagebox.showerror("Export Failed", f"Could not save files:\n{e}")
