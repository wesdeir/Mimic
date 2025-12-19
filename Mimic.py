"""
═══════════════════════════════════════════════════════════════════════════════
MIMIC v3.7 - STATISTICAL GHOST CLICKER
═══════════════════════════════════════════════════════════════════════════════
Version: 3.7.0 - Enhanced UI Update
Target: 7-12 CPS average with 15-16 CPS spikes

KEY FEATURES:
  ✅ Adaptive Mixed Mode (butterfly/jitter/normal)
  ✅ Statistical Distribution Engine (Gaussian + Weibull)
  ✅ Variance Targeting (1,500-2,500)
  ✅ 2% Outlier Injection
  ✅ Real-time Risk Assessment
  ✅ Enhanced Visual Feedback
  
File Organization:
  mimic_data/
    ├── mimicSessions/   ← Auto-clicker exports (F5/F6)
    ├── butterfly/       ← Human training data
    ├── jitter/          ← Human training data
    ├── normal/          ← Human training data
    ├── mixed/           ← Human training data
    └── sessions.json    ← Session history database
  
Controls:
  F4  - Toggle On/Off          F9  - Toggle Enhanced Mode
  F5  - Export TXT Stats       F10 - Mini Mode
  F6  - Export CSV             ← → - Navigate Pages
  F7  - Start/Stop Training    Enter - Quick Toggle (Disabled)
  F8  - Export Training Data   MB1 - Click (Hold)
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
from tkinter import ttk, messagebox
import os
import csv
import json

import win32api
import win32con
from pynput import mouse
# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    """Global configuration with realistic anti-cheat thresholds"""
    
    # Relaxed CPS limits (allow spikes)
    ABSOLUTE_MIN_DELAY_MS = 65   # 15.4 CPS spike allowed
    ABSOLUTE_MAX_DELAY_MS = 400  # Extended pauses for realism
    SUSTAINED_CPS_CAP = 12       # Average shouldn't sustain >12
    
    # Enhanced Mode has wider range
    ENHANCED_MIN_DELAY_MS = 60   # 16.7 CPS burst maximum
    ENHANCED_MAX_DELAY_MS = 450  # Longer pauses
    
    # Realistic variance targets
    ENHANCED_IDEAL_VARIANCE = 1500   # Minimum acceptable
    ENHANCED_TARGET_VARIANCE = 2200  # Optimal butterfly/jitter
    ENHANCED_MAX_VARIANCE = 3500     # Upper bound
    
    STANDARD_IDEAL_VARIANCE = 600    # Minimum acceptable
    STANDARD_TARGET_VARIANCE = 900   # Optimal normal clicking
    STANDARD_MAX_VARIANCE = 1500     # Upper bound
    
    # Anti-Detection Thresholds
    MIN_VARIANCE_THRESHOLD = 800
    PATTERN_CHECK_WINDOW = 20
    
    # Adaptive mode parameters
    TECHNIQUE_TRANSITION_MIN = 5   # Min clicks before switching
    TECHNIQUE_TRANSITION_MAX = 15  # Max clicks before switching
    
    # Enhanced Mode Parameters
    BURST_PROBABILITY = 0.20
    PAUSE_PROBABILITY = 0.02
    BURST_DURATION = (3, 8)
    PAUSE_DURATION_MS = (80, 120)
    
    # Outlier injection
    OUTLIER_PROBABILITY = 0.02     # 2% of clicks
    OUTLIER_COOLDOWN = (30, 80)    # Clicks between outliers
    
    # Mouse Button Constants
    VK_LBUTTON = 0x01   # Left mouse button - ACTIVE
    VK_XBUTTON2 = 0x06  # MB5 - Not used, keeping as backup
    
    # Training Thresholds
    TRAINING_MIN_CLICKS = 100
    TRAINING_RECOMMENDED_CLICKS = 200
    TRAINING_COMPLETE_CLICKS = 250
    
    # File Organization
    @staticmethod
    def get_training_data_path():
        """Get path to Desktop/mimic_data/"""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "mimic_data")
    
    @staticmethod
    def get_clicker_data_path():
        """Get path to Desktop/mimic_data/mimicSessions/"""
        return os.path.join(Config.get_training_data_path(), "mimicSessions")
    
    @staticmethod
    def get_sessions_file():
        """Get path to sessions database"""
        return os.path.join(Config.get_training_data_path(), "sessions.json")

# ═════════════════════════════════════════════════════════════════════════════
# RISK ASSESSMENT ENGINE
# ═════════════════════════════════════════════════════════════════════════════

class RiskAssessor:
    """Comprehensive risk assessment with realistic thresholds"""
    
    THRESHOLDS = {
        "enhanced": {
            "ideal_variance": 1500,
            "target_variance": 2200,
            "max_variance": 3500,
            "min_cps": 7,
            "target_cps": 10,
            "max_cps": 13,
            "spike_cps": 15,
            "min_std_dev": 35,
            "target_std_dev": 45
        },
        "standard": {
            "ideal_variance": 600,
            "target_variance": 900,
            "max_variance": 1500,
            "min_cps": 5,
            "target_cps": 8,
            "max_cps": 11,
            "spike_cps": 13,
            "min_std_dev": 25,
            "target_std_dev": 30
        }
    }
    
    @staticmethod
    def assess(stats):
        """Get comprehensive risk assessment with 0-100 scoring"""
        mode_key = "enhanced" if stats.get('enhanced_mode', True) else "standard"
        thresholds = RiskAssessor.THRESHOLDS[mode_key]
        
        # Extract metrics
        variance = stats.get('variance', 0)
        max_cps = stats.get('max_cps', 0)
        avg_cps = stats.get('avg_cps', 0)
        std_dev = stats.get('std_dev', 0)
        pattern_breaks = stats.get('pattern_breaks', 0)
        total_clicks = stats.get('total', 1)
        
        score = 0
        issues = []
        recommendations = []
        
        # === VARIANCE CHECK (40 points) ===
        if variance >= thresholds['target_variance']:
            score += 40
        elif variance >= thresholds['ideal_variance']:
            score += 25
            gap = int((thresholds['target_variance'] / variance - 1) * 100)
            recommendations.append(f"Increase variance by +{gap}% to reach {thresholds['target_variance']}")
        else:
            score += 10
            issues.append(f"Variance critically low ({int(variance)} vs {thresholds['ideal_variance']} minimum)")
            gap = int((thresholds['target_variance'] / variance - 1) * 100)
            recommendations.append(f"⚠️ CRITICAL: Increase variance by +{gap}%")
        
        # === CPS SPIKE CHECK (25 points) ===
        if max_cps >= thresholds['spike_cps']:
            score += 25
        elif max_cps >= thresholds['max_cps']:
            score += 15
            recommendations.append(f"Allow higher CPS spikes (target: {thresholds['spike_cps']}+)")
        else:
            score += 5
            issues.append(f"No CPS spikes detected (max: {max_cps:.1f})")
            recommendations.append(f"Enable CPS spikes up to {thresholds['spike_cps']}-16")
        
        # === AVERAGE CPS (15 points) ===
        if thresholds['min_cps'] <= avg_cps <= thresholds['max_cps']:
            score += 15
        else:
            score += 5
            if avg_cps > thresholds['max_cps']:
                issues.append(f"Average CPS too high ({avg_cps:.1f})")
            else:
                issues.append(f"Average CPS too low ({avg_cps:.1f})")
        
        # === STANDARD DEVIATION (20 points) ===
        if std_dev >= thresholds['target_std_dev']:
            score += 20
        elif std_dev >= thresholds['min_std_dev']:
            score += 12
            recommendations.append(f"Increase std dev to {thresholds['target_std_dev']}ms")
        else:
            score += 5
            issues.append(f"Std dev too low ({std_dev:.1f}ms)")
            recommendations.append(f"Target std dev: {thresholds['target_std_dev']}ms")
        
        # === PATTERN BREAKS (bonus 10 points) ===
        pattern_ratio = pattern_breaks / (total_clicks / 20) if total_clicks > 20 else 0
        if pattern_ratio >= 0.8:
            score += 10
        elif pattern_ratio >= 0.5:
            score += 5
        
        # Determine risk level
        if score >= 80:
            risk = "LOW"
            color = "#4CAF50"
            status = "✅ SAFE - Anti-cheat compliant"
        elif score >= 50:
            risk = "MEDIUM"
            color = "#FFA500"
            status = "⚠️ ACCEPTABLE - Room for improvement"
        else:
            risk = "HIGH"
            color = "#f44336"
            status = "🚨 DANGEROUS - Easily detectable"
        
        return {
            "risk": risk,
            "score": score,
            "color": color,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "thresholds": thresholds
        }

# ═════════════════════════════════════════════════════════════════════════════
# ENHANCED RISK VISUALIZATION
# ═════════════════════════════════════════════════════════════════════════════

class RiskVisualization:
    """Enhanced risk display with color gradients and percentiles"""
    
    RISK_LEVELS = [
        {"min": 85, "label": "EXCELLENT", "color": "#00e676", "emoji": "🟢", "desc": "Indistinguishable"},
        {"min": 70, "label": "GOOD", "color": "#4CAF50", "emoji": "🟢", "desc": "Safe Range"},
        {"min": 55, "label": "ACCEPTABLE", "color": "#FFC107", "emoji": "🟡", "desc": "Acceptable"},
        {"min": 40, "label": "CAUTION", "color": "#FF9800", "emoji": "🟠", "desc": "Needs Improvement"},
        {"min": 25, "label": "RISKY", "color": "#F44336", "emoji": "🔴", "desc": "High Detection Risk"},
        {"min": 0, "label": "CRITICAL", "color": "#b71c1c", "emoji": "🔴", "desc": "Extremely Dangerous"}
    ]
    
    @staticmethod
    def get_risk_level(score):
        """Get risk level from score 0-100"""
        for level in RiskVisualization.RISK_LEVELS:
            if score >= level["min"]:
                return level
        return RiskVisualization.RISK_LEVELS[-1]  # Critical
# ═════════════════════════════════════════════════════════════════════════════
# ADAPTIVE MIXED MODE CLICKER ENGINE (CLICKING LOGIC PRESERVED)
# ═════════════════════════════════════════════════════════════════════════════

class AdaptiveClickerEngine:
    """Mixed mode engine - blends butterfly/jitter/normal techniques"""
    
    def __init__(self, enhanced_mode=True):
        """Initialize adaptive engine"""
        self.enhanced_mode = enhanced_mode
        self.total_clicks = 0
        self.session_start = datetime.now()
        self.combat_start = None
        self.click_history = deque(maxlen=50)
        self.recent_click_times = deque(maxlen=20)
        self.all_delays = []
        
        # User baseline randomization
        self.user_baseline = random.uniform(0.88, 1.12)
        
        # Rhythm and drift tracking
        self.rhythm_phase = 0.0
        self.drift = 0.0
        
        self.consecutive_clicks = 0
        self.variance_adjustment = 0.15
        self.last_variance_check = datetime.now()
        
        # Pattern detection counters
        self.pattern_breaks = 0
        self.variance_adjustments = 0
        
        # Enhanced mode mechanics
        self.in_burst_mode = False
        self.burst_clicks_remaining = 0
        self.pause_until = None
        self.burst_count = 0
        self.pause_count = 0
        
        # Adaptive technique state
        self.current_technique = "normal"
        self.technique_duration = 0
        self.next_transition = random.randint(
            Config.TECHNIQUE_TRANSITION_MIN,
            Config.TECHNIQUE_TRANSITION_MAX
        )
        
        # Outlier injection
        self.outlier_cooldown = 0
        self.outlier_count = 0
        
        # Active time tracking
        self.total_clicking_time = 0.0
        self.click_session_start = None
        self.is_actively_clicking = False
        
        # CPS history for graphing
        self.cps_history = deque(maxlen=60)
        self.cps_timestamps = deque(maxlen=60)
    
    def start_clicking(self):
        """Session re-randomization for diversity"""
        if not self.is_actively_clicking:
            self.is_actively_clicking = True
            self.click_session_start = time.time()
            
            # Re-randomize parameters each session
            self.user_baseline = random.uniform(0.88, 1.12)
            self.drift = random.uniform(-0.15, 0.15)
            self.rhythm_phase = random.uniform(0, 2 * math.pi)
            
            # Random startup delay (reaction time simulation)
            startup_delay = abs(random.gauss(0.180, 0.045))  # 180ms ±45ms
            time.sleep(startup_delay)
    
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
        """Box-Muller transform for Gaussian distribution"""
        u1, u2 = random.random(), random.random()
        rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)
        return mean + std_dev * rand_std_normal
    
    def weibull_random(self, scale, shape):
        """Weibull distribution for varied timing"""
        u = random.random()
        return scale * ((-math.log(1 - u)) ** (1 / shape))
    
    def check_cps(self):
        """Allow spikes, prevent sustained high CPS"""
        current_time = time.time()
        
        # Clean old entries
        while self.recent_click_times and current_time - self.recent_click_times[0] > 5.0:
            self.recent_click_times.popleft()
        
        if len(self.recent_click_times) >= 2:
            # Recent CPS (last 1 second)
            recent_1s = [t for t in self.recent_click_times if current_time - t <= 1.0]
            recent_cps = len(recent_1s)
            
            # Average CPS (last 5 seconds)
            time_span = current_time - self.recent_click_times[0]
            avg_cps = len(self.recent_click_times) / time_span if time_span > 0 else 0
            
            # Allow short bursts above 12 CPS
            if recent_cps >= 16:  # Extreme spike
                return 0.08
            
            # Prevent sustained >12 CPS average
            if avg_cps > Config.SUSTAINED_CPS_CAP:
                return 0.05
        
        return 0
    
    def calculate_variance(self):
        """Rolling window variance"""
        if len(self.click_history) < 10:
            return 200
        recent = list(self.click_history)[-30:] if len(self.click_history) >= 30 else list(self.click_history)
        mean = sum(recent) / len(recent)
        variance = sum((x - mean) ** 2 for x in recent) / len(recent)
        return variance
    
    def calculate_overall_variance(self):
        """Total session variance"""
        if len(self.all_delays) < 20:
            return 200
        mean = sum(self.all_delays) / len(self.all_delays)
        variance = sum((x - mean) ** 2 for x in self.all_delays) / len(self.all_delays)
        return variance
    
    def calculate_std_dev(self):
        """Standard deviation"""
        variance = self.calculate_overall_variance()
        return math.sqrt(variance)
    
    def check_variance(self):
        """Dynamic variance adjustment every 10s"""
        if (datetime.now() - self.last_variance_check).total_seconds() < 10:
            return
        
        if self.enhanced_mode and len(self.all_delays) >= 50:
            variance = self.calculate_overall_variance()
        elif len(self.click_history) >= 15:
            variance = self.calculate_variance()
        else:
            return
        
        # Adaptive thresholds based on mode
        target_low = 1200 if self.enhanced_mode else 500
        target_mid = 1800 if self.enhanced_mode else 800
        target_high = 2500 if self.enhanced_mode else 1200
        
        if variance < target_low:
            self.variance_adjustment = random.uniform(0.40, 0.60) if self.enhanced_mode else random.uniform(0.30, 0.45)
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
        """Burst mode trigger"""
        if not self.in_burst_mode and self.consecutive_clicks > 5:
            if random.random() < Config.BURST_PROBABILITY:
                self.in_burst_mode = True
                self.burst_clicks_remaining = random.randint(*Config.BURST_DURATION)
                self.burst_count += 1
                return True
        return False
    
    def trigger_pause_mode(self):
        """Pause mode trigger"""
        if not self.in_burst_mode and self.consecutive_clicks > 10:
            if random.random() < Config.PAUSE_PROBABILITY:
                pause_duration = random.uniform(*Config.PAUSE_DURATION_MS) / 1000.0
                self.pause_until = time.time() + pause_duration
                self.pause_count += 1
                return True
        return False
    
    def select_technique(self):
        """Dynamically choose clicking technique"""
        self.technique_duration += 1
        
        # Natural transitions every 5-15 clicks
        if self.technique_duration >= self.next_transition:
            # Weight towards butterfly (highest variance)
            weights = {
                "butterfly": 0.40,  # 40% butterfly
                "jitter": 0.35,     # 35% jitter
                "normal": 0.25      # 25% normal
            }
            self.current_technique = random.choices(
                list(weights.keys()),
                weights=list(weights.values())
            )[0]
            self.technique_duration = 0
            self.next_transition = random.randint(
                Config.TECHNIQUE_TRANSITION_MIN,
                Config.TECHNIQUE_TRANSITION_MAX
            )
        
        return self.current_technique
    
    def should_inject_outlier(self):
        """Statistical outlier injection (2% rate)"""
        if self.outlier_cooldown > 0:
            self.outlier_cooldown -= 1
            return None
        
        if random.random() > Config.OUTLIER_PROBABILITY:
            return None
        
        # Choose outlier type (weighted)
        outlier_type = random.choices(
            ["micro_pause", "panic_burst", "dead_click"],
            weights=[0.70, 0.20, 0.10]
        )[0]
        
        self.outlier_cooldown = random.randint(*Config.OUTLIER_COOLDOWN)
        self.outlier_count += 1
        
        return outlier_type
    
    def calculate_delay(self):
        """Adaptive delay calculation with mixed techniques"""
        
        # Check for outlier injection
        outlier = self.should_inject_outlier()
        if outlier == "micro_pause":
            final = random.uniform(200, 350)
            self.click_history.append(final)
            self.all_delays.append(final)
            return final
        elif outlier == "dead_click":
            final = random.uniform(500, 800)
            self.click_history.append(final)
            self.all_delays.append(final)
            return final
        # panic_burst handled by returning very low delay
        
        # Enhanced mode pause handling
        if self.enhanced_mode:
            if self.pause_until and time.time() < self.pause_until:
                remaining = (self.pause_until - time.time()) * 1000
                self.pause_until = None
                return max(Config.ENHANCED_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, remaining))
            if self.trigger_pause_mode():
                return random.uniform(*Config.PAUSE_DURATION_MS)
            if not self.in_burst_mode:
                self.trigger_burst_mode()
        
        # Burst mode handling
        if self.enhanced_mode and self.in_burst_mode:
            self.burst_clicks_remaining -= 1
            if self.burst_clicks_remaining <= 0:
                self.in_burst_mode = False
            base = abs(self.gaussian_random(55, 12))
            base *= random.uniform(0.85, 1.15)
            final = max(Config.ENHANCED_MIN_DELAY_MS, min(110, base))
            self.click_history.append(final)
            self.all_delays.append(final)
            return final
        
        # Technique-based delay calculation
        technique = self.select_technique()
        
        if technique == "butterfly":
            # High variance, burst-prone, wide spread
            if random.random() < 0.7:
                base = abs(self.gaussian_random(85, 35))
            else:
                base = self.weibull_random(80, 1.8)
            
            # Butterfly clicks have more variation
            base *= random.uniform(0.70, 1.30)
            
            # Panic burst for outlier
            if outlier == "panic_burst":
                base *= 0.55  # Very fast
        
        elif technique == "jitter":
            # Medium variance, sustained, consistent
            if random.random() < 0.7:
                base = abs(self.gaussian_random(105, 22))
            else:
                base = self.weibull_random(100, 2.0)
            
            base *= random.uniform(0.82, 1.18)
        
        elif technique == "normal":
            # Lower variance, rhythmic
            if random.random() < 0.7:
                base = abs(self.gaussian_random(120, 18))
            else:
                base = self.weibull_random(115, 2.5)
            
            base *= random.uniform(0.90, 1.10)
        
        # User baseline multiplier
        base *= self.user_baseline
        
        # Consecutive click fatigue
        if self.consecutive_clicks < 3:
            base *= random.uniform(1.05, 1.20)
        elif self.consecutive_clicks < 8:
            base *= random.uniform(0.92, 1.08)
        else:
            base *= random.uniform(0.88, 0.98)
        
        # Drift accumulation
        drift_amount = 0.010 if self.enhanced_mode else 0.006
        self.drift += random.uniform(-drift_amount, drift_amount)
        drift_limit = 0.40 if self.enhanced_mode else 0.28
        self.drift = max(-drift_limit, min(drift_limit, self.drift))
        base *= (1.0 + self.drift)
        
        # Rhythm oscillation
        self.rhythm_phase = (self.rhythm_phase + random.uniform(0.20, 0.60)) % (2 * math.pi)
        rhythm_amount = 25 if self.enhanced_mode else 18
        base += math.sin(self.rhythm_phase) * rhythm_amount
        
        # Variance adjustment
        base *= (1.0 + self.variance_adjustment)
        
        # Random noise
        noise_range = 32 if self.enhanced_mode else 24
        base += random.randint(-noise_range, noise_range + 1)
        
        # Clamp to relaxed limits (allow 15-16 CPS spikes)
        if self.enhanced_mode:
            final = max(Config.ENHANCED_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, base))
        else:
            final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, base))
        
        # Pattern break detection
        if len(self.click_history) >= Config.PATTERN_CHECK_WINDOW:
            recent = list(self.click_history)[-Config.PATTERN_CHECK_WINDOW:]
            mean = sum(recent) / len(recent)
            variance = sum((x - mean) ** 2 for x in recent) / len(recent)
            threshold = 400 if self.enhanced_mode else 250
            multiplier_range = (0.55, 1.45) if self.enhanced_mode else (0.65, 1.35)
            if variance < threshold:
                final *= random.uniform(*multiplier_range)
                if self.enhanced_mode:
                    final = max(Config.ENHANCED_MIN_DELAY_MS, min(Config.ENHANCED_MAX_DELAY_MS, final))
                else:
                    final = max(Config.ABSOLUTE_MIN_DELAY_MS, min(Config.ABSOLUTE_MAX_DELAY_MS, final))
                self.pattern_breaks += 1
        
        self.click_history.append(final)
        self.all_delays.append(final)
        return final
    
    def click(self):
        """Execute click with realistic timing"""
        if self.combat_start is None:
            self.combat_start = datetime.now()
        
        # Safety check
        safety = self.check_cps()
        if safety > 0:
            time.sleep(safety)
        
        # Variance check
        self.check_variance()
        
        # Calculate delay
        delay_ms = self.calculate_delay()
        
        # Mouse button press with realistic hold time
        pressure_ms = abs(self.gaussian_random(26, 8))
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(pressure_ms / 1000.0)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        
        # Update tracking
        self.recent_click_times.append(time.time())
        self.total_clicks += 1
        self.consecutive_clicks += 1
        
        # Update CPS history
        current_cps = self.get_current_cps()
        self.cps_history.append(current_cps)
        self.cps_timestamps.append(time.time())
        
        # Delay until next click
        time.sleep(delay_ms / 1000.0)
    
    def get_current_cps(self):
        """Real-time CPS calculation"""
        if len(self.click_history) < 5:
            return 0.0
        recent = list(self.click_history)[-10:]
        avg_delay = sum(recent) / len(recent)
        return 1000.0 / avg_delay
    
    def get_detailed_stats(self):
        """Complete statistics with all metrics"""
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
            "std_dev": math.sqrt(overall_variance),
            "pattern_breaks": self.pattern_breaks,
            "variance_adjustments": self.variance_adjustments,
            "burst_count": self.burst_count,
            "pause_count": self.pause_count,
            "outlier_count": self.outlier_count,
            "session_duration": session_duration,
            "clicking_duration": clicking_duration,
            "idle_time": session_duration - clicking_duration,
            "p10_delay": p10,
            "p50_delay": p50,
            "p90_delay": p90,
            "min_delay": min(delays),
            "max_delay": max(delays),
            "avg_delay": avg_delay,
            "enhanced_mode": self.enhanced_mode,
            "current_technique": self.current_technique
        }
    
    def export_to_csv(self, filename):
        """Export click data to CSV with UTF-8 encoding"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(['Click_Number', 'Delay_MS', 'CPS', 'Timestamp'])
                
                for i, delay in enumerate(self.all_delays, 1):
                    cps = 1000.0 / delay if delay > 0 else 0
                    writer.writerow([i, f"{delay:.2f}", f"{cps:.2f}", datetime.now().isoformat()])
            
            return True
        except Exception as e:
            print(f"[ERROR] CSV export failed: {e}")
            return False

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
# ═════════════════════════════════════════════════════════════════════════════
# HUMAN CLICK TRACKER - WITH SESSION INTEGRATION
# ═════════════════════════════════════════════════════════════════════════════

