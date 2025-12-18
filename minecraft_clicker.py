"""
═══════════════════════════════════════════════════════════════════════════════
MINECRAFT AUTO CLICKER - ANTI-CHEAT COMPLIANT
═══════════════════════════════════════════════════════════════════════════════
Version: 2.0
Target: 7-12 CPS range with human-like variance
Anti-Detection Features:
  - Weibull + Gaussian distribution mixing
  - Pattern break detection and mitigation
  - Variance monitoring and adjustment
  - Temporal drift simulation
  - Rhythmic variation modeling
  
Controls:
  - F4: Toggle activation
  - MB5 (hold): Execute clicking
  - F5: Export detailed statistics
  
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
from collections import deque
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
    
    # Anti-Detection Thresholds
    MIN_VARIANCE_THRESHOLD = 120      # Minimum variance to avoid bot detection
    PATTERN_CHECK_WINDOW = 20         # Number of clicks to check for patterns
    
    # Mouse Button Constants
    VK_XBUTTON2 = 0x06               # MB5 (side mouse button)


# ═════════════════════════════════════════════════════════════════════════════
# CLICKER ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class ClickerEngine:
    """
    Core clicking engine with advanced anti-detection algorithms.
    
    This engine implements multiple layers of randomness:
    1. Weibull and Gaussian distributions for base timing
    2. User-specific baseline variation
    3. Momentum-based acceleration/deceleration
    4. Temporal drift simulation
    5. Rhythmic variation patterns
    6. Adaptive variance adjustment
    7. Pattern break injection
    """
    
    def __init__(self):
        """Initialize the clicker engine with randomness parameters"""
        
        # ─────────────────────────────────────────────────────────────────────
        # Session Tracking
        # ─────────────────────────────────────────────────────────────────────
        self.total_clicks = 0
        self.session_start = datetime.now()
        self.combat_start = None
        
        # ─────────────────────────────────────────────────────────────────────
        # Click History & Statistics
        # ─────────────────────────────────────────────────────────────────────
        self.click_history = deque(maxlen=50)      # Rolling window of recent delays
        self.recent_click_times = deque(maxlen=20) # For CPS calculation
        self.all_delays = []                       # Complete delay history for stats
        
        # ─────────────────────────────────────────────────────────────────────
        # Randomness Parameters (Human Simulation)
        # ─────────────────────────────────────────────────────────────────────
        self.user_baseline = random.uniform(0.88, 1.12)  # Personal clicking speed
        self.rhythm_phase = 0.0                          # Rhythmic variation phase
        self.drift = 0.0                                 # Temporal drift accumulator
        self.consecutive_clicks = 0                      # Current combo length
        
        # ─────────────────────────────────────────────────────────────────────
        # Anti-Detection Metrics
        # ─────────────────────────────────────────────────────────────────────
        self.variance_adjustment = 0.0
        self.last_variance_check = datetime.now()
        self.pattern_breaks = 0
        self.variance_adjustments = 0
        
        # ─────────────────────────────────────────────────────────────────────
        # Time Tracking
        # ─────────────────────────────────────────────────────────────────────
        self.total_clicking_time = 0.0      # Total time spent actively clicking
        self.click_session_start = None     # Start time of current clicking session
        self.is_actively_clicking = False   # Currently clicking flag
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Time Tracking Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def start_clicking(self):
        """
        Called when MB5 is pressed down.
        Starts the timer for active clicking time tracking.
        """
        if not self.is_actively_clicking:
            self.is_actively_clicking = True
            self.click_session_start = time.time()
    
    def stop_clicking(self):
        """
        Called when MB5 is released.
        Adds the elapsed time to total clicking time and resets the session timer.
        """
        if self.is_actively_clicking and self.click_session_start:
            self.is_actively_clicking = False
            elapsed = time.time() - self.click_session_start
            self.total_clicking_time += elapsed
            self.click_session_start = None
    
    def get_active_clicking_time(self):
        """
        Returns the total time spent actively clicking.
        Includes the current session if MB5 is still being held.
        
        Returns:
            float: Total clicking time in seconds
        """
        total = self.total_clicking_time
        
        # Add current session if actively clicking
        if self.is_actively_clicking and self.click_session_start:
            total += time.time() - self.click_session_start
        
        return total
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Random Number Generation (Statistical Distributions)
    # ─────────────────────────────────────────────────────────────────────────
    
    def gaussian_random(self, mean, std_dev):
        """
        Generate a random number using Gaussian (normal) distribution.
        Uses Box-Muller transform for accurate normal distribution.
        
        Args:
            mean (float): Mean of the distribution
            std_dev (float): Standard deviation
            
        Returns:
            float: Random value from normal distribution
        """
        u1, u2 = random.random(), random.random()
        rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)
        return mean + std_dev * rand_std_normal
    
    def weibull_random(self, scale, shape):
        """
        Generate a random number using Weibull distribution.
        Weibull distribution models "time until failure" - good for human reaction times.
        
        Args:
            scale (float): Scale parameter (affects spread)
            shape (float): Shape parameter (affects curve shape)
            
        Returns:
            float: Random value from Weibull distribution
        """
        u = random.random()
        return scale * ((-math.log(1 - u)) ** (1 / shape))
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Safety & Anti-Cheat Monitoring
    # ─────────────────────────────────────────────────────────────────────────
    
    def check_cps(self):
        """
        Monitor current CPS and enforce hard limits.
        Prevents exceeding the 12 CPS anti-cheat threshold.
        
        Returns:
            float: Additional delay needed (in seconds) if approaching limit, else 0
        """
        current_time = time.time()
        
        # Remove clicks older than 1 second
        while self.recent_click_times and current_time - self.recent_click_times[0] > 1.0:
            self.recent_click_times.popleft()
        
        # Calculate current CPS
        if len(self.recent_click_times) >= 2:
            time_span = current_time - self.recent_click_times[0]
            recent_cps = len(self.recent_click_times) / time_span if time_span > 0 else 0
            
            # If approaching limit, add safety delay
            if recent_cps >= 11:
                return 0.06  # 60ms safety delay
        
        return 0
    
    def calculate_variance(self):
        """
        Calculate the statistical variance of recent click delays.
        Low variance = robotic behavior, triggers anti-cheat.
        
        Returns:
            float: Variance of recent click timings
        """
        if len(self.click_history) < 10:
            return 200  # Default high variance for insufficient data
        
        recent = list(self.click_history)[-15:]
        mean = sum(recent) / len(recent)
        return sum((x - mean) ** 2 for x in recent) / len(recent)
    
    def check_variance(self):
        """
        Monitor variance levels and inject additional randomness if needed.
        This prevents detection by ML-based anti-cheat systems that look for
        consistent timing patterns.
        """
        # Only check every 15 seconds to avoid over-adjustment
        if (datetime.now() - self.last_variance_check).total_seconds() < 15:
            return
        
        if len(self.click_history) >= 15:
            variance = self.calculate_variance()
            
            # Variance too low = too consistent = bot-like
            if variance < Config.MIN_VARIANCE_THRESHOLD:
                # Add random adjustment to increase variance
                self.variance_adjustment = random.uniform(0.1, 0.2)
                self.variance_adjustments += 1
            else:
                # Gradually reduce adjustment
                self.variance_adjustment *= 0.8
            
            self.last_variance_check = datetime.now()
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Click Delay Calculation (Core Algorithm)
    # ─────────────────────────────────────────────────────────────────────────
    
    def calculate_delay(self):
        """
        Calculate the delay before the next click using multiple layers of randomness.
        
        This is the core of the anti-detection system. It combines:
        1. Statistical distributions (Gaussian + Weibull)
        2. User-specific baseline
        3. Momentum effects (acceleration/deceleration)
        4. Temporal drift (gradual speed changes)
        5. Rhythmic variation (natural human patterns)
        6. Variance adjustment (ML evasion)
        7. Random noise
        8. Pattern break detection
        
        Returns:
            float: Delay in milliseconds before next click
        """
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 1: Base delay from statistical distribution (70% Gaussian, 30% Weibull)
        # ─────────────────────────────────────────────────────────────────────
        if random.random() < 0.7:
            # Gaussian: Normal clicking pattern
            base = abs(self.gaussian_random(108, 18))
        else:
            # Weibull: Occasional variation in rhythm
            base = self.weibull_random(100, 2.5)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 2: Apply user-specific baseline (everyone clicks slightly differently)
        # ─────────────────────────────────────────────────────────────────────
        base *= self.user_baseline
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 3: Add general random variation
        # ─────────────────────────────────────────────────────────────────────
        base *= random.uniform(0.85, 1.15)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 4: Momentum effect (acceleration during combos)
        # ─────────────────────────────────────────────────────────────────────
        if self.consecutive_clicks < 3:
            # Starting slow (reaction time)
            base *= random.uniform(1.05, 1.15)
        elif self.consecutive_clicks < 8:
            # Normal speed
            base *= random.uniform(0.95, 1.05)
        else:
            # Accelerating (getting into rhythm)
            base *= random.uniform(0.90, 0.98)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 5: Temporal drift (gradual speed changes over time)
        # ─────────────────────────────────────────────────────────────────────
        self.drift += random.uniform(-0.003, 0.003)
        self.drift = max(-0.18, min(0.18, self.drift))  # Clamp drift
        base *= (1.0 + self.drift)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 6: Rhythmic variation (humans have natural rhythm patterns)
        # ─────────────────────────────────────────────────────────────────────
        self.rhythm_phase = (self.rhythm_phase + random.uniform(0.25, 0.50)) % (2 * math.pi)
        base += math.sin(self.rhythm_phase) * 14
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 7: Variance adjustment (ML evasion)
        # ─────────────────────────────────────────────────────────────────────
        base *= (1.0 + self.variance_adjustment)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 8: Random noise
        # ─────────────────────────────────────────────────────────────────────
        base += random.randint(-15, 16)
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 9: Hard clamp to CPS limits (7-12 CPS)
        # ─────────────────────────────────────────────────────────────────────
        final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, base))
        
        # ─────────────────────────────────────────────────────────────────────
        # Step 10: Pattern break detection and mitigation
        # ─────────────────────────────────────────────────────────────────────
        if len(self.click_history) >= Config.PATTERN_CHECK_WINDOW:
            recent = list(self.click_history)[-Config.PATTERN_CHECK_WINDOW:]
            mean = sum(recent) / len(recent)
            variance = sum((x - mean) ** 2 for x in recent) / len(recent)
            
            # If variance is too low, inject chaos
            if variance < Config.MIN_VARIANCE_THRESHOLD:
                final *= random.uniform(0.7, 1.3)
                final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, final))
                self.pattern_breaks += 1
        
        # ─────────────────────────────────────────────────────────────────────
        # Record and return
        # ─────────────────────────────────────────────────────────────────────
        self.click_history.append(final)
        self.all_delays.append(final)
        return final
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Click Execution
    # ─────────────────────────────────────────────────────────────────────────
    
    def click(self):
        """
        Execute a single click with proper timing and anti-detection measures.
        This is called repeatedly while MB5 is held down.
        """
        # Mark combat start time
        if self.combat_start is None:
            self.combat_start = datetime.now()
        
        # Check if we need safety delay to avoid CPS violations
        safety = self.check_cps()
        if safety > 0:
            time.sleep(safety)
        
        # Check and adjust variance if needed
        self.check_variance()
        
        # Calculate delay for this click
        delay_ms = self.calculate_delay()
        
        # Calculate click pressure (how long to hold mouse button down)
        # Humans don't click instantly - there's a press duration
        pressure_ms = abs(self.gaussian_random(26, 8))
        
        # ─────────────────────────────────────────────────────────────────────
        # Execute the click
        # ─────────────────────────────────────────────────────────────────────
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(pressure_ms / 1000.0)  # Hold button down
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        # ─────────────────────────────────────────────────────────────────────
        # Record click for statistics
        # ─────────────────────────────────────────────────────────────────────
        self.recent_click_times.append(time.time())
        self.total_clicks += 1
        self.consecutive_clicks += 1
        
        # ─────────────────────────────────────────────────────────────────────
        # Wait before next click (this creates the CPS timing)
        # ─────────────────────────────────────────────────────────────────────
        time.sleep(delay_ms / 1000.0)
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Statistics & Reporting
    # ─────────────────────────────────────────────────────────────────────────
    
    def get_current_cps(self):
        """
        Calculate the current CPS based on recent click history.
        
        Returns:
            float: Current clicks per second
        """
        if len(self.click_history) < 5:
            return 0.0
        
        recent = list(self.click_history)[-10:]
        avg_delay = sum(recent) / len(recent)
        return 1000.0 / avg_delay
    
    def get_detailed_stats(self):
        """
        Generate comprehensive statistics for the session.
        
        Returns:
            dict: Dictionary containing all session statistics
        """
        if not self.all_delays:
            return None
        
        delays = self.all_delays
        avg_delay = sum(delays) / len(delays)
        
        # Calculate percentiles for detailed analysis
        sorted_delays = sorted(delays)
        p10 = sorted_delays[int(len(sorted_delays) * 0.10)]
        p50 = sorted_delays[int(len(sorted_delays) * 0.50)]
        p90 = sorted_delays[int(len(sorted_delays) * 0.90)]
        
        # Time calculations
        session_duration = (datetime.now() - self.session_start).total_seconds()
        clicking_duration = self.get_active_clicking_time()
        
        return {
            "total": self.total_clicks,
            "avg_cps": 1000.0 / avg_delay,
            "min_cps": 1000.0 / max(delays),
            "max_cps": 1000.0 / min(delays),
            "median_cps": 1000.0 / p50,
            "variance": self.calculate_variance(),
            "pattern_breaks": self.pattern_breaks,
            "variance_adjustments": self.variance_adjustments,
            "session_duration": session_duration,
            "clicking_duration": clicking_duration,
            "idle_time": session_duration - clicking_duration,
            "p10_delay": p10,
            "p50_delay": p50,
            "p90_delay": p90,
            "min_delay": min(delays),
            "max_delay": max(delays),
            "avg_delay": avg_delay
        }


# ═════════════════════════════════════════════════════════════════════════════
# GUI APPLICATION
# ═════════════════════════════════════════════════════════════════════════════

class AutoClickerGUI:
    """
    Graphical user interface for the auto clicker.
    Provides real-time statistics and control interface.
    """
    
    def __init__(self):
        """Initialize the GUI and all components"""
        
        # ─────────────────────────────────────────────────────────────────────
        # Main Window Setup
        # ─────────────────────────────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("Minecraft Auto Clicker")
        self.root.geometry("420x480")
        self.root.resizable(False, False)
        
        # ─────────────────────────────────────────────────────────────────────
        # Dark Theme Colors
        # ─────────────────────────────────────────────────────────────────────
        self.bg_color = "#1e1e1e"          # Main background
        self.fg_color = "#ffffff"          # Text color
        self.accent_color = "#4CAF50"      # Green accent (active/positive)
        self.inactive_color = "#f44336"    # Red accent (inactive/negative)
        self.panel_color = "#2d2d2d"       # Panel background
        
        self.root.configure(bg=self.bg_color)
        
        # ─────────────────────────────────────────────────────────────────────
        # Application State
        # ─────────────────────────────────────────────────────────────────────
        self.active = False                 # Program activated (F4)
        self.clicking = False               # Currently clicking (MB5 held)
        self.engine = None                  # Clicker engine instance
        self.running = True                 # Main loop control
        self.last_session_stats = None      # Cached stats for export
        
        # ─────────────────────────────────────────────────────────────────────
        # Initialize UI and Start Systems
        # ─────────────────────────────────────────────────────────────────────
        self.setup_ui()
        self.setup_hotkeys()
        self.start_threads()
        
        # Start display update loop
        self.update_display()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # UI Construction
    # ─────────────────────────────────────────────────────────────────────────
    
    def setup_ui(self):
        """Build the complete user interface"""
        
        # ═════════════════════════════════════════════════════════════════════
        # HEADER SECTION
        # ═════════════════════════════════════════════════════════════════════
        header = tk.Frame(self.root, bg=self.bg_color)
        header.pack(pady=20)
        
        title = tk.Label(
            header, 
            text="⚔️ Minecraft Auto Clicker", 
            font=("Arial", 20, "bold"), 
            bg=self.bg_color, 
            fg=self.fg_color
        )
        title.pack()
        
        subtitle = tk.Label(
            header, 
            text="Anti-Cheat Compliant • 7-12 CPS", 
            font=("Arial", 10), 
            bg=self.bg_color, 
            fg="#888888"
        )
        subtitle.pack(pady=(5, 0))
        
        # ═════════════════════════════════════════════════════════════════════
        # STATUS PANEL
        # ═════════════════════════════════════════════════════════════════════
        status_frame = tk.Frame(
            self.root, 
            bg=self.panel_color, 
            relief=tk.RIDGE, 
            bd=2
        )
        status_frame.pack(pady=15, padx=25, fill=tk.BOTH)
        
        # Status indicator (ACTIVE/INACTIVE)
        self.status_label = tk.Label(
            status_frame, 
            text="● INACTIVE", 
            font=("Arial", 18, "bold"),
            bg=self.panel_color, 
            fg=self.inactive_color
        )
        self.status_label.pack(pady=15)
        
        # Current action (Ready/Waiting/Clicking)
        self.click_status = tk.Label(
            status_frame, 
            text="Ready", 
            font=("Arial", 11),
            bg=self.panel_color, 
            fg="#888888"
        )
        self.click_status.pack(pady=(0, 15))
        
        # ═════════════════════════════════════════════════════════════════════
        # LIVE STATISTICS PANEL
        # ═════════════════════════════════════════════════════════════════════
        stats_frame = tk.Frame(
            self.root, 
            bg=self.panel_color, 
            relief=tk.RIDGE, 
            bd=2
        )
        stats_frame.pack(pady=15, padx=25, fill=tk.BOTH, expand=True)
        
        tk.Label(
            stats_frame, 
            text="Live Statistics", 
            font=("Arial", 13, "bold"),
            bg=self.panel_color, 
            fg=self.fg_color
        ).pack(pady=(15, 10))
        
        # Stats grid
        stats_grid = tk.Frame(stats_frame, bg=self.panel_color)
        stats_grid.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        # Configure grid columns
        stats_grid.columnconfigure(0, weight=1, minsize=150)
        stats_grid.columnconfigure(1, weight=1, minsize=100)
        
        # Create stat rows
        self.create_stat_row(stats_grid, "Total Clicks", "total_clicks", 0)
        self.create_stat_row(stats_grid, "Current CPS", "current_cps", 1)
        self.create_stat_row(stats_grid, "Variance", "variance", 2)
        self.create_stat_row(stats_grid, "Session Avg", "session_cps", 3)
        
        # Bottom spacing
        tk.Label(stats_frame, text="", bg=self.panel_color).pack(pady=5)
        
        # ═════════════════════════════════════════════════════════════════════
        # CONTROLS PANEL
        # ═════════════════════════════════════════════════════════════════════
        controls_frame = tk.Frame(
            self.root, 
            bg=self.panel_color, 
            relief=tk.RIDGE, 
            bd=2
        )
        controls_frame.pack(pady=15, padx=25, fill=tk.BOTH)
        
        tk.Label(
            controls_frame, 
            text="Controls", 
            font=("Arial", 12, "bold"),
            bg=self.panel_color, 
            fg=self.fg_color
        ).pack(pady=(12, 10))
        
        # Controls list
        controls_grid = tk.Frame(controls_frame, bg=self.panel_color)
        controls_grid.pack(pady=(0, 12))
        
        controls_text = [
            ("F4", "Toggle On/Off"),
            ("MB5", "Auto Click (Hold)"),
            ("F5", "Export Stats")
        ]
        
        for key, action in controls_text:
            key_frame = tk.Frame(controls_grid, bg=self.panel_color)
            key_frame.pack(pady=3)
            
            key_label = tk.Label(
                key_frame, 
                text=f"{key}:", 
                font=("Arial", 11, "bold"),
                bg=self.panel_color, 
                fg=self.accent_color,
                width=6, 
                anchor="e"
            )
            key_label.pack(side=tk.LEFT, padx=(0, 10))
            
            action_label = tk.Label(
                key_frame, 
                text=action, 
                font=("Arial", 11),
                bg=self.panel_color, 
                fg="#cccccc",
                anchor="w"
            )
            action_label.pack(side=tk.LEFT)
    
    def create_stat_row(self, parent, label_text, var_name, row):
        """
        Create a single statistic row in the stats grid.
        
        Args:
            parent: Parent frame
            label_text (str): Label for the stat
            var_name (str): Variable name to store the value label
            row (int): Grid row number
        """
        label = tk.Label(
            parent, 
            text=f"{label_text}:", 
            font=("Arial", 11),
            bg=self.panel_color, 
            fg="#cccccc",
            anchor="w"
        )
        label.grid(row=row, column=0, pady=8, padx=(10, 10), sticky="w")
        
        value = tk.Label(
            parent, 
            text="0", 
            font=("Arial", 11, "bold"),
            bg=self.panel_color, 
            fg=self.accent_color,
            anchor="e"
        )
        value.grid(row=row, column=1, pady=8, padx=(10, 10), sticky="e")
        
        # Store reference to value label
        setattr(self, var_name, value)
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Hotkey Setup
    # ─────────────────────────────────────────────────────────────────────────
    
    def setup_hotkeys(self):
        """Register keyboard hotkeys"""
        keyboard.add_hotkey('f4', self.toggle_active)
        keyboard.add_hotkey('f5', self.export_stats)
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Control Methods
    # ─────────────────────────────────────────────────────────────────────────
    
    def toggle_active(self):
        """
        Toggle the clicker on/off (F4 hotkey).
        Creates new engine when activating, saves stats when deactivating.
        """
        self.active = not self.active
        
        if self.active:
            # ─────────────────────────────────────────────────────────────────
            # ACTIVATION
            # ─────────────────────────────────────────────────────────────────
            self.engine = ClickerEngine()
            self.status_label.config(text="● ACTIVE", fg=self.accent_color)
            self.click_status.config(text="Hold MB5 to click")
            
        else:
            # ─────────────────────────────────────────────────────────────────
            # DEACTIVATION
            # ─────────────────────────────────────────────────────────────────
            self.clicking = False
            
            # FIX: Finalize clicking time if MB5 still held when deactivating
            if self.engine and self.engine.is_actively_clicking:
                self.engine.stop_clicking()
            
            self.status_label.config(text="● INACTIVE", fg=self.inactive_color)
            self.click_status.config(text="Session ended - Press F5 for stats")
            
            # Save stats for export
            if self.engine:
                self.last_session_stats = self.engine.get_detailed_stats()
    
    def export_stats(self):
        """
        Export detailed session statistics (F5 hotkey).
        Prints to console and saves to timestamped text file.
        """
        if not self.last_session_stats:
            print("\n[!] No session data available. Run a session first!\n")
            return
        
        stats = self.last_session_stats
        
        # ─────────────────────────────────────────────────────────────────────
        # Determine Risk Level
        # ─────────────────────────────────────────────────────────────────────
        if stats['variance'] > 250 and stats['max_cps'] <= 12:
            risk = "LOW"
            risk_explanation = "Excellent randomness, compliant CPS"
        elif stats['variance'] > 120:
            risk = "MEDIUM"
            risk_explanation = "Acceptable variance, monitor closely"
        else:
            risk = "HIGH"
            risk_explanation = "Too consistent, increase randomness"
        
        # ─────────────────────────────────────────────────────────────────────
        # Calculate Uptime Percentage
        # ─────────────────────────────────────────────────────────────────────
        if stats['session_duration'] > 0:
            uptime_percent = (stats['clicking_duration'] / stats['session_duration']) * 100
        else:
            uptime_percent = 0
        
        # ─────────────────────────────────────────────────────────────────────
        # Generate Report
        # ─────────────────────────────────────────────────────────────────────
        report = f"""
