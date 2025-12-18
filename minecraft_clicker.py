"""
═══════════════════════════════════════════════════════════════════════════════
MINECRAFT AUTO CLICKER v3.6 - ADAPTIVE INTELLIGENCE
═══════════════════════════════════════════════════════════════════════════════
Version: 3.6.0 - Adaptive Intelligence Update
Target: 7-12 CPS average with 15-16 CPS spikes

NEW IN v3.6:
  ✅ Mixed Mode Adaptive Clicking (blends all techniques)
  ✅ Relaxed CPS ceiling (allows 15-16 CPS spikes)
  ✅ Revised Risk Assessment (realistic 1,500-2,500 variance targets)
  ✅ Training Session History (Page 6)
  ✅ Differential Analysis (Page 7 - Human vs Bot)
  ✅ Statistical Outlier Injection (careful 2% rate)
  ✅ Comprehensive Risk Scoring (0-100 points)
  ✅ Auto-tuning recommendations
  
File Organization:
  training_data/
    ├── clickerData/     ← Auto-clicker sessions (F5/F6)
    ├── butterfly/       ← Human training data
    ├── jitter/          ← Human training data
    ├── normal/          ← Human training data
    ├── mixed/           ← Human training data
    └── sessions.json    ← Session history database
  
Controls:
  F4  - Toggle On/Off          F9  - Toggle Enhanced Mode
  F5  - Export TXT Stats       F10 - Mini Mode
  F6  - Export CSV             ← → - Navigate Pages
  F7  - Start/Stop Training    Enter - Quick Toggle
  F8  - Export Training Data   MB5 - Click (Hold)
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

# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═════════════════════════════════════════════════════════════════════════════

class Config:
    """Global configuration with realistic anti-cheat thresholds"""
    
    # ✅ NEW: Relaxed CPS limits (allow spikes)
    ABSOLUTE_MIN_DELAY_MS = 65   # 15.4 CPS spike allowed
    ABSOLUTE_MAX_DELAY_MS = 400  # Extended pauses for realism
    SUSTAINED_CPS_CAP = 12       # Average shouldn't sustain >12
    
    # Enhanced Mode has wider range
    ENHANCED_MIN_DELAY_MS = 60   # 16.7 CPS burst maximum
    ENHANCED_MAX_DELAY_MS = 450  # Longer pauses
    
    # ✅ NEW: Realistic variance targets
    ENHANCED_IDEAL_VARIANCE = 1500   # Minimum acceptable
    ENHANCED_TARGET_VARIANCE = 2200  # Optimal butterfly/jitter
    ENHANCED_MAX_VARIANCE = 3500     # Upper bound
    
    STANDARD_IDEAL_VARIANCE = 600    # Minimum acceptable
    STANDARD_TARGET_VARIANCE = 900   # Optimal normal clicking
    STANDARD_MAX_VARIANCE = 1500     # Upper bound
    
    # Anti-Detection Thresholds
    MIN_VARIANCE_THRESHOLD = 800  # Raised from 120
    PATTERN_CHECK_WINDOW = 20
    
    # ✅ NEW: Adaptive mode parameters
    TECHNIQUE_TRANSITION_MIN = 5   # Min clicks before switching
    TECHNIQUE_TRANSITION_MAX = 15  # Max clicks before switching
    
    # Enhanced Mode Parameters
    BURST_PROBABILITY = 0.20       # Increased from 0.15
    PAUSE_PROBABILITY = 0.10       # Increased from 0.08
    BURST_DURATION = (3, 8)
    PAUSE_DURATION_MS = (200, 450)
    
    # ✅ NEW: Outlier injection
    OUTLIER_PROBABILITY = 0.02     # 2% of clicks
    OUTLIER_COOLDOWN = (30, 80)    # Clicks between outliers
    
    # Mouse Button Constants
    VK_XBUTTON2 = 0x06  # MB5
    VK_LBUTTON = 0x01   # Left mouse button
    
    # Training Thresholds
    TRAINING_MIN_CLICKS = 100
    TRAINING_RECOMMENDED_CLICKS = 200
    TRAINING_COMPLETE_CLICKS = 250
    
    # File Organization
    @staticmethod
    def get_training_data_path():
        """Get path to Desktop/training_data/"""
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return os.path.join(desktop, "training_data")
    
    @staticmethod
    def get_clicker_data_path():
        """Get path to Desktop/training_data/clickerData/"""
        return os.path.join(Config.get_training_data_path(), "clickerData")
    
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
# ADAPTIVE MIXED MODE CLICKER ENGINE
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
        
        # ✅ NEW: Adaptive technique state
        self.current_technique = "normal"
        self.technique_duration = 0
        self.next_transition = random.randint(
            Config.TECHNIQUE_TRANSITION_MIN,
            Config.TECHNIQUE_TRANSITION_MAX
        )
        
        # ✅ NEW: Outlier injection
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
        """Box-Muller transform for Gaussian distribution"""
        u1, u2 = random.random(), random.random()
        rand_std_normal = math.sqrt(-2.0 * math.log(u1)) * math.sin(2.0 * math.pi * u2)
        return mean + std_dev * rand_std_normal
    
    def weibull_random(self, scale, shape):
        """Weibull distribution for varied timing"""
        u = random.random()
        return scale * ((-math.log(1 - u)) ** (1 / shape))
    
    def check_cps(self):
        """✅ NEW: Allow spikes, prevent sustained high CPS"""
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
        
        # ✅ NEW: Adaptive thresholds based on mode
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
        """✅ NEW: Dynamically choose clicking technique"""
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
        """✅ NEW: Statistical outlier injection (2% rate)"""
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
        """✅ NEW: Adaptive delay calculation with mixed techniques"""
        
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
        
        # ✅ NEW: Technique-based delay calculation
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
        
        # ✅ NEW: Clamp to relaxed limits (allow 15-16 CPS spikes)
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
HUMAN CLICK ANALYSIS - {training_type} CLICKING PATTERN
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

RECOMMENDATION FOR AUTO-CLICKER:
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
            if self.export_to_csv(csv_full_path):
                print(f"[SUCCESS] CSV data saved to: {csv_full_path}\n")
            
            # Add to session history
            self.session_manager.add_training_session(stats, txt_full_path)
            
            print(f"[INFO] Files organized in Desktop/training_data/{training_type_safe}/\n")
            
            messagebox.showinfo(
                "Export Success",
                f"Training data exported!\n\nTXT: {txt_filename}\nCSV: {csv_filename}\n\nFolder: training_data/{training_type_safe}/\n\n✅ Added to session history"
            )
            
        except Exception as e:
            # Fallback to current directory
            try:
                with open(txt_filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                self.export_to_csv(csv_filename)
                print(f"[SUCCESS] Files exported to current directory\n")
                print(f"[WARNING] Could not create Desktop folder: {e}\n")
                messagebox.showinfo(
                    "Export Success (Current Dir)",
                    f"Files saved to current directory:\n{txt_filename}\n{csv_filename}"
                )
            except Exception as e2:
                print(f"[ERROR] Could not save files: {e2}\n")
                messagebox.showerror("Export Failed", f"Could not save files:\n{str(e2)}")


# ═════════════════════════════════════════════════════════════════════════════
# CPS LINE GRAPH VISUALIZER
# ═════════════════════════════════════════════════════════════════════════════

class CPSLineGraph(tk.Canvas):
    """Real-time CPS line graph (30-second rolling window)"""
    
    def __init__(self, parent, width=560, height=200, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.padding_left = 50
        self.padding_right = 20
        self.padding_top = 25
        self.padding_bottom = 35
        self.chart_width = width - self.padding_left - self.padding_right
        self.chart_height = height - self.padding_top - self.padding_bottom
        
        # Colors
        self.grid_color = "#333333"
        self.text_color = "#888888"
        self.line_color = "#4CAF50"
        self.danger_color = "#f44336"
        self.optimal_zone_color = "#2d5c2d"
    
    def draw_graph(self, cps_history, cps_timestamps):
        """Draw real-time CPS line graph"""
        self.delete("all")
        
        if not cps_history or len(cps_history) < 2:
            self.create_text(
                self.width // 2, self.height // 2,
                text="Waiting for click data...",
                fill=self.text_color,
                font=("Arial", 11)
            )
            return
        
        # Draw optimal zone (7-12 CPS)
        optimal_top_y = self.padding_top + (1 - (12 / 18)) * self.chart_height
        optimal_bottom_y = self.padding_top + (1 - (7 / 18)) * self.chart_height
        
        self.create_rectangle(
            self.padding_left, optimal_top_y,
            self.padding_left + self.chart_width, optimal_bottom_y,
            fill=self.optimal_zone_color,
            outline=""
        )
        
        # Draw grid lines
        for i in range(7):
            y = self.padding_top + (i * self.chart_height // 6)
            cps_value = 18 - (i * 3)
            
            self.create_line(
                self.padding_left, y,
                self.padding_left + self.chart_width, y,
                fill=self.grid_color,
                dash=(2, 2)
            )
            
            self.create_text(
                self.padding_left - 10, y,
                text=str(cps_value),
                fill=self.text_color,
                font=("Arial", 8),
                anchor="e"
            )
        
        # Draw CPS line
        points = []
        cps_list = list(cps_history)
        
        for i, cps in enumerate(cps_list):
            x = self.padding_left + (i / max(1, len(cps_list) - 1)) * self.chart_width
            y = self.padding_top + (1 - min(cps, 18) / 18) * self.chart_height
            points.extend([x, y])
        
        if len(points) >= 4:
            self.create_line(
                *points,
                fill=self.line_color,
                width=2,
                smooth=True
            )
        
        # Draw axes
        self.create_line(
            self.padding_left, self.padding_top + self.chart_height,
            self.padding_left + self.chart_width, self.padding_top + self.chart_height,
            fill=self.text_color,
            width=2
        )
        
        self.create_line(
            self.padding_left, self.padding_top,
            self.padding_left, self.padding_top + self.chart_height,
            fill=self.text_color,
            width=2
        )
        
        # Labels
        self.create_text(
            self.width // 2, self.height - 10,
            text="Time (last 30 seconds)",
            fill=self.text_color,
            font=("Arial", 9, "bold")
        )
        
        self.create_text(
            15, self.height // 2,
            text="CPS",
            fill=self.text_color,
            font=("Arial", 9, "bold"),
            angle=90
        )


# ═════════════════════════════════════════════════════════════════════════════
# HISTOGRAM VISUALIZER
# ═════════════════════════════════════════════════════════════════════════════

class HistogramCanvas(tk.Canvas):
    """Custom histogram visualization with danger zones"""
    
    def __init__(self, parent, width=560, height=280, **kwargs):
        super().__init__(parent, width=width, height=height, bg="#1a1a1a", highlightthickness=0, **kwargs)
        self.width = width
        self.height = height
        self.padding_left = 55
        self.padding_right = 30
        self.padding_top = 35
        self.padding_bottom = 45
        self.chart_width = width - self.padding_left - self.padding_right
        self.chart_height = height - self.padding_top - self.padding_bottom
        
        # Colors
        self.grid_color = "#333333"
        self.text_color = "#888888"
        self.mean_color = "#4CAF50"
        self.std_color = "#FFA500"
        self.bar_optimal = "#4CAF50"
        self.bar_acceptable = "#FFA500"
        self.bar_risky = "#f44336"
        
    def draw_histogram(self, delays, mean, std_dev, enhanced_mode=False):
        """Draw histogram with danger zones highlighted"""
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
        
        min_delay = 50 if enhanced_mode else 80
        max_delay = 450 if enhanced_mode else 150
        bin_width = 20
        num_bins = int((max_delay - min_delay) / bin_width) + 1
        
        bins = [0] * num_bins
        for delay in delays:
            if min_delay <= delay <= max_delay:
                bin_idx = int((delay - min_delay) / bin_width)
                if 0 <= bin_idx < num_bins:
                    bins[bin_idx] += 1
        
        max_count = max(bins) if max(bins) > 0 else 1
        
        # Draw grid
        num_grid_lines = 5
        for i in range(num_grid_lines + 1):
            y = self.padding_top + (i * self.chart_height // num_grid_lines)
            count_value = int(max_count * (1 - i / num_grid_lines))
            
            self.create_line(
                self.padding_left, y,
                self.padding_left + self.chart_width, y,
                fill=self.grid_color,
                dash=(2, 2)
            )
            
            self.create_text(
                self.padding_left - 10, y,
                text=str(count_value),
                fill=self.text_color,
                font=("Arial", 8),
                anchor="e"
            )
        
        # Draw histogram bars
        bar_width_px = self.chart_width / num_bins
        max_bar_height = self.chart_height * 0.9
        
        for i, count in enumerate(bins):
            if count == 0:
                continue
            
            x1 = self.padding_left + i * bar_width_px
            bar_height = (count / max_count) * max_bar_height
            y1 = self.padding_top + self.chart_height - bar_height
            x2 = x1 + bar_width_px - 2
            y2 = self.padding_top + self.chart_height
            
            delay_value = min_delay + i * bin_width
            
            # Color based on danger zones
            if 65 <= delay_value <= 143:
                color = self.bar_optimal
            elif (enhanced_mode and 50 <= delay_value <= 450) or (not enhanced_mode and 65 <= delay_value <= 180):
                color = self.bar_acceptable
            else:
                color = self.bar_risky
            
            self.create_rectangle(
                x1, y1, x2, y2,
                fill=color,
                outline=""
            )
        
        # Draw mean line
        mean_x = self.padding_left + ((mean - min_delay) / (max_delay - min_delay)) * self.chart_width
        if self.padding_left <= mean_x <= self.padding_left + self.chart_width:
            self.create_line(
                mean_x, self.padding_top,
                mean_x, self.padding_top + self.chart_height,
                fill=self.mean_color,
                width=2
            )
            self.create_text(
                mean_x, self.padding_top - 15,
                text=f"μ={mean:.0f}ms",
                fill=self.mean_color,
                font=("Arial", 8, "bold")
            )
        
        # Draw std dev bands
        std_left = self.padding_left + ((mean - std_dev - min_delay) / (max_delay - min_delay)) * self.chart_width
        std_right = self.padding_left + ((mean + std_dev - min_delay) / (max_delay - min_delay)) * self.chart_width
        
        if self.padding_left <= std_left <= self.padding_left + self.chart_width:
            self.create_line(
                std_left, self.padding_top,
                std_left, self.padding_top + self.chart_height,
                fill=self.std_color,
                width=1,
                dash=(4, 4)
            )
        
        if self.padding_left <= std_right <= self.padding_left + self.chart_width:
            self.create_line(
                std_right, self.padding_top,
                std_right, self.padding_top + self.chart_height,
                fill=self.std_color,
                width=1,
                dash=(4, 4)
            )
        
        # Axes
        self.create_line(
            self.padding_left, self.padding_top + self.chart_height,
            self.padding_left + self.chart_width, self.padding_top + self.chart_height,
            fill=self.text_color,
            width=2
        )
        
        self.create_line(
            self.padding_left, self.padding_top,
            self.padding_left, self.padding_top + self.chart_height,
            fill=self.text_color,
            width=2
        )
        
        # X-axis labels
        num_labels = min(6, num_bins + 1)
        for i in range(num_labels):
            bin_idx = int((i / (num_labels - 1)) * num_bins) if num_labels > 1 else 0
            x = self.padding_left + bin_idx * bar_width_px
            delay_label = min_delay + bin_idx * bin_width
            self.create_text(
                x, self.padding_top + self.chart_height + 22,
                text=f"{delay_label}",
                fill=self.text_color,
                font=("Arial", 8)
            )
        
        # Axis titles
        self.create_text(
            self.width // 2, self.height - 10,
            text="Delay (ms)",
            fill=self.text_color,
            font=("Arial", 9, "bold")
        )
        
        self.create_text(
            15, self.height // 2,
            text="Count",
            fill=self.text_color,
            font=("Arial", 9, "bold"),
            angle=90
        )
# ═════════════════════════════════════════════════════════════════════════════
# MULTI-PAGE GUI APPLICATION - v3.6 WITH DIFFERENTIAL ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

class AutoClickerGUI:
    """Feature-complete multi-page GUI with differential analysis"""
    
    def __init__(self):
        """Initialize the complete GUI"""
        
        # Main Window Setup
        self.root = tk.Tk()
        self.root.title("Minecraft Auto Clicker v3.6 - Adaptive Intelligence")
        self.root.geometry("620x760")
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
        
        # Session Manager
        self.session_manager = SessionManager()
        
        # Application State
        self.active = False
        self.clicking = False
        self.engine = None
        self.running = True
        self.last_session_stats = None
        self.human_tracker = HumanClickTracker(self.session_manager)
        self.enhanced_mode = True
        self.session_history = []
        self.selected_training_types = []
        self.mini_mode = False
        
        # Differential analysis state
        self.selected_human_session = None
        self.selected_bot_session = None
        
        # Page Management
        self.current_page = 0
        self.pages = []
        
        # Build UI
        self.setup_ui()
        self.setup_hotkeys()
        self.start_threads()
        self.update_display()
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
    
    
    def setup_ui(self):
        """Build complete UI with all features"""
        
        # HEADER
        header_frame = tk.Frame(self.root, bg=self.header_color, height=125)
        header_frame.pack(fill=tk.X, pady=(0, 8))
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="⚔️ Minecraft Auto Clicker v3.6",
            font=("Arial", 17, "bold"),
            bg=self.header_color,
            fg=self.fg_color
        )
        title.pack(pady=(15, 3))
        
        subtitle = tk.Label(
            header_frame,
            text="Adaptive Intelligence • Mixed Mode • Differential Analysis",
            font=("Arial", 8),
            bg=self.header_color,
            fg="#888888"
        )
        subtitle.pack(pady=(0, 4))
        
        self.mode_indicator = tk.Label(
            header_frame,
            text="⚡ Enhanced Adaptive Mode",
            font=("Arial", 8, "italic"),
            bg=self.header_color,
            fg=self.enhanced_color
        )
        self.mode_indicator.pack(pady=(0, 4))
        
        # File path indicator
        self.path_indicator = tk.Label(
            header_frame,
            text="📁 Desktop/training_data/",
            font=("Arial", 7),
            bg=self.header_color,
            fg="#666666"
        )
        self.path_indicator.pack(pady=(0, 5))
        
        self.status_indicator = tk.Label(
            header_frame,
            text="● INACTIVE",
            font=("Arial", 10, "bold"),
            bg=self.header_color,
            fg=self.inactive_color
        )
        self.status_indicator.pack(pady=(0, 10))
        
        # TAB NAVIGATION - 7 TABS
        tab_frame = tk.Frame(self.root, bg=self.bg_color)
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
        
        # CONTENT CONTAINER
        self.content_frame = tk.Frame(self.root, bg=self.bg_color)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=25)
        
        # Create all pages
        self.create_page_dashboard()
        self.create_page_settings()
        self.create_page_analytics()
        self.create_page_graphs()
        self.create_page_training()
        self.create_page_history()          # NEW: Page 6
        self.create_page_differential()     # NEW: Page 7
        
        # NAVIGATION FOOTER
        nav_frame = tk.Frame(self.root, bg=self.bg_color)
        nav_frame.pack(fill=tk.X, padx=25, pady=12)
        
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
            text="1 / 7",
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
        """Enhanced dashboard with visual stats cards"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Status panel with timer
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
        cards_frame = tk.Frame(page, bg=self.bg_color)
        cards_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 8))
        
        # Row 1
        row1 = tk.Frame(cards_frame, bg=self.bg_color)
        row1.pack(fill=tk.X, pady=(0, 5))
        
        self.create_stat_card(row1, "Total Clicks", "0", "total_clicks_card", 0)
        self.create_stat_card(row1, "Current CPS", "--", "current_cps_card", 1)
        self.create_stat_card(row1, "Average CPS", "--", "avg_cps_card", 2)
        
        # Row 2
        row2 = tk.Frame(cards_frame, bg=self.bg_color)
        row2.pack(fill=tk.X)
        
        self.create_stat_card(row2, "Variance", "--", "variance_card", 0)
        self.create_stat_card(row2, "Std Dev", "--", "std_dev_card", 1)
        self.create_stat_card(row2, "Risk Level", "--", "risk_card", 2)
        
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
        
        # Row 1 buttons
        btn_row1 = tk.Frame(btn_grid, bg=self.panel_color)
        btn_row1.pack()
        
        self.toggle_btn = tk.Button(
            btn_row1,
            text="🚀 Activate (F4)",
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
            text="💾 Export Stats (F5)",
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
        
        # Row 2 buttons
        btn_row2 = tk.Frame(btn_grid, bg=self.panel_color)
        btn_row2.pack(pady=(5, 0))
        
        csv_btn = tk.Button(
            btn_row2,
            text="📊 Export CSV (F6)",
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
            text="🎮 Mini Mode (F10)",
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
        """Settings page - same as v3.5.1"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        canvas = tk.Canvas(page, bg=self.bg_color, highlightthickness=0, height=510)
        scrollbar = tk.Scrollbar(page, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_color)
        
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
            text="⚡ Toggle Enhanced Mode (F9)",
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
            text="Status: Enabled (Adaptive Mixed Mode)",
            font=("Arial", 9),
            bg=self.panel_color,
            fg=self.enhanced_color
        )
        self.enhanced_status.pack(pady=5)
        
        desc_text = "✅ Blends butterfly/jitter/normal techniques\n✅ Allows 15-16 CPS spikes\n✅ Target variance: 1,500-2,500"
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
        
        path_text = """All data saves to Desktop/training_data/

Folder Structure:
  training_data/
    ├── clickerData/     ← Session exports (F5/F6)
    ├── butterfly/       ← Training data (F8)
    ├── jitter/          ← Training data (F8)
    ├── normal/          ← Training data (F8)
    ├── mixed/           ← Training data (F8)
    └── sessions.json    ← History database"""
        
        tk.Label(
            export_panel,
            text=path_text,
            font=("Courier", 7),
            bg=self.panel_color,
            fg="#888888",
            justify=tk.LEFT
        ).pack(pady=(0, 12), padx=10)
        
        # Controls reference
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
            ("MB5", "Click (Hold)"),
            ("F5", "Export TXT"),
            ("F6", "Export CSV"),
            ("← →", "Switch Pages"),
            ("Enter", "Quick Toggle"),
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
        
        tk.Label(controls_panel, text="", bg=self.panel_color, height=1).pack()
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    
    def create_page_analytics(self):
        """Analytics page - same as v3.5.1"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
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
        
        self.create_metric_row(metrics_grid, "Detection Risk", "risk_level", 0)
        self.create_metric_row(metrics_grid, "Risk Score", "risk_score", 1)
        self.create_metric_row(metrics_grid, "Burst Events", "burst_events", 2)
        self.create_metric_row(metrics_grid, "Pause Events", "pause_events", 3)
        self.create_metric_row(metrics_grid, "Outlier Injections", "outlier_count", 4)
        
        tk.Label(current_panel, text="", bg=self.panel_color, height=1).pack()
        
        # Session history
        history_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        history_panel.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            history_panel,
            text="📜 Recent Clicker Sessions",
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
        
        self.history_text.insert("1.0", "No sessions yet.\nComplete a session to see analytics.")
        self.history_text.config(state=tk.DISABLED)
        
        tk.Label(history_panel, text="", bg=self.panel_color, height=1).pack()
    
    
    def create_page_graphs(self):
        """Graphs page - same as v3.5.1"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
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
            text="Green zone = Optimal (7-12 CPS)",
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
            ("●", "#4CAF50", "Optimal"),
            ("●", "#FFA500", "Acceptable"),
            ("─", "#4CAF50", "Mean"),
            ("┄", "#FFA500", "σ")
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
        """Training page - same as v3.5.1"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Title
        title_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        title_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            title_panel,
            text="🎯 Human Baseline Training",
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
            text="🎬 Start Training (F7)",
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
        
        # Progress indicator
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
        
        # Info
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
            "• Minimum: 100 clicks | Recommended: 200",
            "• Complete: 250+ clicks",
            "• Files save to Desktop/training_data/",
            "• View history in History tab →"
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
        """✅ NEW: Page 6 - Training Session History"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
        self.pages.append(page)
        
        # Title
        title_panel = tk.Frame(page, bg=self.panel_color, relief=tk.RIDGE, bd=2)
        title_panel.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(
            title_panel,
            text="📜 Training Session History",
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
        
        # Initial load
        self.update_history_list()
    
    
    def create_page_differential(self):
        """✅ NEW: Page 7 - Differential Analysis (Human vs Bot)"""
        page = tk.Frame(self.content_frame, bg=self.bg_color)
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
        
        # Load session options
        self.update_differential_options()
    
    
    def update_history_list(self):
        """Update training session history list"""
        filter_type = self.history_filter.get()
        
        # Get sessions
        if filter_type == "All":
            sessions = self.session_manager.get_training_sessions()
        else:
            sessions = self.session_manager.get_training_sessions(filter_type)
        
        # Update display
        self.history_list.config(state=tk.NORMAL)
        self.history_list.delete("1.0", tk.END)
        
        if not sessions:
            self.history_list.insert("1.0", "No training sessions found.\n\nComplete a training session (F7/F8) to see it here.")
        else:
            header = f"{'Date/Time':<20} {'Type':<12} {'Clicks':<8} {'CPS':<8} {'Variance':<10}\n"
            self.history_list.insert("1.0", header)
            self.history_list.insert("2.0", "=" * 70 + "\n")
            
            for session in reversed(sessions[-20:]):  # Last 20 sessions
                timestamp = session.get('timestamp', 'Unknown')
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime('%m/%d %H:%M:%S')
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
        # Get training sessions
        training_sessions = self.session_manager.get_training_sessions()
        training_options = []
        for i, session in enumerate(reversed(training_sessions[-10:])):  # Last 10
            timestamp = session.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%m/%d %H:%M')
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
        
        # Get clicker sessions
        clicker_sessions = self.session_manager.get_clicker_sessions()
        clicker_options = []
        for i, session in enumerate(reversed(clicker_sessions[-10:])):  # Last 10
            timestamp = session.get('timestamp', 'Unknown')
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime('%m/%d %H:%M')
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
        """✅ NEW: Perform differential analysis between human and bot sessions"""
        human_selection = self.human_session_var.get()
        bot_selection = self.bot_session_var.get()
        
        if "Select" in human_selection or "No" in human_selection:
            messagebox.showwarning("No Selection", "Please select a human training session!")
            return
        
        if "Select" in bot_selection or "No" in bot_selection:
            messagebox.showwarning("No Selection", "Please select a bot clicker session!")
            return
        
        # Get actual sessions (index from reversed list)
        training_sessions = list(reversed(self.session_manager.get_training_sessions()[-10:]))
        clicker_sessions = list(reversed(self.session_manager.get_clicker_sessions()[-10:]))
        
        human_idx = self.human_session_menu.current()
        bot_idx = self.bot_session_menu.current()
        
        if human_idx < 0 or human_idx >= len(training_sessions):
            messagebox.showerror("Error", "Invalid human session selection!")
            return
        
        if bot_idx < 0 or bot_idx >= len(clicker_sessions):
            messagebox.showerror("Error", "Invalid bot session selection!")
            return
        
        human_session = training_sessions[human_idx]
        bot_session = clicker_sessions[bot_idx]
        
        # Perform analysis
        report = self.generate_differential_report(human_session, bot_session)
        
        # Display results
        self.diff_results.config(state=tk.NORMAL)
        self.diff_results.delete("1.0", tk.END)
        self.diff_results.insert("1.0", report)
        self.diff_results.config(state=tk.DISABLED)
    
    
    def generate_differential_report(self, human_session, bot_session):
        """Generate detailed differential analysis report"""
        
        # Extract metrics
        h_cps = human_session.get('avg_cps', 0)
        h_var = human_session.get('variance', 0)
        h_std = human_session.get('std_dev', 0)
        h_type = human_session.get('type', 'unknown')
        h_clicks = human_session.get('total_clicks', 0)
        
        b_cps = bot_session.get('avg_cps', 0)
        b_var = bot_session.get('variance', 0)
        b_std = bot_session.get('std_dev', 0)
        b_mode = bot_session.get('mode', 'unknown')
        b_clicks = bot_session.get('total_clicks', 0)
        b_risk = bot_session.get('risk', 'UNKNOWN')
        b_score = bot_session.get('score', 0)
        
        # Calculate gaps
        cps_gap = abs(h_cps - b_cps)
        cps_gap_pct = (cps_gap / h_cps * 100) if h_cps > 0 else 0
        
        var_gap = abs(h_var - b_var)
        var_gap_pct = ((b_var / h_var - 1) * 100) if h_var > 0 else 0
        
        std_gap = abs(h_std - b_std)
        std_gap_pct = ((b_std / h_std - 1) * 100) if h_std > 0 else 0
        
        # Calculate realism score (0-100)
        variance_score = min(100, (b_var / h_var * 100)) if h_var > 0 else 0
        cps_score = max(0, 100 - cps_gap_pct)
        std_score = min(100, (b_std / h_std * 100)) if h_std > 0 else 0
        
        realism_score = (variance_score * 0.5 + cps_score * 0.3 + std_score * 0.2)
        
        # Generate report
        report = f"""
══════════════════════════════════════════════════════════════════════════════
DIFFERENTIAL ANALYSIS - HUMAN vs BOT
══════════════════════════════════════════════════════════════════════════════

SELECTED SESSIONS:
──────────────────────────────────────────────────────────────────────────────
Human:  {h_type.upper()} clicking | {h_clicks} clicks
Bot:    {b_mode.upper()} mode | {b_clicks} clicks

SIDE-BY-SIDE COMPARISON:
──────────────────────────────────────────────────────────────────────────────
                        HUMAN           BOT             GAP
──────────────────────────────────────────────────────────────────────────────
Average CPS:            {h_cps:<8.2f}        {b_cps:<8.2f}        {cps_gap:>6.2f} {"✅" if cps_gap_pct < 15 else "⚠️" if cps_gap_pct < 30 else "❌"}
Variance:               {int(h_var):<8}        {int(b_var):<8}        {var_gap_pct:>+6.1f}% {"✅" if abs(var_gap_pct) < 20 else "⚠️" if abs(var_gap_pct) < 40 else "❌"}
Std Deviation:          {h_std:<8.2f}        {b_std:<8.2f}        {std_gap_pct:>+6.1f}% {"✅" if abs(std_gap_pct) < 20 else "⚠️" if abs(std_gap_pct) < 40 else "❌"}

══════════════════════════════════════════════════════════════════════════════
REALISM SCORE: {realism_score:.1f}/100
══════════════════════════════════════════════════════════════════════════════

Bot Detection Risk: {b_risk} (Score: {b_score}/100)

COMPONENT SCORES:
  • Variance Match:     {variance_score:.1f}/100  (50% weight)
  • CPS Similarity:     {cps_score:.1f}/100  (30% weight)
  • Std Dev Match:      {std_score:.1f}/100  (20% weight)

ANALYSIS:
──────────────────────────────────────────────────────────────────────────────
"""
        
        # Add specific recommendations
        recommendations = []
        
        if var_gap_pct < -30:
            recommendations.append(f"⚠️  Bot variance is {abs(var_gap_pct):.1f}% LOWER than human")
            recommendations.append(f"    → Increase variance by {abs(var_gap_pct):.1f}% (target: {int(h_var)})")
        elif var_gap_pct > 30:
            recommendations.append(f"✅ Bot variance is {var_gap_pct:.1f}% HIGHER than human (good variation)")
        else:
            recommendations.append(f"✅ Variance gap is acceptable ({var_gap_pct:+.1f}%)")
        
        if cps_gap_pct > 20:
            recommendations.append(f"⚠️  CPS gap is {cps_gap_pct:.1f}% (human: {h_cps:.1f}, bot: {b_cps:.1f})")
            if b_cps < h_cps:
                recommendations.append(f"    → Bot is too slow - reduce delays by ~{cps_gap_pct/2:.0f}%")
            else:
                recommendations.append(f"    → Bot is too fast - increase delays by ~{cps_gap_pct/2:.0f}%")
        else:
            recommendations.append(f"✅ CPS similarity is good (gap: {cps_gap_pct:.1f}%)")
        
        if std_gap_pct < -25:
            recommendations.append(f"⚠️  Bot std dev is {abs(std_gap_pct):.1f}% LOWER (too consistent)")
            recommendations.append(f"    → Add more rhythm/drift variation")
        else:
            recommendations.append(f"✅ Standard deviation is acceptable")
        
        if realism_score >= 80:
            recommendations.append(f"\n🎉 EXCELLENT - Bot closely matches human pattern!")
            recommendations.append(f"    Anti-cheat compliance: VERY HIGH")
        elif realism_score >= 60:
            recommendations.append(f"\n⚡ GOOD - Bot is reasonably realistic")
            recommendations.append(f"    Minor improvements recommended above")
        else:
            recommendations.append(f"\n🚨 NEEDS IMPROVEMENT - Bot pattern too different from human")
            recommendations.append(f"    Follow recommendations above to improve")
        
        for rec in recommendations:
            report += rec + "\n"
        
        report += f"""
══════════════════════════════════════════════════════════════════════════════
ACTION ITEMS:
══════════════════════════════════════════════════════════════════════════════
"""
        
        if realism_score < 70:
            report += f"1. Increase bot variance to match {h_type} clicking\n"
            report += f"2. Review Settings → Adaptive Mode parameters\n"
            report += f"3. Allow more CPS spikes (15-16)\n"
            report += f"4. Record more {h_type} training data for better baseline\n"
        else:
            report += f"✅ Current configuration is performing well!\n"
            report += f"✅ Bot realism score: {realism_score:.1f}/100\n"
            report += f"✅ Continue monitoring in Analytics tab\n"
        
        report += f"""
══════════════════════════════════════════════════════════════════════════════
"""
        
        return report
    
    
    def create_metric_row(self, parent, label_text, var_name, row):
        """Create metric row for analytics"""
        label = tk.Label(
            parent,
            text=f"{label_text}:",
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
        
        # Update content when switching pages
        if page_idx == 3 and self.engine:  # Graphs page
            if len(self.engine.cps_history) >= 2:
                self.cps_graph.draw_graph(self.engine.cps_history, self.engine.cps_timestamps)
            if len(self.engine.all_delays) >= 5:
                mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
                std_dev = self.engine.calculate_std_dev()
                self.histogram.draw_histogram(self.engine.all_delays, mean, std_dev, self.enhanced_mode)
        
        elif page_idx == 5:  # History page
            self.update_history_list()
        
        elif page_idx == 6:  # Differential page
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
        keyboard.add_hotkey('enter', self.toggle_active)
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
    
    
    def toggle_enhanced_mode(self):
        """Toggle between enhanced and standard mode"""
        self.enhanced_mode = not self.enhanced_mode
        
        if self.enhanced_mode:
            self.mode_indicator.config(text="⚡ Enhanced Adaptive Mode", fg=self.enhanced_color)
            self.enhanced_status.config(text="Status: Enabled (Adaptive Mixed Mode)", fg=self.enhanced_color)
            self.enhanced_btn.config(bg=self.enhanced_color)
            print("\n[ENHANCED MODE] Activated - Adaptive mixed techniques!\n")
        else:
            self.mode_indicator.config(text="Standard Mode", fg="#888888")
            self.enhanced_status.config(text="Status: Disabled", fg="#888888")
            self.enhanced_btn.config(bg=self.button_color)
            print("\n[STANDARD MODE] Enhanced mode disabled.\n")
        
        if self.active:
            self.engine = AdaptiveClickerEngine(enhanced_mode=self.enhanced_mode)
            print(f"[MODE SWITCH] Clicker restarted.\n")
    
    
    def toggle_active(self):
        """Toggle auto-clicker on/off"""
        self.active = not self.active
        
        if self.active:
            self.engine = AdaptiveClickerEngine(enhanced_mode=self.enhanced_mode)
            self.status_indicator.config(text="● ACTIVE", fg=self.accent_color)
            self.click_status.config(text="Hold MB5 to click", fg=self.fg_color)
            self.toggle_btn.config(text="⏹️ Deactivate (F4)", bg=self.inactive_color)
        else:
            self.clicking = False
            if self.engine and self.engine.is_actively_clicking:
                self.engine.stop_clicking()
            self.status_indicator.config(text="● INACTIVE", fg=self.inactive_color)
            self.click_status.config(text="Session ended - Check Analytics", fg="#888888")
            self.toggle_btn.config(text="🚀 Activate (F4)", bg=self.accent_color)
            
            if self.engine:
                self.last_session_stats = self.engine.get_detailed_stats()
                if self.last_session_stats:
                    self.add_session_to_history(self.last_session_stats)
    
    
    def add_session_to_history(self, stats):
        """Add completed session to history"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        mode = "enhanced" if stats.get('enhanced_mode', False) else "standard"
        
        risk_assessment = RiskAssessor.assess(stats)
        
        session = {
            "timestamp": timestamp,
            "mode": mode,
            "clicks": stats['total'],
            "avg_cps": stats['avg_cps'],
            "variance": stats['variance'],
            "risk": risk_assessment['risk'],
            "score": risk_assessment['score']
        }
        
        self.session_history.append(session)
        self.update_history_display()
    
    
    def update_history_display(self):
        """Update session history text widget"""
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete("1.0", tk.END)
        
        if not self.session_history:
            self.history_text.insert("1.0", "No sessions yet.")
        else:
            header = f"{'Time':<10} {'Mode':<10} {'Clicks':<8} {'CPS':<8} {'Var':<8} {'Score':<8} {'Risk':<8}\n"
            self.history_text.insert("1.0", header)
            self.history_text.insert("2.0", "-" * 70 + "\n")
            
            for session in reversed(self.session_history[-10:]):
                line = f"{session['timestamp']:<10} {session['mode']:<10} {session['clicks']:<8} "
                line += f"{session['avg_cps']:<8.1f} {int(session['variance']):<8} "
                line += f"{session['score']:<8.0f} {session['risk']:<8}\n"
                self.history_text.insert(tk.END, line)
        
        self.history_text.config(state=tk.DISABLED)
    
    
    def select_training_type(self, training_type):
        """Select training type"""
        # Reset buttons
        self.butterfly_btn.config(bg=self.button_color)
        self.jitter_btn.config(bg=self.button_color)
        self.normal_btn.config(bg=self.button_color)
        
        # Highlight selected
        if training_type == "butterfly":
            self.butterfly_btn.config(bg=self.training_color)
            self.training_type_label.config(
                text="Selected: Butterfly (2-finger alternating)",
                fg=self.training_color
            )
        elif training_type == "jitter":
            self.jitter_btn.config(bg=self.training_color)
            self.training_type_label.config(
                text="Selected: Jitter (rapid wrist tension)",
                fg=self.training_color
            )
        elif training_type == "normal":
            self.normal_btn.config(bg=self.training_color)
            self.training_type_label.config(
                text="Selected: Normal (single finger tap)",
                fg=self.training_color
            )
        
        self.selected_training_types = [training_type]
        
        if not self.human_tracker.is_tracking:
            self.training_status_label.config(
                text=f"Ready to train {training_type.upper()} - Press F7",
                fg=self.training_color
            )
    
    
    def toggle_training_mode(self):
        """Toggle training mode"""
        if self.active:
            messagebox.showwarning("Auto-Clicker Active", "Disable auto-clicker before training!")
            return
        
        if not self.human_tracker.is_tracking:
            if not self.selected_training_types:
                messagebox.showwarning("No Type Selected", "Select a click type first!")
                return
            
            training_type = self.selected_training_types[0]
            self.human_tracker.start_tracking(training_type)
            self.status_indicator.config(text=f"● TRAINING: {training_type.upper()}", fg=self.training_color)
            self.click_status.config(text=f"Recording {training_type} clicks...", fg=self.training_color)
            self.training_status_label.config(
                text=f"🔴 RECORDING {training_type.upper()} - Click naturally!",
                fg=self.inactive_color
            )
            self.train_start_btn.config(text="⏹️ Stop Training (F7)", bg=self.inactive_color)
        else:
            self.human_tracker.stop_tracking()
            self.status_indicator.config(text="● INACTIVE", fg=self.inactive_color)
            self.click_status.config(text="Training complete - Press F8", fg="#888888")
            training_type = self.human_tracker.training_type
            self.training_status_label.config(
                text=f"✅ Complete - {self.human_tracker.total_clicks} {training_type} clicks",
                fg=self.accent_color
            )
            self.train_start_btn.config(text="🎬 Start Training (F7)", bg=self.training_color)
    
    
    def export_human_baseline(self):
        """Export training baseline"""
        if self.human_tracker.is_tracking:
            messagebox.showinfo("Training Active", "Stop training (F7) before exporting!")
            return
        
        self.human_tracker.export_human_stats()
        # Refresh history page
        self.update_history_list()
        self.update_differential_options()
    
    
    def export_stats(self):
        """Export detailed TXT stats with UTF-8 encoding and session tracking"""
        if not self.last_session_stats:
            messagebox.showwarning("No Data", "Complete a session first!")
            return
        
        stats = self.last_session_stats
        mode_text = "Enhanced (Adaptive)" if stats.get('enhanced_mode', False) else "Standard"
        
        risk_assessment = RiskAssessor.assess(stats)
        
        report = f"""
══════════════════════════════════════════════════════════════════════════════
MINECRAFT AUTO CLICKER v3.6 - SESSION REPORT
══════════════════════════════════════════════════════════════════════════════
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Mode: {mode_text}
Current Technique: {stats.get('current_technique', 'mixed').upper()}

SESSION OVERVIEW
──────────────────────────────────────────────────────────────────────────────
Total Clicks:              {stats['total']}
Session Duration:          {stats['session_duration']:.1f}s
Active Clicking Time:      {stats['clicking_duration']:.1f}s
Idle Time:                 {stats['idle_time']:.1f}s
Uptime Percentage:         {(stats['clicking_duration']/stats['session_duration']*100):.1f}%

CPS STATISTICS
──────────────────────────────────────────────────────────────────────────────
Average CPS:               {stats['avg_cps']:.2f}
Median CPS:                {stats['median_cps']:.2f}
Minimum CPS:               {stats['min_cps']:.2f}
Maximum CPS:               {stats['max_cps']:.2f}
CPS Range:                 {stats['max_cps'] - stats['min_cps']:.2f}

DELAY STATISTICS (milliseconds)
──────────────────────────────────────────────────────────────────────────────
Average Delay:             {stats['avg_delay']:.2f} ms
Median Delay (P50):        {stats['p50_delay']:.2f} ms
10th Percentile (P10):     {stats['p10_delay']:.2f} ms
90th Percentile (P90):     {stats['p90_delay']:.2f} ms
Min Delay:                 {stats['min_delay']:.2f} ms
Max Delay:                 {stats['max_delay']:.2f} ms
Delay Range:               {stats['max_delay'] - stats['min_delay']:.2f} ms

ANTI-DETECTION METRICS
──────────────────────────────────────────────────────────────────────────────
Variance:                  {stats['variance']:.0f}
Standard Deviation:        {stats['std_dev']:.2f}
Pattern Breaks:            {stats['pattern_breaks']}
Variance Adjustments:      {stats['variance_adjustments']}
Burst Events:              {stats.get('burst_count', 0)}
Pause Events:              {stats.get('pause_count', 0)}
Outlier Injections:        {stats.get('outlier_count', 0)}

DETECTION RISK ASSESSMENT (v3.6)
──────────────────────────────────────────────────────────────────────────────
Risk Level:                {risk_assessment['risk']}
Risk Score:                {risk_assessment['score']}/100
Status:                    {risk_assessment['status']}

RECOMMENDATIONS
──────────────────────────────────────────────────────────────────────────────
"""
        
        if risk_assessment['recommendations']:
            for rec in risk_assessment['recommendations']:
                report += f"  • {rec}\n"
        else:
            report += "  ✅ No improvements needed - performing optimally!\n"
        
        report += f"""

══════════════════════════════════════════════════════════════════════════════
v3.6 ADAPTIVE INTELLIGENCE FEATURES
══════════════════════════════════════════════════════════════════════════════
✅ Mixed mode clicking (butterfly/jitter/normal blend)
✅ Relaxed CPS ceiling (allows 15-16 spikes)
✅ Realistic variance targets (1,500-2,500)
✅ Statistical outlier injection (2% rate)
✅ Session tracking and comparison
✅ Differential analysis available

Use Compare tab (Page 7) to analyze vs human training data!

══════════════════════════════════════════════════════════════════════════════
FILE SAVED TO: Desktop/training_data/clickerData/
══════════════════════════════════════════════════════════════════════════════
"""
        
        print(report)
        
        # Create filename
        mode_suffix = "_adaptive" if stats.get('enhanced_mode', False) else "_standard"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clicker_stats{mode_suffix}_{timestamp}.txt"
        
        # Get clicker data path
        clicker_data_path = Config.get_clicker_data_path()
        
        try:
            os.makedirs(clicker_data_path, exist_ok=True)
            full_path = os.path.join(clicker_data_path, filename)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(report)
            
            # Add to session manager
            self.session_manager.add_clicker_session(stats, full_path)
            
            print(f"[SUCCESS] Stats exported to: {full_path}\n")
            print(f"[INFO] Added to session history\n")
            messagebox.showinfo(
                "Export Success", 
                f"Stats saved to:\n{full_path}\n\n✅ Added to session history\n\nView in History/Compare tabs!"
            )
        except Exception as e:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"[SUCCESS] Stats exported to current directory: {filename}\n")
                messagebox.showinfo("Export Success (Current Dir)", f"Stats saved to:\n{filename}")
            except Exception as e2:
                print(f"[ERROR] Export failed: {e2}\n")
                messagebox.showerror("Export Failed", str(e2))
    
    
    def export_csv(self):
        """Export session data to CSV"""
        if not self.engine or not self.engine.all_delays:
            messagebox.showwarning("No Data", "No click data to export!")
            return
        
        mode_suffix = "_adaptive" if self.enhanced_mode else "_standard"
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"clicker_data{mode_suffix}_{timestamp}.csv"
        
        clicker_data_path = Config.get_clicker_data_path()
        
        try:
            os.makedirs(clicker_data_path, exist_ok=True)
            full_path = os.path.join(clicker_data_path, filename)
            
            if self.engine.export_to_csv(full_path):
                print(f"[SUCCESS] CSV exported to: {full_path}\n")
                messagebox.showinfo("Export Success", f"CSV saved to:\n{full_path}")
            else:
                raise Exception("CSV export failed")
        except Exception as e:
            try:
                if self.engine.export_to_csv(filename):
                    print(f"[SUCCESS] CSV exported to current directory: {filename}\n")
                    messagebox.showinfo("Export Success (Current Dir)", f"CSV saved to:\n{filename}")
                else:
                    raise Exception("CSV export failed")
            except Exception as e2:
                print(f"[ERROR] CSV export failed: {e2}\n")
                messagebox.showerror("Export Failed", str(e2))
    
    
    def toggle_mini_mode(self):
        """Toggle mini-mode"""
        messagebox.showinfo("Mini Mode", "Mini-mode overlay coming in v4.0!\n\nPlanned features:\n• Compact transparent overlay\n• Real-time CPS display\n• Risk indicator\n• In-game use")
    
    
    def is_mb5_held(self):
        """Check if MB5 is held"""
        return win32api.GetAsyncKeyState(Config.VK_XBUTTON2) < 0
    
    
    def mouse_monitor(self):
        """Monitor mouse buttons"""
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
        """Main clicking loop"""
        while self.running:
            if self.active and self.clicking:
                self.engine.click()
            else:
                time.sleep(0.01)
    
    
    def update_display(self):
        """Update all GUI elements"""
        if self.active and self.engine:
            # Update status
            if self.clicking:
                self.click_status.config(text="⚔️ CLICKING", fg=self.accent_color)
            else:
                self.click_status.config(text="Waiting for MB5...", fg="#888888")
            
            # Update timer
            elapsed = (datetime.now() - self.engine.session_start).total_seconds()
            self.session_timer.config(text=f"⏱️ {self.format_time_elapsed(elapsed)}")
            
            # Update dashboard cards
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
                    
                    # Risk assessment
                    risk_assessment = RiskAssessor.assess(stats)
                    self.risk_card.config(text=risk_assessment['risk'], fg=risk_assessment['color'])
                    
                    # Analytics page
                    self.risk_level.config(text=risk_assessment['risk'], fg=risk_assessment['color'])
                    self.risk_score.config(text=f"{risk_assessment['score']}/100")
                    self.burst_events.config(text=str(stats.get('burst_count', 0)))
                    self.pause_events.config(text=str(stats.get('pause_count', 0)))
                    self.outlier_count.config(text=str(stats.get('outlier_count', 0)))
                    
                    # Update graphs if on graphs page
                    if self.current_page == 3:
                        if len(self.engine.cps_history) >= 2:
                            self.cps_graph.draw_graph(self.engine.cps_history, self.engine.cps_timestamps)
                        if len(self.engine.all_delays) >= 5:
                            mean = sum(self.engine.all_delays) / len(self.engine.all_delays)
                            self.histogram.draw_histogram(self.engine.all_delays, mean, std_dev, self.enhanced_mode)
        
        elif self.human_tracker.is_tracking:
            self.total_clicks_card.config(text=str(self.human_tracker.total_clicks))
            self.current_cps_card.config(text="TRAIN")
            
            # Training progress
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
            # Reset display
            self.total_clicks_card.config(text="0")
            self.current_cps_card.config(text="--")
            self.variance_card.config(text="--")
            self.std_dev_card.config(text="--")
            self.avg_cps_card.config(text="--")
            self.risk_card.config(text="--", fg=self.accent_color)
            self.session_timer.config(text="⏱️ 0:00")
            self.training_progress.config(text="")
        
        self.root.after(500, self.update_display)
    
    
    def start_threads(self):
        """Start background threads"""
        click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
        mouse_thread = threading.Thread(target=self.mouse_monitor, daemon=True)
        click_thread.start()
        mouse_thread.start()
    
    
    def on_close(self):
        """Clean shutdown"""
        if self.engine and self.engine.is_actively_clicking:
            self.engine.stop_clicking()
        self.running = False
        self.root.destroy()
    
    
    def run(self):
        """Run the application"""
        self.root.mainloop()


# ═════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        
        if not is_admin:
            print("\n⚠️  ERROR: Administrator privileges required")
            print("Right-click → 'Run as Administrator'\n")
            input("Press Enter to exit...")
            exit(1)
        
        print("═" * 70)
        print("MINECRAFT AUTO CLICKER v3.6 - ADAPTIVE INTELLIGENCE")
        print("═" * 70)
        print("\n✨ NEW IN v3.6:")
        print("  ✅ Adaptive Mixed Mode (blends butterfly/jitter/normal)")
        print("  ✅ Relaxed CPS ceiling (allows 15-16 spikes)")
        print("  ✅ Revised Risk Assessment (1,500-2,500 variance targets)")
        print("  ✅ Training Session History (Page 6)")
        print("  ✅ Differential Analysis (Page 7 - Human vs Bot)")
        print("  ✅ Statistical Outlier Injection (2% rate)")
        print("  ✅ Comprehensive Risk Scoring (0-100 points)")
        print("  ✅ Session database (sessions.json)")
        print("\n🎯 FEATURES:")
        print("  • 7 pages: Dashboard, Settings, Analytics, Graphs,")
        print("              Training, History, Compare")
        print("  • Real-time CPS graphing")
        print("  • Click delay histograms")
        print("  • Human baseline training")
        print("  • Data-driven improvement recommendations")
        print("\n📁 DATA ORGANIZATION:")
        print("  Desktop/training_data/")
        print("    ├── clickerData/     ← Bot sessions")
        print("    ├── butterfly/       ← Training data")
        print("    ├── jitter/          ← Training data")
        print("    ├── normal/          ← Training data")
        print("    └── sessions.json    ← History DB")
        print("\nStarting GUI...\n")
        
        app = AutoClickerGUI()
        app.run()
        
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
