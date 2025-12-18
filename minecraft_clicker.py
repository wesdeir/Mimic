"""
═══════════════════════════════════════════════════════════════════════════════
MINECRAFT AUTO CLICKER - ANTI-CHEAT COMPLIANT
═══════════════════════════════════════════════════════════════════════════════
Version: 3.1 - Multi-Page Interface with Histogram Visualization
Target: 7-12 CPS range with human-like variance
Features:
  - 4-Page tabbed interface with keyboard/mouse navigation
  - Live dashboard with real-time statistics
  - Advanced settings and configuration page
  - Analytics page with session history
  - NEW: Histogram visualization of click delay distribution
  - Professional dark theme UI
  
Navigation:
  - Arrow Keys (← →): Switch pages
  - Enter: Toggle activation
  - Escape: Quick disable
  - F5: Export stats (any page)
  - F7: Training mode toggle
  - F8: Export human baseline
  
Requirements:
  - Python 3.x
  - keyboard library (pip install keyboard)
  - pywin32 library (pip install pywin32)
  - Administrator privileges
═══════════════════════════════════════════════════════════════════════════════
"""

import time
import random
import math
from datetime import datetime
import keyboard
import threading
from collections import deque, Counter
import tkinter as tk
from tkinter import ttk

import win32api
import win32con

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    """Global configuration constants for the auto clicker"""
    
    # CPS Limits (milliseconds between clicks)
    ABSOLUTE_MIN_DELAY_MS = 84   # 11.9 CPS maximum
    ABSOLUTE_MAX_DELAY_MS = 143  # 7.0 CPS minimum
    
    # Enhanced Chaos Mode Limits
    ENHANCED_MIN_DELAY_MS = 50   # 20 CPS burst maximum
    ENHANCED_MAX_DELAY_MS = 400  # Longer pauses for recovery
    
    # Anti-Detection Thresholds
    MIN_VARIANCE_THRESHOLD = 120
    PATTERN_CHECK_WINDOW = 20
    
    # Enhanced Mode Parameters
    BURST_PROBABILITY = 0.15
    PAUSE_PROBABILITY = 0.08
    BURST_DURATION = (3, 8)
    PAUSE_DURATION_MS = (250, 450)
    
    # Mouse Button Constants
    VK_XBUTTON2 = 0x06  # MB5
    VK_LBUTTON = 0x01   # Left mouse button


