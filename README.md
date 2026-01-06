# Mimic: Undetectable AutoClicker & Click Benchmark Suite

Mimic is an advanced automation framework designed to simulate human clicking patterns with high statistical fidelity. Unlike traditional macro software that uses fixed delays or simple randomization, Mimic employs a statistical distribution engine (Gaussian and Weibull) to generate click timings that closely resemble human physiological performance.

This project includes two core components:
1. **Mimic v4.0**: The primary automation engine with real-time risk assessment and adaptive pattern switching.
2. **Mimic Benchmark Tool (v1.3.0)**: A standalone analytics utility for recording, analyzing, and benchmarking clicking performance (CPS, consistency, and fatigue).

## Features

### **Core Functionality**
- **Hold-to-Click Activation** - Natural left-click hold interface using pynput
- **Adaptive Mixed Mode** - Dynamically blends butterfly/jitter/normal clicking techniques
- **Statistical Engine** - Gaussian (Box-Muller) + Weibull distributions for realistic delays
- **Variance Targeting** - Configurable 1,500-3,000 variance range (optimal for AGC bypass)
- **Real-Time Risk Assessment** - Live detection risk scoring (0-100)

### **Anti-Detection Systems**
- Pattern break detection with dynamic adjustment
- 2% outlier injection (micro-pauses, panic bursts)
- Session re-randomization for behavioral diversity
- Drift accumulation and rhythm oscillation
- Configurable burst/pause mechanics

### **Analysis & Training**
- Real-time CPS graphing and delay distribution histograms
- Human baseline training mode (butterfly/jitter/normal)
- Differential analysis (compare human vs bot patterns)
- Session history tracking with JSON persistence
- CSV/TXT export for external analysis

---

## Requirements

Python 3.8+
```cmd
pip install pywin32
pip install pynput
pip install keyboard
```

**Platform:** Windows only (uses Win32 API for mouse events)

---

## Quick Start

1. **Install dependencies:**
```cmd
python -m pip install pywin32 pynput keyboard
```

2. **Run Mimic:**
```cmd
python mimic.py
```

3. **Activate & Click:**
- Press `F4` to enable
- Hold `LEFT CLICK` to auto-click
- Release to stop

---

## Keyboard Controls

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

## GUI Overview

### **7-Tab Interface:**
1. **Dashboard** - Live stats, risk assessment, quick actions
2. **Settings** - Mode configuration, export paths, controls
3. **Analytics** - Detection metrics, session history
4. **Graphs** - Real-time CPS line graph, delay histograms
5. **Training** - Record human baseline clicking patterns
6. **History** - View all training sessions
7. **Compare** - Differential analysis (human vs bot)

---

## Target Metrics

### **Enhanced Mode (Recommended)**
- **CPS Range:** 7-12 average, 15-16 spikes allowed
- **Target Variance:** 2,200+ (optimal for AGC)
- **Acceptable Range:** 1,500-3,500
- **Detection Risk:** LOW (score 80+)

---

## Disclaimer

This software is for educational and research purposes only. Using automation tools in online games may violate Terms of Service and result in account bans. The authors accept no responsibility for damages resulting from the use of this tool.
