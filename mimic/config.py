"""Configuration, risk assessment, and click-engine presets.

Part of Mimic. Split out of the original single-file Mimic.py.
"""

import os
import json
from pathlib import Path


class Config:
    """Global configuration with realistic anti-cheat thresholds"""
    
    # Bounds fitted to click_data/ (chatter-free sessions only).
    # Real observed: min 33.5ms, p01 58ms, p99 308ms, max 475ms.
    ABSOLUTE_MIN_DELAY_MS = 30   # 33.3 CPS spike max
    ABSOLUTE_MAX_DELAY_MS = 450  # was 250, which clipped 1.85% of real pauses
    SUSTAINED_CPS_CAP = 11       # true human peak was 9.67 CPS once chatter removed

    # Enhanced Mode has wider range
    ENHANCED_MIN_DELAY_MS = 30   # 33.3 CPS spike max
    ENHANCED_MAX_DELAY_MS = 450  # humans do pause; the old ceiling never let us

    # Gaussian distribution parameters (measured, not guessed)
    ENHANCED_TARGET_MEAN_MS = 111      # clean-session mean (was 65 -- never matched)
    ENHANCED_TARGET_STD_DEV_MS = 42    # clean-session std dev (this one was right)

    # Realistic variance targets -- real clean-session variance is ~2789
    ENHANCED_IDEAL_VARIANCE = 1800   # Minimum acceptable
    ENHANCED_TARGET_VARIANCE = 2800  # Optimal butterfly/jitter
    ENHANCED_MAX_VARIANCE = 4200     # Upper bound
    
    STANDARD_IDEAL_VARIANCE = 600    # Minimum acceptable
    STANDARD_TARGET_VARIANCE = 900   # Optimal normal clicking
    STANDARD_MAX_VARIANCE = 1500     # Upper bound
    
    # Anti-Detection Thresholds
    MIN_VARIANCE_THRESHOLD = 800
    PATTERN_CHECK_WINDOW = 20

    # Hardware emulation. A real mouse only raises events on a USB polling
    # boundary, so human intervals cluster near whole milliseconds. Set
    # POLL_RATE_HZ to the polling rate of the mouse you want to look like
    # (125 / 500 / 1000), or None to disable quantization entirely.
    POLL_RATE_HZ = 1000
    POLL_JITTER_MS = 0.19    # measured spread around the grid in click_data/

    # Drift is an Ornstein-Uhlenbeck process: DRIFT_REVERSION is the per-click
    # retention (closer to 1.0 = slower wander), DRIFT_SIGMA its steady-state
    # amplitude as a fraction of the base interval.
    DRIFT_REVERSION = 0.985
    DRIFT_SIGMA = 0.055

    # Double-click (switch bounce) emulation.
    # A double-clicking mouse is standard kit in Minecraft PvP: each physical
    # press registers twice, so effective CPS is roughly 1 + DOUBLE_RATE times
    # the hand rate. Mimic drives the OS click API directly, which bypasses the
    # switch entirely -- so with this off, synthetic clicks carry NO doubles,
    # while the same account's manual play is 20-44% doubles. Turning it on
    # keeps the click stream consistent with the hardware the account has
    # always used, and raises combat output without raising the hand rate.
    #
    # Values measured from the operator's own recordings in click_data/:
    # doubles land 34.0ms +/- 0.68ms after the real press, on 20.7-42.9% of
    # presses depending on session.
    DOUBLE_CLICK_EMULATION = False
    DOUBLE_RATE = 0.30
    DOUBLE_GAP_MS = 34.0
    DOUBLE_GAP_STD_MS = 0.68
    DOUBLE_HOLD_MS = 8.0
    
    # Adaptive mode parameters
    TECHNIQUE_TRANSITION_MIN = 5   # Min clicks before switching
    TECHNIQUE_TRANSITION_MAX = 15  # Max clicks before switching
    
    # Click mode Parameters
    BURST_PROBABILITY = 0.40
    PAUSE_PROBABILITY = 0.02
    BURST_DURATION = (2, 6)
    PAUSE_DURATION_MS = (150, 200)
    
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
        return os.path.join(desktop, "Mimic","mimic_data")
    
    @staticmethod
    def get_clicker_data_path():
        """Get path to Desktop/mimic_data/mimicSessions/"""
        return os.path.join(Config.get_training_data_path(), "mimicSessions")
    
    @staticmethod
    def get_sessions_file():
        """Get path to sessions database"""
        return os.path.join(Config.get_training_data_path(), "sessions.json")


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
        
        score = 0 # Constantly check score to ensure variance is within tolerance
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
            status = "🚨 DANGEROUS - Click Normally for 10 or more minutes"
        
        return {
            "risk": risk,
            "score": score,
            "color": color,
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
            "thresholds": thresholds
        }


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
        return RiskVisualization.RISK_LEVELS[-1] 