======================================================================
MINECRAFT AUTO CLICKER - SESSION REPORT
======================================================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

SESSION OVERVIEW
----------------------------------------------------------------------
Total Clicks:              {stats['total']}
Total Session Time:        {stats['session_duration']:.1f} seconds
Active Clicking Time:      {stats['clicking_duration']:.1f} seconds
Idle Time:                 {stats['idle_time']:.1f} seconds
Uptime:                    {uptime_percent:.1f}%

Average CPS:               {stats['avg_cps']:.2f}
Median CPS:                {stats['median_cps']:.2f}

CPS STATISTICS
----------------------------------------------------------------------
Minimum CPS:               {stats['min_cps']:.2f}
Maximum CPS:               {stats['max_cps']:.2f}
CPS Range:                 {stats['min_cps']:.2f} - {stats['max_cps']:.2f}

DELAY STATISTICS (milliseconds)
----------------------------------------------------------------------
Average Delay:             {stats['avg_delay']:.2f} ms
Median Delay (P50):        {stats['p50_delay']:.2f} ms
10th Percentile (P10):     {stats['p10_delay']:.2f} ms
90th Percentile (P90):     {stats['p90_delay']:.2f} ms
Min Delay:                 {stats['min_delay']:.2f} ms
Max Delay:                 {stats['max_delay']:.2f} ms