class HumanClickTracker:
    """Tracks legitimate human clicks for baseline analysis"""
    
    def __init__(self, session_manager):
        self.session_manager = session_manager
        self.is_tracking = False
        self.click_times = []
        self.click_delays = []
        self.session_start = None
        self.last_click_time = None
        self.total_clicks = 0
        self.training_type = "normal"
    
    def start_tracking(self, training_type="normal"):
        self.is_tracking = True
        self.training_type = training_type
        self.session_start = datetime.now()
        self.click_times = []
        self.click_delays = []
        self.last_click_time = None
        self.total_clicks = 0
        print(f"\n[TRAINING MODE: {training_type.upper()}] Recording your clicks...\n")
    
    def stop_tracking(self):
        self.is_tracking = False
        print(f"\n[TRAINING MODE: {self.training_type.upper()}] Stopped recording.\n")
    
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
        
        return {
            "total": self.total_clicks,
            "valid_delays": len(delays),
            "avg_cps": 1000.0 / avg_delay,
            "min_cps": 1000.0 / max(delays),
            "max_cps": 1000.0 / min(delays),
            "median_cps": 1000.0 / p50,
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
        
        training_type = stats['training_type'].upper()
        
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
Session Duration:          {stats['session_duration']:.1f} seconds

Average CPS:               {stats['avg_cps']:.2f}
Median CPS:                {stats['median_cps']:.2f}

CPS STATISTICS
──────────────────────────────────────────────────────────────────────────────
Minimum CPS:               {stats['min_cps']:.2f}
Maximum CPS:               {stats['max_cps']:.2f}
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
        
        # Click-type specific analysis
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
        
        # Create organized filename
        training_type_safe = stats['training_type'].lower().replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        txt_filename = f"{training_type_safe}_baseline_{timestamp}.txt"
        csv_filename = f"{training_type_safe}_baseline_{timestamp}.csv"
        
        # Use Desktop path
        folder_path = os.path.join(Config.get_training_data_path(), training_type_safe)
        
        try:
            os.makedirs(folder_path, exist_ok=True)
            
            # Save TXT report with UTF-8 encoding
            txt_full_path = os.path.join(folder_path, txt_filename)
            with open(txt_full_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"[SUCCESS] TXT report saved to: {txt_full_path}\n")
            
            # Save CSV data with UTF-8 encoding
            csv_full_path = os.path.join(folder_path, csv_filename)
            self.export_to_csv(csv_full_path)
            print(f"[SUCCESS] CSV data saved to: {csv_full_path}\n")
            
            # Add to session manager
            self.session_manager.add_training_session(stats, txt_full_path)
            
            messagebox.showinfo("Export Successful", f"Training data exported!\n\n📁 {folder_path}")
        
        except Exception as e:
            print(f"[ERROR] Export failed: {e}\n")
            messagebox.showerror("Export Failed", f"Could not save files:\n{e}")

# ═════════════════════════════════════════════════════════════════════════════
# VISUALIZATION COMPONENTS
# ═════════════════════════════════════════════════════════════════════════════

class CPSLineGraph:
    """Real-time CPS line graph visualization"""
    
    def __init__(self, parent, width=600, height=200):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0)
        self.width = width
        self.height = height
        self.padding = 40
    
    def draw_graph(self, cps_data, timestamps):
        """Draw CPS line graph"""
        self.canvas.delete("all")
        
        if len(cps_data) < 2:
            self.canvas.create_text(
                self.width // 2, self.height // 2,
                text="Waiting for data...",
                fill="#888888",
                font=("Arial", 10)
            )
            return
        
        # Calculate bounds
        current_time = time.time()
        time_window = 30  # 30 second window
        
        # Filter to last 30 seconds
        visible_data = []
        visible_times = []
        for i, t in enumerate(timestamps):
            if current_time - t <= time_window:
                visible_data.append(cps_data[i])
                visible_times.append(t)
        
        if len(visible_data) < 2:
            return
        
        max_cps = max(max(visible_data), 15)
        min_cps = 0
        
        # Draw axes
        self.canvas.create_line(
            self.padding, self.height - self.padding,
            self.width - 20, self.height - self.padding,
            fill="#333333", width=2
        )
        self.canvas.create_line(
            self.padding, self.padding,
            self.padding, self.height - self.padding,
            fill="#333333", width=2
        )
        
        # Draw horizontal grid lines and labels
        for i in range(0, int(max_cps) + 1, 3):
            y = self.height - self.padding - (i / max_cps) * (self.height - 2 * self.padding)
            self.canvas.create_line(
                self.padding, y,
                self.width - 20, y,
                fill="#2a2a2a", dash=(2, 4)
            )
            self.canvas.create_text(
                self.padding - 10, y,
                text=str(i),
                fill="#666666",
                font=("Arial", 8),
                anchor="e"
            )
        
        # Draw optimal zone (7-12 CPS)
        y_7 = self.height - self.padding - (7 / max_cps) * (self.height - 2 * self.padding)
        y_12 = self.height - self.padding - (12 / max_cps) * (self.height - 2 * self.padding)
        
        self.canvas.create_rectangle(
            self.padding, y_12,
            self.width - 20, y_7,
            fill="#1b5e20", outline="", stipple="gray50"
        )
        
        # Draw CPS line
        points = []
        for i, cps in enumerate(visible_data):
            x = self.padding + (i / (len(visible_data) - 1)) * (self.width - self.padding - 20)
            y = self.height - self.padding - (cps / max_cps) * (self.height - 2 * self.padding)
            points.extend([x, y])
        
        if len(points) >= 4:
            self.canvas.create_line(
                points,
                fill="#4CAF50",
                width=2,
                smooth=True
            )
        
        # Draw current CPS indicator
        if visible_data:
            current_cps = visible_data[-1]
            self.canvas.create_text(
                self.width - 30, self.padding,
                text=f"{current_cps:.1f}",
                fill="#4CAF50",
                font=("Arial", 12, "bold"),
                anchor="ne"
            )
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)