class ClickEnginePresets:
    """Predefined configurations for different clicking styles"""
    
    # Anchored to the operator's own chatter-free recordings in click_data/
    # (mean 110.8ms, std 42.4ms, median 94ms, ~9.0 CPS). The previous values
    # targeted 65-85ms / ~13 CPS, which no session in the training data ever
    # reached once switch chatter was discounted -- they were faster than the
    # human they were supposed to imitate.
    #
    # mean/std are absolute milliseconds; the engine moment-matches them onto
    # its log-normal draw in AdaptiveClickerEngine.set_preset().
    PRESETS = {
        "Conservative": {
            "description": "Slower than your baseline - safest, lowest variance flags",
            "butterfly_mean": 108,
            "butterfly_std": 38,
            "jitter_mean": 122,
            "jitter_std": 44,
            "normal_mean": 134,
            "normal_std": 50,
            "burst_mean": 92,
            "burst_std": 26,
            "burst_max_clamp": 70,
            "variance_target": 2400,
            "risk_level": "Low"
        },

        "Balanced": {
            "description": "(Recommended) - matches your measured human baseline",
            "butterfly_mean": 96,
            "butterfly_std": 36,
            "jitter_mean": 108,
            "jitter_std": 42,
            "normal_mean": 120,
            "normal_std": 47,
            "burst_mean": 82,
            "burst_std": 24,
            "burst_max_clamp": 60,
            "variance_target": 2800,
            "risk_level": "Medium"
        },

        "Aggressive": {
            "description": "Faster than your baseline - stays under the CPS cap",
            "butterfly_mean": 82,
            "butterfly_std": 32,
            "jitter_mean": 92,
            "jitter_std": 38,
            "normal_mean": 102,
            "normal_std": 42,
            "burst_mean": 70,
            "burst_std": 20,
            "burst_max_clamp": 52,
            "variance_target": 3000,
            "risk_level": "High"
        },
    }
    
    @staticmethod
    def apply_preset(engine, preset_name):
        """Apply a preset to the engine"""
        if preset_name not in ClickEnginePresets.PRESETS:
            return False
        
        preset = ClickEnginePresets.PRESETS[preset_name]
        engine.preset_name = preset_name
        engine.preset_config = preset
        return True
    
    @staticmethod
    def get_preset_list():
        """Return list of available presets"""
        return list(ClickEnginePresets.PRESETS.keys())


class PresetManager:
    """Persist user-created presets to disk"""
    
    PRESETS_FILE = Path.home() / "Desktop" / "mimic_data" / "custom_presets.json"
    
    @staticmethod
    def load_custom_presets():
        """Load saved presets from file"""
        try:
            if PresetManager.PRESETS_FILE.exists():
                with open(PresetManager.PRESETS_FILE, 'r') as f:
                    custom = json.load(f)
                    ClickEnginePresets.PRESETS.update(custom)
                    print(f"[PRESET] Loaded {len(custom)} custom presets")
        except Exception as e:
            print(f"[WARNING] Could not load presets: {e}")
    
    @staticmethod
    def save_preset(name, config):
        """Save a new preset to file"""
        try:
            PresetManager.PRESETS_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            custom = {}
            if PresetManager.PRESETS_FILE.exists():
                with open(PresetManager.PRESETS_FILE, 'r') as f:
                    custom = json.load(f)
            
            custom[name] = config
            
            with open(PresetManager.PRESETS_FILE, 'w') as f:
                json.dump(custom, f, indent=2)
            
            ClickEnginePresets.PRESETS[name] = config
            print(f"[PRESET] Saved: {name}")
            return True
        except Exception as e:
            print(f"[ERROR] Could not save preset: {e}")
            return False
