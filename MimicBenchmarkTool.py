"""

MIMIC Clicking Benchmark - CPS Test Tool

Tracks individual clicks, calculates CPS, and exports detailed analytics to CSV + TXT

GUI-only interface, integrated with MIMIC

Tracks ALL clicks including double-clicks

Timer starts on first click

Enhanced with fatigue analysis, click intervals, and burst detection

Auto-generates readable filenames and summary stats files

Auto-saves to Desktop/click_data/ folder with proper permission handling

"""

import csv
import time
import os
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, field
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

    def to_dict(self):
        return {
            'click_number': self.click_number,
            'timestamp': self.timestamp,
            'delay_ms': round(self.delay_ms, 3),
            'button': self.button
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

        return {
            'total_clicks': len(self.clicks),
            'single_clicks': single_clicks,
            'double_clicks': double_clicks,
            'duration_seconds': round(self.end_time - self.start_time, 3),
            'cps': round(self.get_cps(), 2),
            'min_delay_ms': round(min(delays), 3) if delays else 0,
            'max_delay_ms': round(max(delays), 3) if delays else 0,
            'avg_delay_ms': round(statistics.mean(delays), 3) if delays else 0,
            'std_dev_ms': round(statistics.stdev(delays), 3) if len(delays) > 1 else 0,
            'consistency': self._calculate_consistency(delays),
            'fatigue_analysis': fatigue_analysis,
            'interval_distribution': interval_distribution,
            'percentiles': percentiles,
            'burst_info': burst_info
        }

    def _export_stats_to_txt(self, stats: dict, filename: str):
        """Export detailed statistics to text file"""
        base, _ = os.path.splitext(filename)
        stats_filename = f"{base}_STATS.txt"

        stats_content = f"""
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

        fieldnames = ['click_number', 'timestamp', 'relative_time_ms', 'delay_ms', 'button', 'click_type']

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
                duration_seconds=duration
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

        results_str = f"""
═════════════════════════════════════════════════

SESSION RESULTS

═════════════════════════════════════════════════

Total Clicks: {stats['total_clicks']}

Single-clicks: {stats['single_clicks']}

Double-clicks: {stats['double_clicks']}

Duration: {stats['duration_seconds']}s

CPS (Average): {stats['cps']} clicks/sec

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