ANTI-DETECTION METRICS
----------------------------------------------------------------------
Variance:                  {stats['variance']:.0f}
Pattern Breaks:            {stats['pattern_breaks']}
Variance Adjustments:      {stats['variance_adjustments']}

ANTI-CHEAT ASSESSMENT
----------------------------------------------------------------------
CPS Compliance:            {'PASS' if stats['max_cps'] <= 12 else 'FAIL'}
Variance Threshold:        {'PASS' if stats['variance'] > 120 else 'WARNING'}
Pattern Detection:         {'ACTIVE' if stats['pattern_breaks'] > 0 else 'INACTIVE'}

DETECTION RISK: {risk}
Explanation: {risk_explanation}

======================================================================
RECOMMENDED SAFE RANGES (Anti-Cheat Compliant)
======================================================================

CRITICAL THRESHOLDS:
----------------------------------------------------------------------
CPS Maximum:               <= 12.0 (Hard limit for anti-cheat)
Variance Minimum:          >= 120 (Below this triggers bot detection)

OPTIMAL RANGES (Green Zone):
----------------------------------------------------------------------
Average CPS:               8.5 - 10.5 (Competitive but safe)
Variance:                  250+ (Excellent human-like behavior)
Max CPS:                   <= 11.9 (Stay under hard cap)
Pattern Breaks:            2+ per 200 clicks (Shows adaptation)