class HistogramCanvas:
    """Click delay distribution histogram"""
    
    def __init__(self, parent, width=600, height=250):
        self.canvas = tk.Canvas(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0)
        self.width = width
        self.height = height
        self.padding = 40
    
    def draw_histogram(self, delays, mean, std_dev, enhanced_mode):
        """Draw delay distribution histogram"""
        self.canvas.delete("all")
        
        if len(delays) < 10:
            self.canvas.create_text(
                self.width // 2, self.height // 2,
                text="Need more clicks...",
                fill="#888888",
                font=("Arial", 10)
            )
            return
        
        # Create bins
        min_delay = min(delays)
        max_delay = max(delays)
        num_bins = 20
        bin_width = (max_delay - min_delay) / num_bins
        
        bins = [0] * num_bins
        for delay in delays:
            bin_idx = min(int((delay - min_delay) / bin_width), num_bins - 1)
            bins[bin_idx] += 1
        
        max_count = max(bins)
        
        # Draw axes
        self.canvas.create_line(
            self.padding, self.height - self.padding,
            self.width - 20, self.height - self.padding,
            fill="#333333", width=2
        )
        self.canvas.create_line(
            self.padding, self.padding,
            self.padding, self.height - self.padding,
            fill="#333333", width=2
        )
        
        # Danger zones
        ideal_min = 60 if enhanced_mode else 80
        ideal_max = 150 if enhanced_mode else 130
        
        # Draw bars
        bar_width = (self.width - self.padding - 20) / num_bins
        
        for i, count in enumerate(bins):
            if count == 0:
                continue
            
            bin_delay = min_delay + (i + 0.5) * bin_width
            
            # Color based on delay range
            if ideal_min <= bin_delay <= ideal_max:
                color = "#4CAF50"  # Optimal
            else:
                color = "#FFA500"  # Acceptable
            
            x1 = self.padding + i * bar_width
            y1 = self.height - self.padding - (count / max_count) * (self.height - 2 * self.padding)
            x2 = x1 + bar_width - 2
            y2 = self.height - self.padding
            
            self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill=color, outline=""
            )
        
        # Draw mean line
        mean_x = self.padding + ((mean - min_delay) / (max_delay - min_delay)) * (self.width - self.padding - 20)
        self.canvas.create_line(
            mean_x, self.padding,
            mean_x, self.height - self.padding,
            fill="#4CAF50", width=2, dash=(4, 4)
        )
        
        # Labels
        self.canvas.create_text(
            self.padding, self.height - self.padding + 20,
            text=f"{min_delay:.0f}ms",
            fill="#666666",
            font=("Arial", 8)
        )
        self.canvas.create_text(
            self.width - 20, self.height - self.padding + 20,
            text=f"{max_delay:.0f}ms",
            fill="#666666",
            font=("Arial", 8)
        )
    
    def pack(self, **kwargs):
        self.canvas.pack(**kwargs)
