# ⚙️ Mimic v3.7 - Statistical Ghost Clicker

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-Educational-orange.svg)

> **Adaptive Intelligence • Statistical Mimicry**

Mimic is a sophisticated auto-clicker designed for Minecraft 1.8.9 PvP that uses statistical distributions and adaptive algorithms to replicate human clicking patterns. Built specifically to target anti-cheat systems like MMC's AGC with variance-based detection [web:75].

---

## 🎯 Features

### **Core Functionality**
- **Hold-to-Click Activation** - Natural left-click hold interface using pynput [web:112]
- **Adaptive Mixed Mode** - Dynamically blends butterfly/jitter/normal clicking techniques
- **Statistical Engine** - Gaussian (Box-Muller) + Weibull distributions for realistic delays
- **Variance Targeting** - Configurable 1,500-2,500 variance range (optimal for AGC bypass)
- **Real-Time Risk Assessment** - Live detection risk scoring (0-100)

### **Anti-Detection Systems**
- ✅ Pattern break detection with dynamic adjustment
- ✅ 2% outlier injection (micro-pauses, panic bursts)
- ✅ Session re-randomization for behavioral diversity
- ✅ Drift accumulation and rhythm oscillation
- ✅ Configurable burst/pause mechanics

### **Analysis & Training**
- 📊 Real-time CPS graphing and delay distribution histograms
- 🎓 Human baseline training mode (butterfly/jitter/normal)
- 🔬 Differential analysis (compare human vs bot patterns)
- 📈 Session history tracking with JSON persistence
- 💾 CSV/TXT export for external analysis

---

## 📋 Requirements

Python 3.8+
pip install pywin32
pip install pynput
pip install keyboard

text

**Platform:** Windows only (uses Win32 API for mouse events)

---

## 🚀 Quick Start

1. **Install dependencies:**

python -m pip install pywin32 pynput keyboard

text

2. **Run Mimic:**

python mimic.py

text

3. **Activate & Click:**
- Press `F4` to enable
- Hold `LEFT CLICK` to auto-click
- Release to stop

---

## ⌨️ Keyboard Controls

| Key | Action |
|-----|--------|
| `F4` | Toggle On/Off |
| `LEFT CLICK` | Auto-Click (Hold) |
| `F5` | Export TXT Stats |
| `F6` | Export CSV Data |
| `F7` | Start/Stop Training |
| `F8` | Export Training Data |
| `F9` | Toggle Enhanced Mode |
| `F10` | Mini Mode (Coming Soon) |
| `← →` | Navigate Pages |
| `Enter` | Quick Toggle |

---

## 🎨 GUI Overview

### **7-Tab Interface:**
1. **Dashboard** - Live stats, risk assessment, quick actions
2. **Settings** - Mode configuration, export paths, controls
3. **Analytics** - Detection metrics, session history
4. **Graphs** - Real-time CPS line graph, delay histograms
5. **Training** - Record human baseline clicking patterns
6. **History** - View all training sessions
7. **Compare** - Differential analysis (human vs bot)

---

## 📊 Target Metrics

### **Enhanced Mode (Recommended)**
- **CPS Range:** 7-12 average, 15-16 spikes allowed
- **Target Variance:** 2,200 (optimal for AGC)
- **Acceptable Range:** 1,500-3,500
- **Detection Risk:** LOW (score 80+)

### **Standard Mode**
- **CPS Range:** 5-9 average, 11-13 spikes
- **Target Variance:** 900
- **Acceptable Range:** 600-1,500
- **Detection Risk:** LOW (score 70+)

---

## 🧪 Testing Strategy

Based on anti-cheat research for 1.8.9 PvP servers [web:75][web:84]:

### **Phase 1: Hypixel (Week 1)**
- Server: `mc.hypixel.net`
- Anti-Cheat: Watchdog
- Goal: 30+ minute sessions undetected
- Game Modes: Duels → BedWars/SkyWars

### **Phase 2: Extended Testing (Week 2)**
- Increase to 1-2 hour sessions
- Monitor variance/CPS when flagged (if any)
- Adjust settings based on results

### **Phase 3: MMC Final Test (Week 3+)**
- Server: `na.minemen.club` / `eu.minemen.club`
- Anti-Cheat: AGC (AntiGamingChair) - Most strict
- Goal: 30+ minutes undetected = success
- **Use alt accounts for testing**

---

## 📁 File Organization

Desktop/mimic_data/
├── mimicSessions/ # Auto-clicker exports (F5/F6)
│ ├── mimic_session_.txt
│ └── mimic_data_.csv
├── butterfly/ # Training data
├── jitter/ # Training data
├── normal/ # Training data
├── mixed/ # Training data
└── sessions.json # Session history database

text

---

## 🔧 Advanced Tuning

Accessible in **Settings → Advanced Tuning**:

- **Pause Probability:** 0-20% (default: 10%)
- **Pause Duration:** 50-500ms (default: 200-450ms)
- **Burst Probability:** 0-50% (default: 20%)
- **Target Variance:** 800-3500 (default: 2200)

Fine-tune these during gameplay to balance hit registration vs detection risk.

---

## ⚠️ Disclaimer

**Educational purposes only.** This tool is designed for:
- Understanding anti-cheat detection systems
- Statistical analysis of human input patterns
- Research into behavioral biometrics

Use at your own risk. The author is not responsible for any bans or violations of server terms of service.

---

## 🛠️ Technical Details

### **Statistical Methods:**
- **Box-Muller Transform** - Gaussian random distribution
- **Weibull Distribution** - Long-tail delay modeling
- **Rolling Window Variance** - Pattern consistency analysis
- **Drift Accumulation** - Simulates finger fatigue

### **Architecture:**
- Multi-threaded design (GUI + listener + clicker loops)
- pynput for physical input detection with `injected` flag filtering
- Win32 API for synthetic mouse events
- Session persistence via JSON

---

## 📝 Version History

### **v3.7.0** (Current)
- ✅ Left-click hold activation (pynput integration)
- ✅ Ghost Stealth UI rebrand
- ✅ Advanced tuning sliders in GUI
- ✅ Improved race condition handling
- ✅ Session history tracking

### **v3.0-3.6**
- Statistical engine development
- Multi-mode support
- Training system implementation
- Risk assessment framework

---

## 🤝 Contributing

Interested in playtesting or contributing data?

1. Test on Hypixel/MMC
2. Record detection times (if any)
3. Export session data (F6)
4. Share anonymized results

---

## 📜 License

Educational use only.

---

<div align="center">

**Built with statistical precision for the 1.7.10/1.8.9 PvP community**

[Report Bug](https://github.com/yourusername/mimic/issues) • [Request Feature](https://github.com/yourusername/mimic/issues)

</div>