ACCEPTABLE RANGES (Yellow Zone):
----------------------------------------------------------------------
Average CPS:               7.0 - 8.4 or 10.6 - 11.5
Variance:                  120 - 249 (Acceptable, watch closely)
Max CPS:                   11.9 - 12.0 (Cutting it close)
Pattern Breaks:            0-1 per 200 clicks (Minimal adaptation)

DANGER ZONES (Red Zone):
----------------------------------------------------------------------
Average CPS:               > 12.0 (INSTANT BAN RISK)
Variance:                  < 120 (Bot-like consistency)
Max CPS:                   > 12.0 (Anti-cheat violation)
Pattern Breaks:            0 with low variance (Robotic)

YOUR SESSION ANALYSIS:
----------------------------------------------------------------------
Average CPS:               {stats['avg_cps']:.2f} ({'GREEN' if 8.5 <= stats['avg_cps'] <= 10.5 else 'YELLOW' if 7.0 <= stats['avg_cps'] <= 11.5 else 'RED'})
Variance:                  {stats['variance']:.0f} ({'GREEN' if stats['variance'] >= 250 else 'YELLOW' if stats['variance'] >= 120 else 'RED'})
Max CPS:                   {stats['max_cps']:.2f} ({'GREEN' if stats['max_cps'] <= 11.9 else 'YELLOW' if stats['max_cps'] <= 12.0 else 'RED'})