# ═════════════════════════════════════════════════════════════════════════════
# CLICKER ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class ClickerEngine:
    """Core clicking engine with advanced anti-detection algorithms"""
    
    def __init__(self, enhanced_mode=False):
        """Initialize the clicker engine"""
        self.enhanced_mode = enhanced_mode
        self.total_clicks = 0
        self.session_start = datetime.now()
        self.combat_start = None
        self.click_history = deque(maxlen=50)
        self.recent_click_times = deque(maxlen=20)
        self.all_delays = []
        self.user_baseline = random.uniform(0.88, 1.12)
        self.rhythm_phase = 0.0
        self.drift = 0.0
        self.consecutive_clicks = 0
        self.variance_adjustment = 0.15
        self.last_variance_check = datetime.now()
        self.pattern_breaks = 0
        self.variance_adjustments = 0
        self.in_burst_mode = False
        self.burst_clicks_remaining = 0
        self.pause_until = None
        self.burst_count = 0
        self.pause_count = 0
        self.total_clicking_time = 0.0
        self.click_session_start = None
        self.is_actively_clicking = False
    
    def start_clicking(self):
        if not self.is_actively_clicking:
            self.is_actively_clicking = True
            self.click_session_start = time.time()
    
    def stop_clicking(self):
        if self.is_actively_clicking and self.click_session_start:
            self.is_actively_clicking = False
            elapsed = time.time() - self.click_session_start
            self.total_clicking_time += elapsed
            self.click_session_start = None
            self.in_burst_mode = False
            self.burst_clicks_remaining = 0
            self.pause_until = None
    
    def get_active_clicking_time(self):
        total = self.total_clicking_time
        if self.is_actively_clicking and self.click_session_start:
            total += time.time() - self.click_session_start
        return total
    
    def gaussian_random(self, mean, std_dev):
        u1, u2 = random.random(), random.random()
        rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)
        return mean + std_dev * rand_std_normal
    
    def weibull_random(self, scale, shape):
        u = random.random()
        return scale * ((-math.log(1 - u)) ** (1 / shape))
    
    def check_cps(self):
        current_time = time.time()
        while self.recent_click_times and current_time - self.recent_click_times[0] > 1.0:
            self.recent_click_times.popleft()
        if len(self.recent_click_times) >= 2:
            time_span = current_time - self.recent_click_times[0]
            recent_cps = len(self.recent_click_times) / time_span if time_span > 0 else 0
            if recent_cps >= 11:
                return 0.06
        return 0
    
    def calculate_variance(self):
        if len(self.click_history) < 10:
            return 200
        if self.enhanced_mode:
            recent = list(self.click_history)
        else:
            recent = list(self.click_history)[-30:] if len(self.click_history) >= 30 else list(self.click_history)
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        return variance
    
    def calculate_overall_variance(self):
        if len(self.all_delays) < 20:
            return 200
        mean = sum(self.all_delays) / len(self.all_delays)
        variance = sum((x - mean) ** 2 for x in self.all_delays) / len(self.all_delays)
        return variance
    
    def calculate_std_dev(self):
        """Calculate standard deviation"""
        variance = self.calculate_overall_variance()
        return math.sqrt(variance)
    
    def check_variance(self):
        if (datetime.now() - self.last_variance_check).total_seconds() < 10:
            return
        if self.enhanced_mode and len(self.all_delays) >= 50:
            variance = self.calculate_overall_variance()
        elif len(self.click_history) >= 15:
            variance = self.calculate_variance()
        else:
            return
        target_low = 800 if self.enhanced_mode else 150
        target_mid = 1500 if self.enhanced_mode else 200
        target_high = 2500 if self.enhanced_mode else 250
        if variance < target_low:
            self.variance_adjustment = random.uniform(0.35, 0.50) if self.enhanced_mode else random.uniform(0.25, 0.40)
            self.variance_adjustments += 1
        elif variance < target_mid:
            self.variance_adjustment = random.uniform(0.25, 0.40) if self.enhanced_mode else random.uniform(0.15, 0.30)
            self.variance_adjustments += 1
        elif variance < target_high:
            self.variance_adjustment = random.uniform(0.15, 0.28) if self.enhanced_mode else random.uniform(0.08, 0.18)
            self.variance_adjustments += 1
        else:
            self.variance_adjustment *= 0.85
        self.last_variance_check = datetime.now()
    
    def trigger_burst_mode(self):
        if not self.in_burst_mode and self.consecutive_clicks > 5:
            if random.random() < Config.BURST_PROBABILITY:
                self.in_burst_mode = True
                self.burst_clicks_remaining = random.randint(*Config.BURST_DURATION)
                self.burst_count += 1
                return True
        return False
    
    def trigger_pause_mode(self):
        if not self.in_burst_mode and self.consecutive_clicks > 10:
            if random.random() < Config.PAUSE_PROBABILITY:
                pause_duration = random.uniform(*Config.PAUSE_DURATION_MS) / 1000.0
                self.pause_until = time.time() + pause_duration
                self.pause_count += 1
                return True
        return False
    
    def calculate_delay(self):
        if self.enhanced_mode:
            if self.pause_until and time.time() < self.pause_until:
                remaining = (self.pause_until - time.time()) * 1000
                self.pause_until = None
                return max(Config.ENHANCED_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, remaining))
            if self.trigger_pause_mode():
                return random.uniform(*Config.PAUSE_DURATION_MS)
            if not self.in_burst_mode:
                self.trigger_burst_mode()
        
        if self.enhanced_mode and self.in_burst_mode:
            self.burst_clicks_remaining -= 1
            if self.burst_clicks_remaining <= 0:
                self.in_burst_mode = False
            base = abs(self.gaussian_random(55, 12))
            base *= random.uniform(0.85, 1.15)
            final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(110, base))
            self.click_history.append(final)
            self.all_delays.append(final)
            return final
        
        if self.enhanced_mode:
            if random.random() < 0.7:
                base = abs(self.gaussian_random(100, 30))
            else:
                base = self.weibull_random(95, 2.0)
        else:
            if random.random() < 0.7:
                base = abs(self.gaussian_random(108, 24))
            else:
                base = self.weibull_random(100, 2.2)
        
        base *= self.user_baseline
        
        if self.enhanced_mode:
            base *= random.uniform(0.75, 1.25)
        else:
            base *= random.uniform(0.80, 1.20)
        
        if self.consecutive_clicks < 3:
            base *= random.uniform(1.05, 1.20)
        elif self.consecutive_clicks < 8:
            base *= random.uniform(0.92, 1.08)
        else:
            base *= random.uniform(0.88, 0.98)
        
        drift_amount = 0.008 if self.enhanced_mode else 0.005
        self.drift += random.uniform(-drift_amount, drift_amount)
        drift_limit = 0.35 if self.enhanced_mode else 0.25
        self.drift = max(-drift_limit, min(drift_limit, self.drift))
        base *= (1.0 + self.drift)
        
        self.rhythm_phase = (self.rhythm_phase + random.uniform(0.20, 0.60)) % (2 * math.pi)
        rhythm_amount = 22 if self.enhanced_mode else 18
        base += math.sin(self.rhythm_phase) * rhythm_amount
        
        base *= (1.0 + self.variance_adjustment)
        
        noise_range = 28 if self.enhanced_mode else 22
        base += random.randint(-noise_range, noise_range + 1)
        
        if self.enhanced_mode:
            final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, base))
        else:
            final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, base))
        
        if len(self.click_history) >= Config.PATTERN_CHECK_WINDOW:
            recent = list(self.click_history)[-Config.PATTERN_CHECK_WINDOW:]
            mean = sum(recent) / len(recent)
            variance = sum((x - mean) ** 2 for x in recent) / len(recent)
            threshold = 250 if self.enhanced_mode else 180
            multiplier_range = (0.60, 1.40) if self.enhanced_mode else (0.65, 1.35)
            if variance < threshold:
                final *= random.uniform(*multiplier_range)
                if self.enhanced_mode:
                    final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, final))
                else:
                    final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, final))
                self.pattern_breaks += 1
        
        self.click_history.append(final)
        self.all_delays.append(final)
        return final
    
    def click(self):
        if self.combat_start is None:
            self.combat_start = datetime.now()
        safety = self.check_cps()
        if safety > 0:
            time.sleep(safety)
        self.check_variance()
        delay_ms = self.calculate_delay()
        pressure_ms = abs(self.gaussian_random(26, 8))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(pressure_ms / 1000.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        self.recent_click_times.append(time.time())
        self.total_clicks += 1
        self.consecutive_clicks += 1
        time.sleep(delay_ms / 1000.0)
    
    def get_current_cps(self):
        if len(self.click_history) < 5:
            return 0.0
        recent = list(self.click_history)[-10:]
        avg_delay = sum(recent) / len(recent)
        return 1000.0 / avg_delay
    
    def get_detailed_stats(self):
        if not self.all_delays:
            return None
        delays = self.all_delays
        avg_delay = sum(delays) / len(delays)
        sorted_delays = sorted(delays)
        p10 = sorted_delays[int(len(sorted_delays) * 0.10)]
        p50 = sorted_delays[int(len(sorted_delays) * 0.50)]
        p90 = sorted_delays[int(len(sorted_delays) * 0.90)]
        session_duration = (datetime.now() - self.session_start).total_seconds()
        clicking_duration = self.get_active_clicking_time()
        overall_variance = self.calculate_overall_variance()
        return {
            "total": self.total_clicks,
            "avg_cps": 1000.0 / avg_delay,
            "min_cps": 1000.0 / max(delays),
            "max_cps": 1000.0 / min(delays),
            "median_cps": 1000.0 / p50,
            "variance": overall_variance,
            "pattern_breaks": self.pattern_breaks,
            "variance_adjustments": self.variance_adjustments,
            "burst_count": self.burst_count,
            "pause_count": self.pause_count,
            "session_duration": session_duration,
            "clicking_duration": clicking_duration,
            "idle_time": session_duration - clicking_duration,
            "p10_delay": p10,
            "p50_delay": p50,
            "p90_delay": p90,
            "min_delay": min(delays),
            "max_delay": max(delays),
            "avg_delay": avg_delay,
            "enhanced_mode": self.enhanced_mode
        }


# ═════════════════════════════════════════════════════════════════════════════
# HUMAN CLICK TRACKER
# ═════════════════════════════════════════════════════════════════════════════

class HumanClickTracker:
    """Tracks legitimate human clicks for baseline analysis"""
    
    def __init__(self):
        self.is_tracking = False
        self.click_times = []
        self.click_delays = []
        self.session_start = None
        self.last_click_time = None
        self.total_clicks = 0
    
    def start_tracking(self):
        self.is_tracking = True
        self.session_start = datetime.now()
        self.click_times = []
        self.click_delays = []
        self.last_click_time = None
        self.total_clicks = 0
        print("\n[TRAINING MODE] Recording your clicks...\n")
    
    def stop_tracking(self):
        self.is_tracking = False
        print("\n[TRAINING MODE] Stopped recording.\n")
    
    def record_click(self):
        if not self.is_tracking:
            return
        current_time = time.time()
        self.click_times.append(current_time)
        self.total_clicks += 1
        if self.last_click_time is not None:
            delay_ms = (current_time - self.last_click_time) * 1000
            if delay_ms < 500:
                self.click_delays.append(delay_ms)
        self.last_click_time = current_time


# ═════════════════════════════════════════════════════════════════════════════
# HISTOGRAM VISUALIZER
# ═════════════════════════════════════════════════════════════════════════════

class HistogramCanvas(tk.Canvas):
    """Custom histogram visualization for click delay distribution"""
    
    def __init__(self, parent, width=460, height=300, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.padding = 40
        self.chart_width = width - 2 * self.padding
        self.chart_height = height - 2 * self.padding
        
        # Colors
        self.grid_color = "#333333"
        self.text_color = "#888888"
        self.mean_color = "#4CAF50"
        self.std_color = "#FFA500"
        self.bar_optimal = "#4CAF50"
        self.bar_acceptable = "#FFA500"
        self.bar_risky = "#f44336"
        
    def draw_histogram(self, delays, mean, std_dev, enhanced_mode=False):
        """Draw histogram with statistical markers"""
        self.delete("all")
        
        if not delays or len(delays) < 5:
            self.create_text(
                self.width // 2, self.height // 2,
                text="Not enough data\n(need 5+ clicks)",
                fill=self.text_color,
                font=("Arial", 11),
                justify=tk.CENTER
            )
            return
        
        # Create bins (20ms buckets)
        min_delay = 50 if enhanced_mode else 80
        max_delay = 420 if enhanced_mode else 150
        bin_width = 20
        num_bins = int((max_delay - min_delay) / bin_width) + 1
        
        # Count delays in each bin
        bins = [0] * num_bins
        for delay in delays:
            if min_delay <= delay <= max_delay:
                bin_idx = int((delay - min_delay) / bin_width)
                if 0 <= bin_idx < num_bins:
                    bins[bin_idx] += 1
        
        max_count = max(bins) if max(bins) > 0 else 1
        
        # Draw grid lines
        for i in range(5):
            y = self.padding + (i * self.chart_height // 4)
            self.create_line(
                self.padding, y,
                self.padding + self.chart_width, y,
                fill=self.grid_color,
                dash=(2, 2)
            )
        
        # Draw histogram bars
        bar_width = self.chart_width / num_bins
        for i, count in enumerate(bins):
            if count == 0:
                continue
            
            x1 = self.padding + i * bar_width
            bar_height = (count / max_count) * self.chart_height
            y1 = self.padding + self.chart_height - bar_height
            x2 = x1 + bar_width - 2
            y2 = self.padding + self.chart_height
            
            # Determine bar color based on delay range
            delay_value = min_delay + i * bin_width
            if 84 <= delay_value <= 143:
                color = self.bar_optimal
            elif (enhanced_mode and 50 <= delay_value <= 400) or (not enhanced_mode and 70 <= delay_value <= 160):
                color = self.bar_acceptable
            else:
                color = self.bar_risky
            
            self.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline=""
            )
        
        # Draw mean line
        mean_x = self.padding + ((mean - min_delay) / (max_delay - min_delay)) * self.chart_width
        if self.padding <= mean_x <= self.padding + self.chart_width:
            self.create_line(
                mean_x, self.padding,
                mean_x, self.padding + self.chart_height,
                fill=self.mean_color,
                width=2
            )
            self.create_text(
                mean_x, self.padding - 10,
                text=f"μ={mean:.0f}ms",
                fill=self.mean_color,
                font=("Arial", 8, "bold")
            )
        
        # Draw standard deviation bands
        std_left = self.padding + ((mean - std_dev - min_delay) / (max_delay - min_delay)) * self.chart_width
        std_right = self.padding + ((mean + std_dev - min_delay) / (max_delay - min_delay)) * self.chart_width
        
        if self.padding <= std_left <= self.padding + self.chart_width:
            self.create_line(
                std_left, self.padding,
                std_left, self.padding + self.chart_height,
                fill=self.std_color,
                width=1,
                dash=(4, 4)
            )
        
        if self.padding <= std_right <= self.padding + self.chart_width:
            self.create_line(
                std_right, self.padding,
                std_right, self.padding + self.chart_height,
                fill=self.std_color,
                width=1,
                dash=(4, 4)
            )
        
        # Draw axes
        self.create_line(
            self.padding, self.padding + self.chart_height,
            self.padding + self.chart_width, self.padding + self.chart_height,
            fill=self.text_color,
            width=2
        )
        
        # X-axis labels
        for i in range(0, num_bins + 1, max(1, num_bins // 5)):
            x = self.padding + i * bar_width
            delay_label = min_delay + i * bin_width
            self.create_text(
                x, self.padding + self.chart_height + 15,
                text=f"{delay_label}",
                fill=self.text_color,
                font=("Arial", 7)
            )
        
        # Axis titles
        self.create_text(
            self.width // 2, self.height - 10,
            text="Delay (ms)",
            fill=self.text_color,
            font=("Arial", 8, "bold")
        )
        
        self.create_text(
            10, self.height // 2,
            text="Count",
            fill=self.text_color,
            font=("Arial", 8, "bold"),
            angle=90
        )


# ═════════════════════════════════════════════════════════════════════════════
# MULTI-PAGE GUI APPLICATION
# ═════════════════════════════════════════════════════════════════════════════

class AutoClickerGUI:
    """Multi-page graphical user interface with histogram visualization"""
    
    def __init__(self):
        """Initialize the multi-page GUI"""
        
        # Main Window Setup
        self.root = tk.Tk()
        self.root.title("Minecraft Auto Clicker v3.1")
        self.root.geometry("500x800")
        self.root.resizable(False, False)
        
        # Dark Theme Colors
        self.bg_color = "#1e1e1e"
        self.fg_color = "#ffffff"
        self.accent_color = "#4CAF50"
        self.inactive_color = "#f44336"
        self.training_color = "#FFA500"
        self.enhanced_color = "#9C27B0"
        self.panel_color = "#2d2d2d"
        self.header_color = "#252525"
        self.button_color = "#3d3d3d"
        self.button_hover = "#4d4d4d"
        self.active_tab = "#4CAF50"
        self.inactive_tab = "#3d3d3d"
        
        self.root.configure(bg=self.bg_color)
        
        # Application State
        self.active = False
        self.clicking = False
        self.engine = None
        self.running = True
        self.last_session_stats = None
        self.human_tracker = HumanClickTracker()
        self.enhanced_mode = False
        self.session_history = []
        
        # Page Management
        self.current_page = 0
        self.pages = []
        
        # Build UI and Start Systems
        self.setup_ui()
        self.setup_hotkeys()
        self.start_threads()
        self.update_display()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    
    def setup_ui(self):
        """Build the complete multi-page interface"""
        
        # HEADER (Fixed across all pages)
        header_frame = tk.Frame(self.root, bg=self.header_color, height=100)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="⚔️ Minecraft Auto Clicker",
            font=("Arial", 18, "bold"),
            bg=self.header_color,
            fg=self.fg_color
        )
        title.pack(pady=(12, 2))
        
        subtitle = tk.Label(
            header_frame,
            text="Anti-Cheat Compliant • 7-12 CPS",
            font=("Arial", 9),
            bg=self.header_color,
            fg="#888888"
        )
        subtitle.pack()
        
        self.mode_indicator = tk.Label(
            header_frame,
            text="Standard Mode",
            font=("Arial", 8, "italic"),
            bg=self.header_color,
            fg="#888888"
        )
        self.mode_indicator.pack(pady=(3, 0))
        
        self.status_indicator = tk.Label(
            header_frame,
            text="● INACTIVE",
            font=("Arial", 10, "bold"),
            bg=self.header_color,
            fg=self.inactive_color
        )
        self.status_indicator.pack(pady=(5, 0))
        
        # TAB NAVIGATION
        tab_frame = tk.Frame(self.root, bg=self.bg_color)
        tab_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.tab_buttons = []
        tab_names = ["Dashboard", "Settings", "Analytics", "Histogram"]
        
        for i, name in enumerate(tab_names):
            btn = tk.Button(
                tab_frame,
                text=name,
                font=("Arial", 9, "bold"),
                bg=self.inactive_tab,
                fg=self.fg_color,
                activebackground=self.button_hover,
                activeforeground=self.fg_color,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda idx=i: self.switch_page(idx)
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
            self.tab_buttons.append(btn)
        
        # CONTENT CONTAINER
        self.content_frame = tk.Frame(self.root, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # Create all pages
        self.create_page_dashboard()
        self.create_page_settings()
        self.create_page_analytics()
        self.create_page_histogram()
        
        # NAVIGATION FOOTER
        nav_frame = tk.Frame(self.root, bg=self.bg_color)
        nav_frame.pack(fill=tk.X, padx=20, pady=15)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="◀ Prev",
            font=("Arial", 10, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.prev_page,
            width=10
        )
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.page_indicator = tk.Label(
            nav_frame,
            text="1 / 4",
            font=("Arial", 10, "bold"),
            bg=self.bg_color,
            fg="#888888"
        )
        self.page_indicator.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ▶",
            font=("Arial", 10, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.next_page,
            width=10
        )
        self.next_btn.pack(side=tk.RIGHT, padx=5)
        
        # Show first page
        self.switch_page(0)
    
    
    def create_page_dashboard(self):
        """Create Page 1: Dashboard with live statistics"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Status panel
        status_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        status_panel.pack(fill=tk.X, pady=(0, 10))
        
        self.click_status = tk.Label(
            status_panel,
            text="Ready to activate",
            font=("Arial", 11),
            bg=self.panel_color,
            fg="#888888"
        )
        self.click_status.pack(pady=15)
        
        # Live statistics
        stats_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        stats_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tk.Label(
            stats_panel,
            text="Live Statistics",
            font=("Arial", 13, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        stats_grid = tk.Frame(stats_panel, bg=self.panel_color)
        stats_grid.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Create stat rows
        self.create_stat_row(stats_grid, "Total Clicks", "total_clicks", 0)
        self.create_stat_row(stats_grid, "Current CPS", "current_cps", 1)
        self.create_stat_row(stats_grid, "Variance", "variance", 2)
        self.create_stat_row(stats_grid, "Session Avg", "session_cps", 3)
        self.create_stat_row(stats_grid, "Time Elapsed", "time_elapsed", 4)
        
        tk.Label(stats_panel, text="", bg=self.panel_color).pack(pady=5)
        
        # Quick actions
        actions_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        actions_panel.pack(fill=tk.X)
        
        tk.Label(
            actions_panel,
            text="Quick Actions",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        btn_frame = tk.Frame(actions_panel, bg=self.panel_color)
        btn_frame.pack(pady=10)
        
        self.toggle_btn = tk.Button(
            btn_frame,
            text="Activate (F4)",
            font=("Arial", 10, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#45a049",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_active,
            width=15
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            btn_frame,
            text="Export Stats (F5)",
            font=("Arial", 10),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_stats,
            width=15
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(actions_panel, text="", bg=self.panel_color).pack(pady=5)
    
    
    def create_page_settings(self):
        """Create Page 2: Settings and configuration"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Mode settings
        mode_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        mode_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            mode_panel,
            text="Clicking Mode",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        enhanced_frame = tk.Frame(mode_panel, bg=self.panel_color)
        enhanced_frame.pack(pady=10)
        
        self.enhanced_btn = tk.Button(
            enhanced_frame,
            text="⚡ Enhanced Chaos Mode (F9)",
            font=("Arial", 10, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_enhanced_mode,
            width=30
        )
        self.enhanced_btn.pack(pady=5)
        
        self.enhanced_status = tk.Label(
            enhanced_frame,
            text="Status: Disabled",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#888888"
        )
        self.enhanced_status.pack(pady=5)
        
        desc_text = "Enhanced mode adds burst/pause mechanics\nfor butterfly clicking simulation (1,500-2,500 variance)"
        tk.Label(
            mode_panel,
            text=desc_text,
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888",
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # Training mode
        training_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        training_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            training_panel,
            text="Human Baseline Training",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        training_btn_frame = tk.Frame(training_panel, bg=self.panel_color)
        training_btn_frame.pack(pady=10)
        
        train_btn = tk.Button(
            training_btn_frame,
            text="Start Training (F7)",
            font=("Arial", 10),
            bg=self.training_color,
            fg="white",
            activebackground="#ff9500",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_training_mode,
            width=18
        )
        train_btn.pack(side=tk.LEFT, padx=5)
        
        export_train_btn = tk.Button(
            training_btn_frame,
            text="Export Baseline (F8)",
            font=("Arial", 10),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_human_baseline,
            width=18
        )
        export_train_btn.pack(side=tk.LEFT, padx=5)
        
        train_desc = "Record your natural clicking to analyze variance\nand get personalized recommendations"
        tk.Label(
            training_panel,
            text=train_desc,
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888",
            justify=tk.CENTER
        ).pack(pady=(0, 15))
        
        # Controls reference
        controls_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        controls_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            controls_panel,
            text="Keyboard Controls",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        controls_grid = tk.Frame(controls_panel, bg=self.panel_color)
        controls_grid.pack(pady=10)
        
        controls = [
            ("F4", "Toggle On/Off"),
            ("MB5", "Auto Click (Hold)"),
            ("F5", "Export Stats"),
            ("← →", "Switch Pages"),
            ("Enter", "Quick Toggle"),
            ("Esc", "Quick Disable")
        ]
        
        for key, action in controls:
            row = tk.Frame(controls_grid, bg=self.panel_color)
            row.pack(pady=3)
            
            tk.Label(
                row,
                text=f"{key}:",
                font=("Arial", 9, "bold"),
                bg=self.panel_color,
                fg=self.accent_color,
                width=8,
                anchor="e"
            ).pack(side=tk.LEFT, padx=5)
            
            tk.Label(
                row,
                text=action,
                font=("Arial", 9),
                bg=self.panel_color,
                fg="#cccccc",
                anchor="w"
            ).pack(side=tk.LEFT)
        
        tk.Label(controls_panel, text="", bg=self.panel_color).pack(pady=5)
    
    
    def create_page_analytics(self):
        """Create Page 3: Analytics and session history"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Current session metrics
        current_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        current_panel.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(
            current_panel,
            text="Current Session Metrics",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        metrics_grid = tk.Frame(current_panel, bg=self.panel_color)
        metrics_grid.pack(pady=10, padx=20)
        
        self.create_metric_row(metrics_grid, "Detection Risk", "risk_level", 0)
        self.create_metric_row(metrics_grid, "Burst Events", "burst_events", 1)
        self.create_metric_row(metrics_grid, "Pause Events", "pause_events", 2)
        self.create_metric_row(metrics_grid, "Pattern Breaks", "pattern_breaks", 3)
        
        tk.Label(current_panel, text="", bg=self.panel_color).pack(pady=5)
        
        # Session history
        history_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        history_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            history_panel,
            text="Session History",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        history_frame = tk.Frame(history_panel, bg=self.panel_color)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        self.history_text = tk.Text(
            history_frame,
            height=10,
            font=("Courier", 8),
            bg="#1a1a1a",
            fg="#cccccc",
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        self.history_text.insert("1.0", "No sessions recorded yet.\nComplete a session to see analytics here.")
        self.history_text.config(state=tk.DISABLED)
        
        tk.Label(history_panel, text="", bg=self.panel_color).pack(pady=5)
    
    
    def create_page_histogram(self):
        """Create Page 4: Histogram visualization"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Histogram panel
        histogram_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        histogram_panel.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        tk.Label(
            histogram_panel,
            text="Click Delay Distribution",
            font=("Arial", 13, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        # Create histogram canvas
        self.histogram = HistogramCanvas(histogram_panel, width=460, height=300)
        self.histogram.pack(pady=10, padx=10)
        
        # Legend
        legend_frame = tk.Frame(histogram_panel, bg=self.panel_color)
        legend_frame.pack(pady=10)
        
        legend_items = [
            ("●", "#4CAF50", "Optimal Range (84-143ms)"),
            ("●", "#FFA500", "Acceptable Range"),
            ("─", "#4CAF50", "Mean (μ)"),
            ("┄", "#FFA500", "Std Dev (σ)")
        ]
        
        for symbol, color, text in legend_items:
            item = tk.Frame(legend_frame, bg=self.panel_color)
            item.pack(side=tk.LEFT, padx=10)
            
            tk.Label(
                item,
                text=symbol,
                fg=color,
                bg=self.panel_color,
                font=("Arial", 12, "bold")
            ).pack(side=tk.LEFT)
            
            tk.Label(
                item,
                text=text,
                fg="#888888",
                bg=self.panel_color,
                font=("Arial", 8)
            ).pack(side=tk.LEFT, padx=3)
        
        tk.Label(histogram_panel, text="", bg=self.panel_color).pack(pady=5)
        
        # Statistics panel
        stats_info_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        stats_info_panel.pack(fill=tk.X)
        
        tk.Label(
            stats_info_panel,
            text="Statistical Summary",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        stats_info_grid = tk.Frame(stats_info_panel, bg=self.panel_color)
        stats_info_grid.pack(pady=10, padx=20)
        
        self.create_metric_row(stats_info_grid, "Mean Delay", "hist_mean", 0)
        self.create_metric_row(stats_info_grid, "Std Deviation", "hist_std", 1)
        self.create_metric_row(stats_info_grid, "Variance", "hist_variance", 2)
        
        tk.Label(stats_info_panel, text="", bg=self.panel_color).pack(pady=5)
    
    
    def create_stat_row(self, parent, label_text, var_name, row):
        """Create a statistic row for dashboard"""
        label = tk.Label(
            parent,
            text=f"{label_text}:",
            font=("Arial", 10),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w"
        )
        label.grid(row=row, column=0, pady=8, padx=10, sticky="w")
        
        value = tk.Label(
            parent,
            text="--",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg=self.accent_color,
            anchor="e"
        )
        value.grid(row=row, column=1, pady=8, padx=10, sticky="e")
        
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        
        setattr(self, var_name, value)
    
    
    def create_metric_row(self, parent, label_text, var_name, row):
        """Create a metric row for analytics"""
        label = tk.Label(
            parent,
            text=f"{label_text}:",
            font=("Arial", 10),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w",
            width=18
        )
        label.grid(row=row, column=0, pady=6, padx=10, sticky="w")
        
        value = tk.Label(
            parent,
            text="--",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg=self.accent_color,
            anchor="e",
            width=15
        )
        value.grid(row=row, column=1, pady=6, padx=10, sticky="e")
        
        setattr(self, var_name, value)
    
    
    def switch_page(self, page_idx):
        """Switch to specified page"""
        if page_idx < 0 or page_idx >= len(self.pages):
            return
        
        for page in self.pages:
            page.pack_forget()
        
        self.pages[page_idx].pack(fill=tk.BOTH, expand=True)
        self.current_page = page_idx
        
        for i, btn in enumerate(self.tab_buttons):
            if i == page_idx:
                btn.config(bg=self.active_tab)
            else:
                btn.config(bg=self.inactive_tab)
        
        self.page_indicator.config(text=f"{page_idx + 1} / {len(self.pages)}")
        self.prev_btn.config(state=tk.NORMAL if page_idx > 0 else tk.DISABLED)
        self.next_btn.config(state=tk.NORMAL if page_idx < len(self.pages) - 1 else tk.DISABLED)
        
        # Update histogram when switching to it
        if page_idx == 3 and self.engine and len(self.engine.all_delays) >= 5:
            mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
            std_dev = self.engine.calculate_std_dev()
            self.histogram.draw_histogram(self.engine.all_delays, mean, std_dev, self.enhanced_mode)
    
    
    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.switch_page(self.current_page + 1)
    
    def prev_page(self):
        if self.current_page > 0:
            self.switch_page(self.current_page - 1)
    
    
    def setup_hotkeys(self):
        """Register keyboard hotkeys"""
        keyboard.add_hotkey('f4', self.toggle_active)
        keyboard.add_hotkey('enter', self.toggle_active)
        keyboard.add_hotkey('escape', self.quick_disable)
        keyboard.add_hotkey('f5', self.export_stats)
        keyboard.add_hotkey('f7', self.toggle_training_mode)
        keyboard.add_hotkey('f8', self.export_human_baseline)
        keyboard.add_hotkey('f9', self.toggle_enhanced_mode)
        keyboard.add_hotkey('left', self.prev_page)
        keyboard.add_hotkey('right', self.next_page)
    
    
    def quick_disable(self):
        if self.active:
            self.toggle_active()
    
    
    def format_time_elapsed(self, seconds):
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = int(seconds % 60)
            return f"{hours}h {minutes}m {secs}s"
    
    
    def toggle_enhanced_mode(self):
        self.enhanced_mode = not self.enhanced_mode
        
        if self.enhanced_mode:
            self.mode_indicator.config(text="⚡ Enhanced Chaos Mode", fg=self.enhanced_color)
            self.enhanced_status.config(text="Status: Enabled", fg=self.enhanced_color)
            self.enhanced_btn.config(bg=self.enhanced_color)
            print("\n[ENHANCED MODE] Activated!\n")
        else:
            self.mode_indicator.config(text="Standard Mode", fg="#888888")
            self.enhanced_status.config(text="Status: Disabled", fg="#888888")
            self.enhanced_btn.config(bg=self.button_color)
            print("\n[STANDARD MODE] Enhanced mode disabled.\n")
        
        if self.active:
            self.engine = ClickerEngine(enhanced_mode=self.enhanced_mode)
            print(f"[MODE SWITCH] Clicker restarted.\n")
    
    
    def toggle_active(self):
        self.active = not self.active
        
        if self.active:
            self.engine = ClickerEngine(enhanced_mode=self.enhanced_mode)
            self.status_indicator.config(text="● ACTIVE", fg=self.accent_color)
            self.click_status.config(text="Hold MB5 to click", fg=self.fg_color)
            self.toggle_btn.config(text="Deactivate (F4)", bg=self.inactive_color)
        else:
            self.clicking = False
            if self.engine and self.engine.is_actively_clicking:
                self.engine.stop_clicking()
            self.status_indicator.config(text="● INACTIVE", fg=self.inactive_color)
            self.click_status.config(text="Session ended - Check Analytics", fg="#888888")
            self.toggle_btn.config(text="Activate (F4)", bg=self.accent_color)
            
            if self.engine:
                self.last_session_stats = self.engine.get_detailed_stats()
                if self.last_session_stats:
                    self.add_session_to_history(self.last_session_stats)
    
    
    def add_session_to_history(self, stats):
        timestamp = datetime.now().strftime('%H:%M:%S')
        mode = "Enhanced" if stats.get('enhanced_mode', False) else "Standard"
        
        if stats['variance'] > 250 and stats['max_cps'] <= 12:
            risk = "LOW"
        elif stats['variance'] > 120:
            risk = "MEDIUM"
        else:
            risk = "HIGH"
        
        session = {
            "timestamp": timestamp,
            "mode": mode,
            "clicks": stats['total'],
            "avg_cps": stats['avg_cps'],
            "variance": stats['variance'],
            "risk": risk
        }
        
        self.session_history.append(session)
        self.update_history_display()
    
    
    def update_history_display(self):
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        
        if not self.session_history:
            self.history_text.insert("1.0", "No sessions recorded yet.")
        else:
            header = f"{'Time':<10} {'Mode':<10} {'Clicks':<8} {'CPS':<6} {'Var':<6} {'Risk':<8}\n"
            self.history_text.insert("1.0", header)
            self.history_text.insert("2.0", "-" * 58 + "\n")
            
            for session in reversed(self.session_history[-10:]):
                line = f"{session['timestamp']:<10} {session['mode']:<10} {session['clicks']:<8} "
                line += f"{session['avg_cps']:<6.1f} {int(session['variance']):<6} {session['risk']:<8}\n"
                self.history_text.insert(tk.END, line)
        
        self.history_text.config(state=tk.DISABLED)
    
    
    def toggle_training_mode(self):
        if self.active:
            print("\n[!] Disable auto-clicker before training!\n")
            return
        
        if not self.human_tracker.is_tracking:
            self.human_tracker.start_tracking()
            self.status_indicator.config(text="● TRAINING MODE", fg=self.training_color)
            self.click_status.config(text="Click naturally - Recording patterns", fg=self.training_color)
        else:
            self.human_tracker.stop_tracking()
            self.status_indicator.config(text="● INACTIVE", fg=self.inactive_color)
            self.click_status.config(text="Training complete - Press F8 to export", fg="#888888")
    
    
    def export_human_baseline(self):
        if self.human_tracker.is_tracking:
            print("\n[!] Stop training mode before exporting!\n")
            return
        print("\n[!] Export feature simplified for demo\n")
    
    
    def export_stats(self):
        if not self.last_session_stats:
            print("\n[!] No session data available!\n")
            return
        
        stats = self.last_session_stats
        mode_text = "Enhanced" if stats.get('enhanced_mode', False) else "Standard"
        
        report = f"""
======================================================================
SESSION REPORT
======================================================================
Mode: {mode_text}
Clicks: {stats['total']}
Avg CPS: {stats['avg_cps']:.2f}
Variance: {int(stats['variance'])}
Risk: {"LOW" if stats['variance'] > 250 else "MEDIUM" if stats['variance'] > 120 else "HIGH"}
======================================================================
"""
        print(report)
        
        filename = f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w') as f:
                f.write(report)
            print(f"[SUCCESS] Exported to: {filename}\n")
        except:
            print("[ERROR] Could not save file\n")
    
    
    def is_mb5_held(self):
        return win32api.GetAsyncKeyState(Config.VK_XBUTTON2) < 0
    
    
    def mouse_monitor(self):
        last_state = False
        last_lmb_state = False
        
        while self.running:
            if self.active:
                current_state = self.is_mb5_held()
                if current_state and not last_state:
                    self.clicking = True
                    if self.engine:
                        self.engine.start_clicking()
                elif not current_state and last_state:
                    self.clicking = False
                    if self.engine:
                        self.engine.stop_clicking()
                        self.engine.consecutive_clicks = 0
                last_state = current_state
            elif self.human_tracker.is_tracking:
                current_lmb = win32api.GetAsyncKeyState(Config.VK_LBUTTON) < 0
                if current_lmb and not last_lmb_state:
                    self.human_tracker.record_click()
                last_lmb_state = current_lmb
            else:
                last_state = False
                last_lmb_state = False
            time.sleep(0.01)
    
    
    def clicking_loop(self):
        while self.running:
            if self.active and self.clicking:
                self.engine.click()
            else:
                time.sleep(0.01)
    
    
    def update_display(self):
        """Update GUI with current statistics and histogram"""
        if self.active and self.engine:
            if self.clicking:
                self.click_status.config(text="⚔️ CLICKING", fg=self.accent_color)
            else:
                self.click_status.config(text="Waiting for MB5...", fg="#888888")
            
            self.total_clicks.config(text=str(self.engine.total_clicks))
            
            if self.engine.total_clicks > 10:
                current_cps = self.engine.get_current_cps()
                self.current_cps.config(text=f"{current_cps:.1f}")
                
                variance = self.engine.calculate_overall_variance() if len(self.engine.all_delays) >= 20 else self.engine.calculate_variance()
                self.variance.config(text=f"{int(variance)}")
                
                stats = self.engine.get_detailed_stats()
                if stats:
                    self.session_cps.config(text=f"{stats['avg_cps']:.2f}")
                    
                    # Update analytics
                    if stats['variance'] > 250 and stats['max_cps'] <= 12:
                        risk = "LOW"
                        risk_color = self.accent_color
                    elif stats['variance'] > 120:
                        risk = "MEDIUM"
                        risk_color = self.training_color
                    else:
                        risk = "HIGH"
                        risk_color = self.inactive_color
                    
                    self.risk_level.config(text=risk, fg=risk_color)
                    self.burst_events.config(text=str(stats.get('burst_count', 0)))
                    self.pause_events.config(text=str(stats.get('pause_count', 0)))
                    self.pattern_breaks.config(text=str(stats['pattern_breaks']))
                    
                    # Update histogram stats
                    mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
                    std_dev = self.engine.calculate_std_dev()
                    self.hist_mean.config(text=f"{mean:.1f} ms")
                    self.hist_std.config(text=f"{std_dev:.1f} ms")
                    self.hist_variance.config(text=f"{int(variance)}")
                    
                    # Update histogram if on that page
                    if self.current_page == 3 and len(self.engine.all_delays) >= 5:
                        self.histogram.draw_histogram(self.engine.all_delays, mean, std_dev, self.enhanced_mode)
            else:
                self.current_cps.config(text="--")
                self.variance.config(text="--")
                self.session_cps.config(text="--")
            
            elapsed_seconds = (datetime.now() - self.engine.session_start).total_seconds()
            self.time_elapsed.config(text=self.format_time_elapsed(elapsed_seconds))
        
        elif self.human_tracker.is_tracking:
            self.total_clicks.config(text=str(self.human_tracker.total_clicks))
            self.current_cps.config(text="TRAINING")
            self.variance.config(text="--")
            self.session_cps.config(text="--")
            
            if self.human_tracker.session_start:
                elapsed_seconds = (datetime.now() - self.human_tracker.session_start).total_seconds()
                self.time_elapsed.config(text=self.format_time_elapsed(elapsed_seconds))
        
        else:
            self.total_clicks.config(text="0")
            self.current_cps.config(text="--")
            self.variance.config(text="--")
            self.session_cps.config(text="--")
            self.time_elapsed.config(text="--")
            
            self.risk_level.config(text="--", fg=self.accent_color)
            self.burst_events.config(text="--")
            self.pause_events.config(text="--")
            self.pattern_breaks.config(text="--")
            self.hist_mean.config(text="--")
            self.hist_std.config(text="--")
            self.hist_variance.config(text="--")
        
        self.root.after(500, self.update_display)  # Update histogram every 500ms
    
    
    def start_threads(self):
        click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
        mouse_thread = threading.Thread(target=self.mouse_monitor, daemon=True)
        click_thread.start()
        mouse_thread.start()
    
    
    def on_close(self):
        if self.engine and self.engine.is_actively_clicking:
            self.engine.stop_clicking()
        self.running = False
        self.root.destroy()
    
    
    def run(self):
        self.root.mainloop()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if not is_admin:
            print("\n⚠️  ERROR: Need Administrator privileges")
            input("Press Enter to exit...")
            exit(1)
        
        app = AutoClickerGUI()
        app.run()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