# ═════════════════════════════════════════════════════════════════════════════
# MAIN GUI APPLICATION (GHOST STEALTH REBRAND)
# ═════════════════════════════════════════════════════════════════════════════

class MinecraftAutoClickerGUI:
    """Mimic - Statistical Ghost Clicker GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mimic v3.7")
        self.root.geometry("650x750")
        self.root.resizable(False, False)
        
        # Ghost Stealth color scheme
        self.bgcolor = "#0D0D0D"           # Pure black background
        self.panel_color = "#1E1E1E"       # Charcoal panels
        self.header_color = "#1A1A1A"      # Slightly lighter header
        self.fg_color = "#F5F5F5"          # White text
        self.accent_color = "#4CAF50"      # Green accent
        self.secondary_color = "#7C4DFF"   # Purple for stats
        self.tech_accent = "#00E5FF"       # Cyan tech elements
        self.button_color = "#3d3d3d"
        self.button_hover = "#4d4d4d"
        self.inactive_color = "#888888"
        self.training_color = "#FF9800"
        self.enhanced_color = "#2196F3"
        
        # Tab colors
        self.active_tab = "#3d3d3d"
        self.inactive_tab = "#2d2d2d"
        
        self.root.configure(bg=self.bgcolor)
        
        # State
        self.active = False
        self.clicking = False
        self.enhanced_mode = True
        self.engine = None
        self.current_page = 0
        self.pages = []
        
        self.physical_left_held = False  # Track physical button state
        self.mouse_listener = mouse.Listener(on_click=self.on_physical_click)
        self.mouse_listener.start()
    
        # Session management
        self.session_manager = SessionManager()
        self.human_tracker = HumanClickTracker(self.session_manager)
        
        # Setup
        self.setup_ui()
        self.setup_hotkeys()
        self.start_threads()
        self.update_display()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    def on_physical_click(self, x, y, button, pressed, injected=False):
        """Listener for PHYSICAL mouse events only"""
        # Ignore synthetic clicks from our autoclicker
        if injected:
            return
        
        # Only track PHYSICAL left button
        if button == mouse.Button.left:
            self.physical_left_held = pressed
            # Uncomment for debugging:
            # if self.active:
            #     print(f"[PHYSICAL] Left: {'DOWN' if pressed else 'UP'}")

    
    def setup_ui(self):
        """Build complete UI with Ghost Stealth theme"""
        
        # ═══ HEADER ═══
        header_frame = tk.Frame(self.root, bg=self.header_color, height=125)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="⚙️ Mimic v3.7",
            font=("Arial", 17, "bold"),
            bg=self.header_color,
            fg=self.fg_color
        )
        title.pack(pady=(15, 3))
        
        subtitle = tk.Label(
            header_frame,
            text="Adaptive Intelligence • Statistical Mimicry",
            font=("Arial", 8),
            bg=self.header_color,
            fg="#888888"
        )
        subtitle.pack(pady=(0, 4))
        
        self.mode_indicator = tk.Label(
            header_frame,
            text="✨ Enhanced Adaptive Mode",
            font=("Arial", 8, "italic"),
            bg=self.header_color,
            fg=self.enhanced_color
        )
        self.mode_indicator.pack(pady=(0, 4))
        
        self.path_indicator = tk.Label(
            header_frame,
            text="📁 Desktop/mimic_data",
            font=("Arial", 7),
            bg=self.header_color,
            fg="#666666"
        )
        self.path_indicator.pack(pady=(0, 5))
        
        self.status_indicator = tk.Label(
            header_frame,
            text="⚫ INACTIVE",
            font=("Arial", 10, "bold"),
            bg=self.header_color,
            fg=self.inactive_color
        )
        self.status_indicator.pack(pady=(0, 10))
        
        # ═══ TAB NAVIGATION ═══
        tab_frame = tk.Frame(self.root, bg=self.bgcolor)
        tab_frame.pack(fill=tk.X, padx=25, pady=(0, 8))
        
        self.tab_buttons = []
        tab_names = ["Dashboard", "Settings", "Analytics", "Graphs", "Training", "History", "Compare"]
        
        for i, name in enumerate(tab_names):
            btn = tk.Button(
                tab_frame,
                text=name,
                font=("Arial", 8, "bold"),
                bg=self.inactive_tab,
                fg=self.fg_color,
                activebackground=self.button_hover,
                activeforeground=self.fg_color,
                relief=tk.FLAT,
                cursor="hand2",
                command=lambda idx=i: self.switch_page(idx)
            )
            btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=1)
            self.tab_buttons.append(btn)
        
        # ═══ CONTENT CONTAINER ═══
        self.content_frame = tk.Frame(self.root, bg=self.bgcolor)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=25)
        
        # Create all pages
        self.create_page_dashboard()
        self.create_page_settings()
        self.create_page_analytics()
        self.create_page_graphs()
        self.create_page_training()
        self.create_page_history()
        self.create_page_differential()
        
        # ═══ NAVIGATION FOOTER ═══
        nav_frame = tk.Frame(self.root, bg=self.bgcolor)
        nav_frame.pack(fill=tk.X, padx=25, pady=12)
        
        self.prev_btn = tk.Button(
            nav_frame,
            text="◄ Prev",
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
            text="1 / 7",
            font=("Arial", 10, "bold"),
            bg=self.bgcolor,
            fg="#888888"
        )
        self.page_indicator.pack(side=tk.LEFT, expand=True)
        
        self.next_btn = tk.Button(
            nav_frame,
            text="Next ►",
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
        """Enhanced dashboard with visual risk indicators"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Status panel
        status_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        status_panel.pack(fill=tk.X, pady=(0, 8))
        
        status_inner = tk.Frame(status_panel, bg=self.panel_color)
        status_inner.pack(pady=12)
        
        self.click_status = tk.Label(
            status_inner,
            text="Ready to activate",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg="#888888"
        )
        self.click_status.pack()
        
        self.session_timer = tk.Label(
            status_inner,
            text="⏱️ 0:00",
            font=("Arial", 10),
            bg=self.panel_color,
            fg="#888888"
        )
        self.session_timer.pack(pady=(5, 0))
        
        # Quick stats cards (2x3 grid)
        cards_frame = tk.Frame(page, bg=self.bgcolor)
        cards_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # Row 1
        row1 = tk.Frame(cards_frame, bg=self.bgcolor)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        self.create_stat_card(row1, "Total Clicks", "0", "total_clicks_card", 0)
        self.create_stat_card(row1, "Current CPS", "--", "current_cps_card", 1)
        self.create_stat_card(row1, "Average CPS", "--", "avg_cps_card", 2)
        
        # Row 2
        row2 = tk.Frame(cards_frame, bg=self.bgcolor)
        row2.pack(fill=tk.X)
        
        self.create_stat_card(row2, "Variance", "--", "variance_card", 0)
        self.create_stat_card(row2, "Std Dev", "--", "std_dev_card", 1)
        self.create_stat_card(row2, "Risk Level", "--", "risk_card", 2)
        
        # Enhanced risk visualization panel
        risk_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        risk_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            risk_panel,
            text="🎯 Detection Risk Assessment",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        # Container for risk score display
        self.risk_display_container = tk.Frame(risk_panel, bg=self.panel_color)
        self.risk_display_container.pack(pady=10)
        
        # Component indicators
        component_frame = tk.Frame(risk_panel, bg=self.panel_color)
        component_frame.pack(pady=(0, 10), padx=20, fill=tk.X)
        
        self.variance_health = tk.Label(
            component_frame,
            text="⚪ Variance: --",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w"
        )
        self.variance_health.pack(fill=tk.X, pady=2)
        
        self.cps_health = tk.Label(
            component_frame,
            text="⚪ CPS Range: --",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w"
        )
        self.cps_health.pack(fill=tk.X, pady=2)
        
        self.pattern_health = tk.Label(
            component_frame,
            text="⚪ Pattern Breaks: --",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w"
        )
        self.pattern_health.pack(fill=tk.X, pady=2)
        
        # Quick actions panel
        actions_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        actions_panel.pack(fill=tk.X)
        
        tk.Label(
            actions_panel,
            text="Quick Actions",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        btn_grid = tk.Frame(actions_panel, bg=self.panel_color)
        btn_grid.pack(pady=10)
        
        # Button row 1
        btn_row1 = tk.Frame(btn_grid, bg=self.panel_color)
        btn_row1.pack()
        
        self.toggle_btn = tk.Button(
            btn_row1,
            text="▶ Activate (F4)",
            font=("Arial", 9, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#45a049",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_active,
            width=18,
            height=2
        )
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        export_btn = tk.Button(
            btn_row1,
            text="📊 Export Stats (F5)",
            font=("Arial", 9),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_stats,
            width=18,
            height=2
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Button row 2
        btn_row2 = tk.Frame(btn_grid, bg=self.panel_color)
        btn_row2.pack(pady=(5, 0))
        
        csv_btn = tk.Button(
            btn_row2,
            text="💾 Export CSV (F6)",
            font=("Arial", 9),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_csv,
            width=18,
            height=2
        )
        csv_btn.pack(side=tk.LEFT, padx=5)
        
        mini_btn = tk.Button(
            btn_row2,
            text="🪟 Mini Mode (F10)",
            font=("Arial", 9),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_mini_mode,
            width=18,
            height=2
        )
        mini_btn.pack(side=tk.LEFT, padx=5)
        
        tk.Label(actions_panel, text="", bg=self.panel_color, height=1).pack()
    
    def create_stat_card(self, parent, label, value, var_name, col):
        """Create a visual stat card"""
        card = tk.Frame(parent, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        card.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=3)
        
        tk.Label(
            card,
            text=label,
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(8, 2))
        
        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 14, "bold"),
            bg=self.panel_color,
            fg=self.accent_color
        )
        value_label.pack(pady=(0, 8))
        
        setattr(self, var_name, value_label)
    
    def create_page_settings(self):
        """Settings page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Create scrollable canvas
        canvas = tk.Canvas(page, bg=self.bgcolor, highlightthickness=0, height=510)
        scrollbar = tk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bgcolor)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mode settings
        mode_panel = tk.Frame(scrollable_frame, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        mode_panel.pack(fill=tk.X, pady=(0, 8), padx=2)
        
        tk.Label(
            mode_panel,
            text="Clicking Mode",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        enhanced_frame = tk.Frame(mode_panel, bg=self.panel_color)
        enhanced_frame.pack(pady=8)
        
        self.enhanced_btn = tk.Button(
            enhanced_frame,
            text="✨ Toggle Enhanced Mode (F9)",
            font=("Arial", 10, "bold"),
            bg=self.enhanced_color,
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
            text="Status: ✅ Enabled • Adaptive Mixed Mode",
            font=("Arial", 9),
            bg=self.panel_color,
            fg=self.enhanced_color
        )
        self.enhanced_status.pack(pady=5)
        
        desc_text = "• Blends butterfly/jitter/normal techniques\n• Allows 15-16 CPS spikes\n• Target variance: 1,500-2,500"
        tk.Label(
            mode_panel,
            text=desc_text,
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888",
            justify=tk.CENTER
        ).pack(pady=(0, 12))
        
        # Export settings
        export_panel = tk.Frame(scrollable_frame, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        export_panel.pack(fill=tk.X, pady=(0, 8), padx=2)
        
        tk.Label(
            export_panel,
            text="📁 Export Settings",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        path_text = """All data saves to: Desktop/mimic_data/

Folder Structure:
  mimic_data/
    ├── mimicSessions/  ← Session exports (F5/F6)
    ├── butterfly/      ← Training data (F8)
    ├── jitter/         ← Training data (F8)
    ├── normal/         ← Training data (F8)
    ├── mixed/          ← Training data (F8)
    └── sessions.json   ← History database"""
        
        tk.Label(
            export_panel,
            text=path_text,
            font=("Courier", 7),
            bg=self.panel_color,
            fg="#888888",
            justify=tk.LEFT
        ).pack(pady=(0, 12), padx=10)
        
        # Controls panel
        controls_panel = tk.Frame(scrollable_frame, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        controls_panel.pack(fill=tk.X, padx=2)
        
        tk.Label(
            controls_panel,
            text="⌨️ Keyboard Controls",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        controls_grid = tk.Frame(controls_panel, bg=self.panel_color)
        controls_grid.pack(pady=8)
        
        controls = [
            ("F4", "Toggle On/Off"),
            ("LEFT CLICK", "Click (Hold)"),
            ("F5", "Export TXT"),
            ("F6", "Export CSV"),
            ("← →", "Switch Pages"),
            #("Enter", "Quick Toggle"), #DISABLED
            ("F7", "Train Start/Stop"),
            ("F8", "Export Baseline"),
            ("F9", "Toggle Enhanced"),
            ("F10", "Mini Mode")
        ]
        
        for key, action in controls:
            row = tk.Frame(controls_grid, bg=self.panel_color)
            row.pack(pady=2)
            
            tk.Label(
                row,
                text=f"[{key}]",
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
        
        tk.Label(controls_panel, text="", bg=self.panel_color, height=1).pack()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    def create_page_analytics(self):
        """Analytics page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Current session metrics
        current_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        current_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            current_panel,
            text="📊 Current Session Metrics",
            font=("Arial", 12, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        metrics_grid = tk.Frame(current_panel, bg=self.panel_color)
        metrics_grid.pack(pady=8, padx=20)
        
        self.create_metric_row(metrics_grid, "Detection Risk:", "risk_level", 0)
        self.create_metric_row(metrics_grid, "Risk Score:", "risk_score", 1)
        self.create_metric_row(metrics_grid, "Burst Events:", "burst_events", 2)
        self.create_metric_row(metrics_grid, "Pause Events:", "pause_events", 3)
        self.create_metric_row(metrics_grid, "Outlier Injections:", "outlier_count", 4)
        
        tk.Label(current_panel, text="", bg=self.panel_color, height=1).pack()
        
        # Session history
        history_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        history_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            history_panel,
            text="📜 Recent Sessions",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        history_frame = tk.Frame(history_panel, bg=self.panel_color)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        history_scrollbar = tk.Scrollbar(history_frame)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_text = tk.Text(
            history_frame,
            height=10,
            font=("Courier", 8),
            bg="#1a1a1a",
            fg="#cccccc",
            relief=tk.FLAT,
            wrap=tk.WORD,
            yscrollcommand=history_scrollbar.set
        )
        self.history_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.config(command=self.history_text.yview)
        
        self.history_text.insert("1.0", "No sessions yet. Start a session to see analytics.")
        self.history_text.config(state=tk.DISABLED)
        
        tk.Label(history_panel, text="", bg=self.panel_color, height=1).pack()
    
    def create_metric_row(self, parent, label_text, var_name, row):
        """Create metric row for analytics"""
        label = tk.Label(
            parent,
            text=f"{label_text}",
            font=("Arial", 10),
            bg=self.panel_color,
            fg="#cccccc",
            anchor="w",
            width=18
        )
        label.grid(row=row, column=0, pady=5, padx=10, sticky="w")
        
        value = tk.Label(
            parent,
            text="--",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg=self.accent_color,
            anchor="e",
            width=15
        )
        value.grid(row=row, column=1, pady=5, padx=10, sticky="e")
        
        setattr(self, var_name, value)
    
    def create_page_graphs(self):
        """Graphs page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # CPS Line Graph
        graph_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        graph_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            graph_panel,
            text="📈 Real-Time CPS (30s Rolling)",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        self.cps_graph = CPSLineGraph(graph_panel, width=560, height=200)
        self.cps_graph.pack(pady=5, padx=10)
        
        tk.Label(
            graph_panel,
            text="Green zone: Optimal 7-12 CPS",
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(0, 10))
        
        # Histogram
        histogram_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        histogram_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            histogram_panel,
            text="📊 Click Delay Distribution",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        self.histogram = HistogramCanvas(histogram_panel, width=560, height=240)
        self.histogram.pack(pady=5, padx=10)
        
        # Legend
        legend_frame = tk.Frame(histogram_panel, bg=self.panel_color)
        legend_frame.pack(pady=5)
        
        legend_items = [
            ("█", "#4CAF50", "Optimal"),
            ("█", "#FFA500", "Acceptable"),
            ("┃", "#4CAF50", "Mean")
        ]
        
        for symbol, color, text in legend_items:
            item = tk.Frame(legend_frame, bg=self.panel_color)
            item.pack(side=tk.LEFT, padx=10)
            
            tk.Label(
                item,
                text=symbol,
                fg=color,
                bg=self.panel_color,
                font=("Arial", 10, "bold")
            ).pack(side=tk.LEFT)
            
            tk.Label(
                item,
                text=text,
                fg="#888888",
                bg=self.panel_color,
                font=("Arial", 8)
            ).pack(side=tk.LEFT, padx=2)
        
        tk.Label(histogram_panel, text="", bg=self.panel_color, height=1).pack()
    
    def create_page_training(self):
        """Training page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Title
        title_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        title_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            title_panel,
            text="🎓 Human Baseline Training",
            font=("Arial", 13, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 5))
        
        tk.Label(
            title_panel,
            text="Record natural clicking patterns for AI analysis",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(0, 12))
        
        # Click type selector
        selector_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        selector_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            selector_panel,
            text="Select Click Type",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        button_frame = tk.Frame(selector_panel, bg=self.panel_color)
        button_frame.pack(pady=8)
        
        self.butterfly_btn = tk.Button(
            button_frame,
            text="🦋 Butterfly\n(2-finger)",
            font=("Arial", 9, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.select_training_type("butterfly"),
            width=16,
            height=3
        )
        self.butterfly_btn.grid(row=0, column=0, padx=5, pady=5)
        
        self.jitter_btn = tk.Button(
            button_frame,
            text="⚡ Jitter\n(wrist tension)",
            font=("Arial", 9, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.select_training_type("jitter"),
            width=16,
            height=3
        )
        self.jitter_btn.grid(row=0, column=1, padx=5, pady=5)
        
        self.normal_btn = tk.Button(
            button_frame,
            text="👆 Normal\n(single tap)",
            font=("Arial", 9, "bold"),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.select_training_type("normal"),
            width=16,
            height=3
        )
        self.normal_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.training_type_label = tk.Label(
            selector_panel,
            text="No type selected",
            font=("Arial", 10),
            bg=self.panel_color,
            fg="#888888"
        )
        self.training_type_label.pack(pady=(5, 12))
        
        # Training controls
        controls_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        controls_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            controls_panel,
            text="Training Controls",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 8))
        
        training_btn_frame = tk.Frame(controls_panel, bg=self.panel_color)
        training_btn_frame.pack(pady=8)
        
        self.train_start_btn = tk.Button(
            training_btn_frame,
            text="▶ Start Training (F7)",
            font=("Arial", 10, "bold"),
            bg=self.training_color,
            fg="white",
            activebackground="#ff9500",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.toggle_training_mode,
            width=20,
            height=2
        )
        self.train_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.train_export_btn = tk.Button(
            training_btn_frame,
            text="💾 Export Data (F8)",
            font=("Arial", 10),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.export_human_baseline,
            width=20,
            height=2
        )
        self.train_export_btn.pack(side=tk.LEFT, padx=5)
        
        self.training_progress = tk.Label(
            controls_panel,
            text="",
            font=("Arial", 8),
            bg=self.panel_color,
            fg="#888888"
        )
        self.training_progress.pack()
        
        self.training_status_label = tk.Label(
            controls_panel,
            text="Inactive - Select a type above",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#888888"
        )
        self.training_status_label.pack(pady=(5, 12))
        
        # Info panel
        info_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        info_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            info_panel,
            text="💡 Tips",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        tips = [
            "• Click naturally for 30+ seconds",
            "• Minimum: 100 clicks • Recommended: 200+",
            "• Complete: 250+ clicks",
            "• Files save to Desktop/mimic_data/",
            "• View history in History tab"
        ]
        
        for tip in tips:
            tk.Label(
                info_panel,
                text=tip,
                font=("Arial", 8),
                bg=self.panel_color,
                fg="#cccccc",
                anchor="w"
            ).pack(pady=2, padx=20, anchor="w")
        
        tk.Label(info_panel, text="", bg=self.panel_color, height=1).pack()
    
    def create_page_history(self):
        """History page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Title
        title_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        title_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            title_panel,
            text="📚 Training Session History",
            font=("Arial", 13, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 5))
        
        tk.Label(
            title_panel,
            text="View all recorded training sessions",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(0, 12))
        
        # Filter controls
        filter_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        filter_panel.pack(fill=tk.X, pady=(0, 8))
        
        filter_frame = tk.Frame(filter_panel, bg=self.panel_color)
        filter_frame.pack(pady=10)
        
        tk.Label(
            filter_frame,
            text="Filter by Type:",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#cccccc"
        ).pack(side=tk.LEFT, padx=5)
        
        self.history_filter = tk.StringVar(value="All")
        filter_options = ["All", "butterfly", "jitter", "normal", "mixed"]
        filter_menu = ttk.Combobox(
            filter_frame,
            textvariable=self.history_filter,
            values=filter_options,
            state="readonly",
            width=15
        )
        filter_menu.pack(side=tk.LEFT, padx=5)
        filter_menu.bind("<<ComboboxSelected>>", lambda e: self.update_history_list())
        
        refresh_btn = tk.Button(
            filter_frame,
            text="🔄 Refresh",
            font=("Arial", 9),
            bg=self.button_color,
            fg=self.fg_color,
            activebackground=self.button_hover,
            relief=tk.FLAT,
            cursor="hand2",
            command=self.update_history_list,
            width=10
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # Session list
        list_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        list_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            list_panel,
            text="Sessions",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        list_frame = tk.Frame(list_panel, bg=self.panel_color)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_list = tk.Text(
            list_frame,
            height=15,
            font=("Courier", 8),
            bg="#1a1a1a",
            fg="#cccccc",
            relief=tk.FLAT,
            wrap=tk.NONE,
            yscrollcommand=scrollbar.set
        )
        self.history_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_list.yview)
        
        # Action buttons
        action_frame = tk.Frame(list_panel, bg=self.panel_color)
        action_frame.pack(pady=10)
        
        compare_btn = tk.Button(
            action_frame,
            text="📊 Compare Sessions →",
            font=("Arial", 9, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#45a049",
            relief=tk.FLAT,
            cursor="hand2",
            command=lambda: self.switch_page(6),
            width=20
        )
        compare_btn.pack(pady=5)
        
        tk.Label(
            list_panel,
            text="💡 Tip: Use Compare tab to analyze human vs bot patterns",
            font=("Arial", 7),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(0, 10))
        
        self.update_history_list()
    
    def create_page_differential(self):
        """Differential analysis page"""
        page = tk.Frame(self.content_frame, bg=self.bgcolor)
        self.pages.append(page)
        
        # Title
        title_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        title_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            title_panel,
            text="🔬 Differential Analysis",
            font=("Arial", 13, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(12, 5))
        
        tk.Label(
            title_panel,
            text="Compare human training data vs bot performance",
            font=("Arial", 9),
            bg=self.panel_color,
            fg="#888888"
        ).pack(pady=(0, 12))
        
        # Session selectors
        selector_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        selector_panel.pack(fill=tk.X, pady=(0, 8))
        
        selector_inner = tk.Frame(selector_panel, bg=self.panel_color)
        selector_inner.pack(pady=12, padx=20)
        
        # Human session selector
        human_frame = tk.Frame(selector_inner, bg=self.panel_color)
        human_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            human_frame,
            text="Human Data:",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg="#4CAF50",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        self.human_session_var = tk.StringVar(value="Select training session...")
        self.human_session_menu = ttk.Combobox(
            human_frame,
            textvariable=self.human_session_var,
            state="readonly",
            width=40
        )
        self.human_session_menu.pack(side=tk.LEFT, padx=5)
        
        # Bot session selector
        bot_frame = tk.Frame(selector_inner, bg=self.panel_color)
        bot_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            bot_frame,
            text="Bot Data:",
            font=("Arial", 10, "bold"),
            bg=self.panel_color,
            fg="#2196F3",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        self.bot_session_var = tk.StringVar(value="Select clicker session...")
        self.bot_session_menu = ttk.Combobox(
            bot_frame,
            textvariable=self.bot_session_var,
            state="readonly",
            width=40
        )
        self.bot_session_menu.pack(side=tk.LEFT, padx=5)
        
        # Analyze button
        analyze_btn = tk.Button(
            selector_panel,
            text="🔍 ANALYZE",
            font=("Arial", 11, "bold"),
            bg=self.accent_color,
            fg="white",
            activebackground="#45a049",
            relief=tk.FLAT,
            cursor="hand2",
            command=self.run_differential_analysis,
            width=20,
            height=2
        )
        analyze_btn.pack(pady=(5, 12))
        
        # Results panel
        results_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        results_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            results_panel,
            text="Analysis Results",
            font=("Arial", 11, "bold"),
            bg=self.panel_color,
            fg=self.fg_color
        ).pack(pady=(10, 5))
        
        results_frame = tk.Frame(results_panel, bg=self.panel_color)
        results_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=8)
        
        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.diff_results = tk.Text(
            results_frame,
            height=16,
            font=("Courier", 8),
            bg="#1a1a1a",
            fg="#cccccc",
            relief=tk.FLAT,
            wrap=tk.WORD,
            yscrollcommand=scrollbar.set
        )
        self.diff_results.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.diff_results.yview)
        
        self.diff_results.insert("1.0", "Select human and bot sessions above, then click ANALYZE.\n\nThis will show:\n• CPS comparison\n• Variance gap analysis\n• Realism score (0-100)\n• Specific improvement recommendations")
        self.diff_results.config(state=tk.DISABLED)
        
        tk.Label(results_panel, text="", bg=self.panel_color, height=1).pack()
        
        self.update_differential_options()
    
    def update_history_list(self):
        """Update training session history list"""
        filter_type = self.history_filter.get()
        
        if filter_type == "All":
            sessions = self.session_manager.get_training_sessions()
        else:
            sessions = self.session_manager.get_training_sessions(filter_type)
        
        self.history_list.config(state=tk.NORMAL)
        self.history_list.delete("1.0", tk.END)
        
        if not sessions:
            self.history_list.insert("1.0", "No training sessions found.\n\nStart a training session (F7→F8) to see it here.")
        else:
            header = f"{'Date/Time':<20} {'Type':<12} {'Clicks':<8} {'CPS':<8} {'Variance':<10}\n"
            self.history_list.insert("1.0", header)
            self.history_list.insert("2.0", "-" * 70 + "\n")
            
            for session in reversed(sessions[-20:]):
                timestamp = session.get('timestamp', 'Unknown')
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%m/%d %H:%M:%S")
                except:
                    time_str = timestamp[:19]
                
                type_str = session.get('type', 'unknown')
                clicks = session.get('total_clicks', 0)
                cps = session.get('avg_cps', 0)
                variance = session.get('variance', 0)
                
                line = f"{time_str:<20} {type_str:<12} {clicks:<8} {cps:<8.2f} {int(variance):<10}\n"
                self.history_list.insert(tk.END, line)
        
        self.history_list.config(state=tk.DISABLED)
    
    def update_differential_options(self):
        """Update dropdown options for differential analysis"""
        training_sessions = self.session_manager.get_training_sessions()
        training_options = []
        
        for i, session in enumerate(reversed(training_sessions[-10:])):
            timestamp = session.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = timestamp[:16]
            
            type_str = session.get('type', 'unknown')
            clicks = session.get('total_clicks', 0)
            variance = int(session.get('variance', 0))
            
            option = f"{time_str} | {type_str} | {clicks} clicks | Var:{variance}"
            training_options.append(option)
        
        if training_options:
            self.human_session_menu['values'] = training_options
        else:
            self.human_session_menu['values'] = ["No training sessions available"]
        
        clicker_sessions = self.session_manager.get_clicker_sessions()
        clicker_options = []
        
        for i, session in enumerate(reversed(clicker_sessions[-10:])):
            timestamp = session.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = timestamp[:16]
            
            mode = session.get('mode', 'unknown')
            clicks = session.get('total_clicks', 0)
            variance = int(session.get('variance', 0))
            risk = session.get('risk', 'N/A')
            
            option = f"{time_str} | {mode} | {clicks} clicks | Var:{variance} | {risk}"
            clicker_options.append(option)
        
        if clicker_options:
            self.bot_session_menu['values'] = clicker_options
        else:
            self.bot_session_menu['values'] = ["No clicker sessions available"]
    
    def run_differential_analysis(self):
        """Perform differential analysis between human and bot sessions"""
        human_selection = self.human_session_var.get()
        bot_selection = self.bot_session_var.get()
        
        if "Select" in human_selection or "No" in human_selection:
            messagebox.showwarning("No Selection", "Please select a human training session!")
            return
        
        if "Select" in bot_selection or "No" in bot_selection:
            messagebox.showwarning("No Selection", "Please select a bot clicker session!")
            return
        
        training_sessions = self.session_manager.get_training_sessions()
        clicker_sessions = self.session_manager.get_clicker_sessions()
        
        human_idx = self.human_session_menu.current()
        bot_idx = self.bot_session_menu.current()
        
        if human_idx < 0 or bot_idx < 0:
            messagebox.showerror("Error", "Could not find selected sessions!")
            return
        
        available_training = list(reversed(training_sessions[-10:]))
        available_clicker = list(reversed(clicker_sessions[-10:]))
        
        if human_idx >= len(available_training) or bot_idx >= len(available_clicker):
            messagebox.showerror("Error", "Session index out of range!")
            return
        
        human_session = available_training[human_idx]
        bot_session = available_clicker[bot_idx]
        
        h_type = human_session.get('type', 'unknown')
        h_clicks = human_session.get('total_clicks', 0)
        h_cps = human_session.get('avg_cps', 0)
        h_var = human_session.get('variance', 0)
        h_std = human_session.get('std_dev', 0)
        
        b_mode = bot_session.get('mode', 'unknown')
        b_clicks = bot_session.get('total_clicks', 0)
        b_cps = bot_session.get('avg_cps', 0)
        b_var = bot_session.get('variance', 0)
        b_std = bot_session.get('std_dev', 0)
        b_risk = bot_session.get('risk', 'UNKNOWN')
        b_score = bot_session.get('score', 0)
        
        cps_gap = b_cps - h_cps
        cps_gap_pct = (cps_gap / h_cps * 100) if h_cps != 0 else 0
        
        var_gap = b_var - h_var
        var_gap_pct = (var_gap / h_var * 100) if h_var != 0 else 0
        
        std_gap = b_std - h_std
        std_gap_pct = (std_gap / h_std * 100) if h_std != 0 else 0
        
        if h_type == "butterfly":
            var_target = 2200
        elif h_type == "jitter":
            var_target = 1200
        else:
            var_target = 900
        
        var_diff_pct = abs(b_var - h_var) / h_var if h_var > 0 else 1.0
        if var_diff_pct < 0.15:
            variance_score = 50
        elif var_diff_pct < 0.30:
            variance_score = 35
        elif var_diff_pct < 0.50:
            variance_score = 20
        else:
            variance_score = 5
        
        cps_diff_pct = abs(b_cps - h_cps) / h_cps if h_cps > 0 else 1.0
        if cps_diff_pct < 0.10:
            cps_score = 30
        elif cps_diff_pct < 0.20:
            cps_score = 20
        elif cps_diff_pct < 0.35:
            cps_score = 10
        else:
            cps_score = 5
        
        std_diff_pct = abs(b_std - h_std) / h_std if h_std > 0 else 1.0
        if std_diff_pct < 0.15:
            std_score = 20
        elif std_diff_pct < 0.30:
            std_score = 12
        else:
            std_score = 5
        
        realism_score = variance_score + cps_score + std_score
        
        report = f"""
╔═══════════════════════════════════════════════════════════════════════╗
║              MIMIC - DIFFERENTIAL ANALYSIS - HUMAN vs BOT             ║
╠═══════════════════════════════════════════════════════════════════════╣

SELECTED SESSIONS:
  Human: {h_type.upper()} clicking • {h_clicks} clicks
  Bot:   {b_mode.upper()} mode • {b_clicks} clicks

SIDE-BY-SIDE COMPARISON:
╔═══════════════════╦══════════════════╦══════════════════╦═════════════╗
║    Metric         ║   Human          ║   Bot            ║   Gap       ║
╠═══════════════════╬══════════════════╬══════════════════╬═════════════╣
║ Average CPS       ║    {h_cps:>8.2f}      ║    {b_cps:>8.2f}      ║  {cps_gap_pct:>7.1f}%   ║
║ Variance          ║    {int(h_var):>8}      ║    {int(b_var):>8}      ║  {var_gap_pct:>7.1f}%   ║
║ Std Deviation     ║    {h_std:>8.2f}      ║    {b_std:>8.2f}      ║  {std_gap_pct:>7.1f}%   ║
╚═══════════════════╩══════════════════╩══════════════════╩═════════════╝

REALISM SCORE: {realism_score}/100
{"🟢" if realism_score >= 70 else "🟡" if realism_score >= 50 else "🔴"} Bot Detection Risk: {b_risk} (Score: {b_score}/100)

COMPONENT SCORES:
  • Variance Match:     {variance_score}/50 {"✅" if variance_score >= 35 else "⚠️"}
  • CPS Similarity:     {cps_score}/30 {"✅" if cps_score >= 20 else "⚠️"}
  • Std Dev Match:      {std_score}/20 {"✅" if std_score >= 12 else "⚠️"}

ANALYSIS:
"""
        
        if realism_score >= 80:
            report += "  ✅ EXCELLENT - Bot matches human baseline very closely\n"
            report += "  • Current configuration is optimal\n"
            report += "  • Continue monitoring in Analytics tab\n"
        elif realism_score >= 60:
            report += "  🟡 GOOD - Bot approximates human clicking well\n"
            if var_gap_pct < -20:
                report += f"  • Bot variance is {abs(var_gap_pct):.0f}% LOWER than human\n"
                report += f"  • Target: Increase to ~{int(h_var)} for better match\n"
            elif var_gap_pct > 20:
                report += f"  • Bot variance is {var_gap_pct:.0f}% HIGHER than human\n"
                report += "  • This is acceptable for anti-cheat purposes\n"
            
            if abs(cps_gap_pct) > 15:
                report += f"  • CPS gap: {abs(cps_gap_pct):.0f}% difference\n"
                if cps_gap_pct > 0:
                    report += "  • Bot clicking faster than recorded human baseline\n"
                else:
                    report += "  • Bot clicking slower than recorded human baseline\n"
        else:
            report += "  🔴 NEEDS IMPROVEMENT - Significant gaps detected\n"
            if variance_score < 20:
                report += f"  ⚠️ CRITICAL: Variance mismatch ({var_gap_pct:+.0f}%)\n"
                report += f"  → Target variance: {int(h_var)} (currently {int(b_var)})\n"
            if cps_score < 15:
                report += f"  ⚠️ WARNING: CPS mismatch ({cps_gap_pct:+.0f}%)\n"
                report += f"  → Target CPS: {h_cps:.1f} (currently {b_cps:.1f})\n"
            
            report += "\nACTION ITEMS:\n"
            report += "  1. Review clicker mode settings (Enhanced vs Standard)\n"
            report += "  2. Record more training data for accurate baseline\n"
            report += "  3. Compare with different human session types\n"
        
        report += """
═══════════════════════════════════════════════════════════════════════════
💡 TIP: Record more training data to improve baseline accuracy
"""
        
        self.diff_results.config(state=tk.NORMAL)
        self.diff_results.delete("1.0", tk.END)
        self.diff_results.insert("1.0", report)
        self.diff_results.config(state=tk.DISABLED)
    
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
        
        if page_idx == 3 and self.engine:
            if len(self.engine.cps_history) >= 2:
                self.cps_graph.draw_graph(self.engine.cps_history, self.engine.cps_timestamps)
            if len(self.engine.all_delays) >= 5:
                mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
                stddev = self.engine.calculate_std_dev()
                self.histogram.draw_histogram(self.engine.all_delays, mean, stddev, self.enhanced_mode)
        elif page_idx == 5:
            self.update_history_list()
        elif page_idx == 6:
            self.update_differential_options()
    
    def next_page(self):
        if self.current_page < len(self.pages) - 1:
            self.switch_page(self.current_page + 1)
    
    def prev_page(self):
        if self.current_page > 0:
            self.switch_page(self.current_page - 1)
    
    def setup_hotkeys(self):
        """Register all keyboard hotkeys"""
        keyboard.add_hotkey('f4', self.toggle_active)
        #keyboard.add_hotkey('enter', self.toggle_active) #DISABLED
        keyboard.add_hotkey('f5', self.export_stats)
        keyboard.add_hotkey('f6', self.export_csv)
        keyboard.add_hotkey('f7', self.toggle_training_mode)
        keyboard.add_hotkey('f8', self.export_human_baseline)
        keyboard.add_hotkey('f9', self.toggle_enhanced_mode)
        keyboard.add_hotkey('f10', self.toggle_mini_mode)
        keyboard.add_hotkey('left', self.prev_page)
        keyboard.add_hotkey('right', self.next_page)
    
    def format_time_elapsed(self, seconds):
        """Format seconds to readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def update_display(self):
        """Update all GUI elements with visual risk indicators"""
        if self.active and self.engine:
            if self.clicking:
                self.click_status.config(text="⚔️ CLICKING", fg=self.accent_color)
            else:
                self.click_status.config(text="Waiting for MB5...", fg="#888888")
            
            elapsed = (datetime.now() - self.engine.session_start).total_seconds()
            self.session_timer.config(text=f"⏱️ {self.format_time_elapsed(elapsed)}")
            
            self.total_clicks_card.config(text=str(self.engine.total_clicks))
            
            if self.engine.total_clicks > 10:
                current_cps = self.engine.get_current_cps()
                self.current_cps_card.config(text=f"{current_cps:.1f}")
                
                variance = self.engine.calculate_overall_variance() if len(self.engine.all_delays) >= 20 else self.engine.calculate_variance()
                self.variance_card.config(text=f"{int(variance)}")
                
                std_dev = self.engine.calculate_std_dev()
                self.std_dev_card.config(text=f"{std_dev:.1f}")
                
                stats = self.engine.get_detailed_stats()
                if stats:
                    self.avg_cps_card.config(text=f"{stats['avg_cps']:.2f}")
                    
                    risk_assessment = RiskAssessor.assess(stats)
                    self.risk_card.config(text=risk_assessment['risk'], fg=risk_assessment['color'])
                    
                    if stats.get('total', 0) >= 20:
                        score = risk_assessment['score']
                        risk_level = RiskVisualization.get_risk_level(score)
                        
                        for widget in self.risk_display_container.winfo_children():
                            widget.destroy()
                        
                        score_label = tk.Label(
                            self.risk_display_container,
                            text=f"{risk_level['emoji']} {score}/100 - {risk_level['label']}",
                            font=("Arial", 16, "bold"),
                            bg=self.panel_color,
                            fg=risk_level['color']
                        )
                        score_label.pack()
                        
                        thresholds = risk_assessment['thresholds']
                        
                        if variance >= thresholds['target_variance']:
                            v_icon, v_color = "🟢", "#4CAF50"
                        elif variance >= thresholds['ideal_variance']:
                            v_icon, v_color = "🟡", "#FFC107"
                        else:
                            v_icon, v_color = "🔴", "#F44336"
                        
                        self.variance_health.config(
                            text=f"{v_icon} Variance: {int(variance)} (Target: {thresholds['target_variance']})",
                            fg=v_color
                        )
                        
                        max_cps = stats.get('max_cps', 0)
                        if max_cps >= thresholds['spike_cps']:
                            c_icon, c_color = "🟢", "#4CAF50"
                        elif max_cps >= thresholds['max_cps']:
                            c_icon, c_color = "🟡", "#FFC107"
                        else:
                            c_icon, c_color = "🔴", "#F44336"
                        
                        self.cps_health.config(
                            text=f"{c_icon} CPS Range: {max_cps:.1f} max (Target: {thresholds['spike_cps']}+)",
                            fg=c_color
                        )
                        
                        breaks = stats.get('pattern_breaks', 0)
                        total = stats.get('total', 1)
                        break_ratio = breaks / (total / 20) if total > 20 else 0
                        
                        if break_ratio >= 0.75:
                            p_icon, p_color = "🟢", "#4CAF50"
                        elif break_ratio >= 0.50:
                            p_icon, p_color = "🟡", "#FFC107"
                        else:
                            p_icon, p_color = "🔴", "#F44336"
                        
                        self.pattern_health.config(
                            text=f"{p_icon} Pattern Breaks: {breaks} ({break_ratio*100:.0f}% rate)",
                            fg=p_color
                        )
                    
                    self.risk_level.config(text=risk_assessment['risk'], fg=risk_assessment['color'])
                    self.risk_score.config(text=f"{risk_assessment['score']}/100")
                    self.burst_events.config(text=str(stats.get('burst_count', 0)))
                    self.pause_events.config(text=str(stats.get('pause_count', 0)))
                    self.outlier_count.config(text=str(stats.get('outlier_count', 0)))
                    
                    if self.current_page == 3:
                        if len(self.engine.cps_history) >= 2:
                            self.cps_graph.draw_graph(self.engine.cps_history, self.engine.cps_timestamps)
                        if len(self.engine.all_delays) >= 5:
                            mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
                            self.histogram.draw_histogram(self.engine.all_delays, mean, std_dev, self.enhanced_mode)
        
        elif self.human_tracker.is_tracking:
            self.total_clicks_card.config(text=str(self.human_tracker.total_clicks))
            self.current_cps_card.config(text="TRAIN")
            
            clicks = self.human_tracker.total_clicks
            if clicks < Config.TRAINING_MIN_CLICKS:
                progress = f"Progress: {clicks}/{Config.TRAINING_MIN_CLICKS} minimum"
                progress_color = "#888888"
            elif clicks < Config.TRAINING_RECOMMENDED_CLICKS:
                progress = f"Progress: {clicks}/{Config.TRAINING_RECOMMENDED_CLICKS} recommended"
                progress_color = self.training_color
            elif clicks < Config.TRAINING_COMPLETE_CLICKS:
                progress = f"Almost there: {clicks}/{Config.TRAINING_COMPLETE_CLICKS}"
                progress_color = self.training_color
            else:
                progress = f"✅ {clicks} clicks - COMPLETE!"
                progress_color = self.accent_color
            
            self.training_progress.config(text=progress, fg=progress_color)
            
            if self.human_tracker.session_start:
                elapsed = (datetime.now() - self.human_tracker.session_start).total_seconds()
                self.session_timer.config(text=f"⏱️ {self.format_time_elapsed(elapsed)}")
        
        else:
            self.total_clicks_card.config(text="0")
            self.current_cps_card.config(text="--")
            self.variance_card.config(text="--")
            self.std_dev_card.config(text="--")
            self.avg_cps_card.config(text="--")
            self.risk_card.config(text="--", fg=self.accent_color)
            self.session_timer.config(text="⏱️ 0:00")
            self.training_progress.config(text="")
        
        self.root.after(500, self.update_display)
    
    def toggle_active(self):
        """Toggle clicker on/off"""
        if self.human_tracker.is_tracking:
            messagebox.showwarning("Training Active", "Stop training mode first (F7)")
            return
        
        self.active = not self.active
        
        if self.active:
            self.engine = AdaptiveClickerEngine(enhanced_mode=self.enhanced_mode)
            self.status_indicator.config(text="🟢 ACTIVE - Hold LEFT CLICK", fg=self.accent_color)
            self.toggle_btn.config(text="⏸ Deactivate (F4)", bg="#f44336")
            print("\n[MIMIC] Activated - Hold LEFT CLICK to click\n")
        else:
            # Stop clicking FIRST
            self.clicking = False
            self.physical_left_held = False  # Also reset physical state
            
            # Then safely stop engine
            if self.engine:
                self.engine.stop_clicking()
            
            # THEN set to None
            self.engine = None
            
            self.status_indicator.config(text="⚫ INACTIVE", fg=self.inactive_color)
            self.toggle_btn.config(text="▶ Activate (F4)", bg=self.accent_color)
            print("\n[MIMIC] Deactivated\n")


    
    def toggle_enhanced_mode(self):
        """Toggle enhanced mode"""
        if self.active:
            messagebox.showwarning("Cannot Change", "Stop clicker first (F4)")
            return
        
        self.enhanced_mode = not self.enhanced_mode
        
        if self.enhanced_mode:
            self.mode_indicator.config(text="✨ Enhanced Adaptive Mode", fg=self.enhanced_color)
            self.enhanced_status.config(text="Status: ✅ Enabled • Adaptive Mixed Mode", fg=self.enhanced_color)
            print("\n[MODE] Enhanced Mode ENABLED\n")
        else:
            self.mode_indicator.config(text="Standard Mode", fg="#888888")
            self.enhanced_status.config(text="Status: ⚪ Disabled • Standard Mode", fg="#888888")
            print("\n[MODE] Standard Mode ENABLED\n")
    
    def select_training_type(self, click_type):
        """Select training click type"""
        self.human_tracker.training_type = click_type
        self.training_type_label.config(
            text=f"Selected: {click_type.upper()}",
            fg=self.training_color
        )
        print(f"\n[TRAINING] Type selected: {click_type.upper()}\n")
    
    def toggle_training_mode(self):
        """Toggle training mode on/off"""
        if self.active:
            messagebox.showwarning("Clicker Active", "Stop clicker first (F4)")
            return
        
        if not self.human_tracker.is_tracking:
            if self.human_tracker.training_type == "normal" and not hasattr(self, '_type_selected'):
                messagebox.showwarning("No Type Selected", "Please select a click type first!")
                return
            
            self.human_tracker.start_tracking(self.human_tracker.training_type)
            self.training_status_label.config(
                text=f"🔴 RECORDING - {self.human_tracker.training_type.upper()}",
                fg=self.training_color
            )
            self.train_start_btn.config(text="⏹ Stop Training (F7)", bg="#f44336")
        else:
            self.human_tracker.stop_tracking()
            self.training_status_label.config(text="Inactive - Select a type above", fg="#888888")
            self.train_start_btn.config(text="▶ Start Training (F7)", bg=self.training_color)
    
    def export_stats(self):
        """Export clicker statistics"""
        if not self.engine or not self.engine.all_delays:
            messagebox.showwarning("No Data", "No clicker data to export!")
            return
        
        stats = self.engine.get_detailed_stats()
        if not stats:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mimic_session_{timestamp}.txt"
        filepath = os.path.join(Config.get_clicker_data_path(), filename)
        
        try:
            os.makedirs(Config.get_clicker_data_path(), exist_ok=True)
            
            report = f"""
═══════════════════════════════════════════════════════════════════════════
MIMIC SESSION REPORT v3.7
═══════════════════════════════════════════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {"Enhanced Adaptive" if stats['enhanced_mode'] else "Standard"}

STATISTICS:
Total Clicks: {stats['total']}
Average CPS: {stats['avg_cps']:.2f}
Max CPS: {stats['max_cps']:.2f}
Variance: {int(stats['variance'])}
Std Dev: {stats['std_dev']:.2f}

ANTI-DETECTION:
Pattern Breaks: {stats['pattern_breaks']}
Burst Events: {stats['burst_count']}
Pause Events: {stats['pause_count']}
Outliers: {stats['outlier_count']}

═══════════════════════════════════════════════════════════════════════════
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report)
            
            self.session_manager.add_clicker_session(stats, filepath)
            
            messagebox.showinfo("Export Success", f"Saved to:\n{filepath}")
            print(f"\n[EXPORT] Stats saved to: {filepath}\n")
        
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    
    def export_csv(self):
        """Export CSV data"""
        if not self.engine or not self.engine.all_delays:
            messagebox.showwarning("No Data", "No clicker data to export!")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"mimic_data_{timestamp}.csv"
        filepath = os.path.join(Config.get_clicker_data_path(), filename)
        
        try:
            os.makedirs(Config.get_clicker_data_path(), exist_ok=True)
            self.engine.export_to_csv(filepath)
            messagebox.showinfo("Export Success", f"CSV saved to:\n{filepath}")
            print(f"\n[EXPORT] CSV saved to: {filepath}\n")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))
    
    def export_human_baseline(self):
        """Export human training baseline"""
        if not self.human_tracker.is_tracking and len(self.human_tracker.click_delays) < 10:
            messagebox.showwarning("No Data", "Record training data first (F7)!")
            return
        
        self.human_tracker.export_human_stats()
    
    def toggle_mini_mode(self):
        """Toggle mini mode (placeholder)"""
        messagebox.showinfo("Coming Soon", "Mini-mode will be available in a future update!")
    
    def start_threads(self):
        """Start background threads"""
        self.running = True
        
        threading.Thread(target=self.mouse_button_listener, daemon=True).start()
        threading.Thread(target=self.clicking_loop, daemon=True).start()
    
    def mouse_button_listener(self):
        """Monitor for training mode only - clicking handled by pynput"""
        while self.running:
            # Training mode (unchanged)
            if self.human_tracker.is_tracking:
                left_state = win32api.GetAsyncKeyState(0x01)
                if left_state & 0x8000:
                    self.human_tracker.record_click()
                    time.sleep(0.05)
            
            time.sleep(0.01)

    
    def clicking_loop(self):
        """Main clicking loop - uses pynput for reliable state tracking"""
        while self.running:
            if self.active and self.engine:  # Check self.engine exists
                # Check the PHYSICAL state (unaffected by synthetic clicks)
                if self.physical_left_held:
                    if not self.clicking:
                        self.clicking = True
                        if self.engine:  # Double-check before calling
                            self.engine.start_clicking()
                        print("[MIMIC] Started auto-clicking")
                    
                    # Send synthetic click - CHECK ENGINE EXISTS
                    if self.engine:  # Add this check
                        self.engine.click()
                    
                else:
                    if self.clicking:
                        self.clicking = False
                        if self.engine:  # Check before calling
                            self.engine.stop_clicking()
                        print("[MIMIC] Stopped auto-clicking")
                    time.sleep(0.01)
            else:
                time.sleep(0.01)



    def on_close(self):
        """Handle window close"""
        self.running = False
        self.mouse_listener.stop()  # ADD THIS LINE - Stop pynput listener
        self.root.destroy()

    
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

# ═════════════════════════════════════════════════════════════════════════════
# MAIN EXECUTION
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("""
    ═══════════════════════════════════════════════════════════════════════
    
            ███╗   ███╗██╗███╗   ███╗██╗ ██████╗
            ████╗ ████║██║████╗ ████║██║██╔════╝
            ██╔████╔██║██║██╔████╔██║██║██║     
            ██║╚██╔╝██║██║██║╚██╔╝██║██║██║     
            ██║ ╚═╝ ██║██║██║ ╚═╝ ██║██║╚██████╗
            ╚═╝     ╚═╝╚═╝╚═╝     ╚═╝╚═╝ ╚═════╝
                                                    
                      Statistical Ghost Clicker
                             v3.7.0
    
    ═══════════════════════════════════════════════════════════════════════
    
         LAUNCH SEQUENCE
       • Loading adaptive engine...
       • Initializing statistical distributions...
       • Starting GUI...
    
    ═══════════════════════════════════════════════════════════════════════
    """)
    
    app = MinecraftAutoClickerGUI()
    app.run()