Overall Status:            {risk}

RECOMMENDATIONS:
----------------------------------------------------------------------"""

        # ─────────────────────────────────────────────────────────────────────
        # Generate Specific Recommendations
        # ─────────────────────────────────────────────────────────────────────
        recommendations = []
        
        if stats['max_cps'] > 12.0:
            recommendations.append("- URGENT: Reduce max CPS, you exceeded 12.0 limit")
        elif stats['max_cps'] > 11.9:
            recommendations.append("- Consider reducing max CPS slightly for safety margin")
        
        if stats['variance'] < 120:
            recommendations.append("- URGENT: Increase randomness, variance too low")
        elif stats['variance'] < 250:
            recommendations.append("- Good variance but aim for 250+ for best results")
        
        if stats['avg_cps'] < 8.5:
            recommendations.append("- Your clicking is conservative, can increase slightly")
        elif stats['avg_cps'] > 10.5:
            recommendations.append("- Your clicking is aggressive, consider toning down")
        
        if stats['pattern_breaks'] == 0 and stats['variance'] < 200:
            recommendations.append("- No pattern breaks occurred, may need longer sessions")
        
        if not recommendations:
            recommendations.append("- Excellent session! All metrics in optimal ranges")
            recommendations.append("- Continue with current settings for competition")
        
        for rec in recommendations:
            report += f"\n{rec}"
        
        report += "\n======================================================================\n"
        
        # ─────────────────────────────────────────────────────────────────────
        # Output Report
        # ─────────────────────────────────────────────────────────────────────
        print(report)
        
        # Save to file
        filename = f"clicker_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w') as f:
                f.write(report)
            print(f"[SUCCESS] Stats exported to: {filename}\n")
        except Exception as e:
            print(f"[ERROR] Could not save to file: {e}\n")
            print("Stats are displayed above - you can copy/paste from console.\n")
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Mouse Input Detection
    # ─────────────────────────────────────────────────────────────────────────
    
    def is_mb5_held(self):
        """
        Check if MB5 (side mouse button) is currently pressed.
        
        Returns:
            bool: True if MB5 is pressed, False otherwise
        """
        return win32api.GetAsyncKeyState(Config.VK_XBUTTON2) < 0
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Background Threads
    # ─────────────────────────────────────────────────────────────────────────
    
    def mouse_monitor(self):
        """
        Background thread that monitors MB5 button state.
        Triggers clicking start/stop based on button press/release.
        """
        last_state = False
        
        while self.running:
            if self.active:
                current_state = self.is_mb5_held()
                
                # ─────────────────────────────────────────────────────────────
                # MB5 just pressed
                # ─────────────────────────────────────────────────────────────
                if current_state and not last_state:
                    self.clicking = True
                    if self.engine:
                        self.engine.start_clicking()  # Start time tracking
                
                # ─────────────────────────────────────────────────────────────
                # MB5 just released
                # ─────────────────────────────────────────────────────────────
                elif not current_state and last_state:
                    self.clicking = False
                    if self.engine:
                        self.engine.stop_clicking()  # Stop time tracking
                        self.engine.consecutive_clicks = 0  # Reset combo
                
                last_state = current_state
            else:
                last_state = False
            
            time.sleep(0.01)  # Check every 10ms
    
    def clicking_loop(self):
        """
        Background thread that executes clicks.
        Continuously calls engine.click() while clicking is active.
        """
        while self.running:
            if self.active and self.clicking:
                self.engine.click()
            else:
                time.sleep(0.01)  # Idle sleep
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Display Update
    # ─────────────────────────────────────────────────────────────────────────
    
    def update_display(self):
        """
        Update the GUI with current statistics.
        Called every 100ms to refresh display.
        """
        if self.active and self.engine:
            # ─────────────────────────────────────────────────────────────────
            # Update Click Status
            # ─────────────────────────────────────────────────────────────────
            if self.clicking:
                self.click_status.config(text="⚔️ CLICKING", fg=self.accent_color)
            else:
                self.click_status.config(text="Waiting for MB5...", fg="#888888")
            
            # ─────────────────────────────────────────────────────────────────
            # Update Statistics
            # ─────────────────────────────────────────────────────────────────
            self.total_clicks.config(text=str(self.engine.total_clicks))
            
            if self.engine.total_clicks > 10:
                current_cps = self.engine.get_current_cps()
                self.current_cps.config(text=f"{current_cps:.1f}")
                
                variance = self.engine.calculate_variance()
                self.variance.config(text=f"{int(variance)}")
                
                stats = self.engine.get_detailed_stats()
                if stats:
                    self.session_cps.config(text=f"{stats['avg_cps']:.2f}")
            else:
                self.current_cps.config(text="--")
                self.variance.config(text="--")
                self.session_cps.config(text="--")
        else:
            # Reset display when inactive
            self.total_clicks.config(text="0")
            self.current_cps.config(text="--")
            self.variance.config(text="--")
            self.session_cps.config(text="--")
        
        # Schedule next update
        self.root.after(100, self.update_display)
    
    
    # ─────────────────────────────────────────────────────────────────────────
    # Thread Management
    # ─────────────────────────────────────────────────────────────────────────
    
    def start_threads(self):
        """Start background worker threads"""
        click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
        mouse_thread = threading.Thread(target=self.mouse_monitor, daemon=True)
        
        click_thread.start()
        mouse_thread.start()
    
    def on_close(self):
        """
        Handle window close event.
        Ensures proper cleanup of resources and time tracking.
        """
        # FIX: Finalize clicking time before closing
        if self.engine and self.engine.is_actively_clicking:
            self.engine.stop_clicking()
        
        self.running = False
        self.root.destroy()
    
    def run(self):
        """Start the GUI main loop"""
        self.root.mainloop()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        # ─────────────────────────────────────────────────────────────────────
        # Check Administrator Privileges
        # ─────────────────────────────────────────────────────────────────────
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if not is_admin:
            print("\n⚠️  ERROR: Need Administrator privileges")
            print("Right-click Command Prompt → 'Run as Administrator'\n")
            input("Press Enter to exit...")
            exit(1)
        
        # ─────────────────────────────────────────────────────────────────────
        # Launch Application
        # ─────────────────────────────────────────────────────────────────────
        app = AutoClickerGUI()
        app.run()
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
