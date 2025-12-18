# ⚔️ Minecraft Auto Clicker v3.5.1 FINAL

## 🎯 Production-Ready Anti-Cheat Compliant Auto Clicker

A sophisticated auto-clicker designed specifically for Minecraft PvP, featuring advanced anti-detection algorithms, human-like clicking patterns, and comprehensive analytics.

---

## ✨ Features

### 🔧 Core Functionality
- **7-12 CPS Range**: Optimized for Minecraft anti-cheat compliance
- **Enhanced Chaos Mode**: Butterfly clicking simulation with burst/pause mechanics
- **Standard Mode**: Jitter/normal clicking with controlled variance
- **Real-time CPS Monitoring**: Live performance tracking
- **Smart Variance Control**: Dynamic pattern breaking every 10 seconds

### 🎨 User Interface
- **5-Page Dashboard**: Dashboard, Settings, Analytics, Graphs, Training
- **Quick Stats Cards**: Total clicks, CPS, variance, risk level
- **Real-time CPS Graph**: 30-second rolling window visualization
- **Click Delay Histogram**: Distribution analysis with danger zones
- **Session History**: Track performance across multiple sessions

### 📊 Analytics & Export
- **Detailed TXT Reports**: Comprehensive session statistics
- **CSV Data Export**: Raw click data for analysis/AI training
- **Training Mode**: Record human clicking patterns (butterfly/jitter/normal)
- **Risk Assessment**: LOW/MEDIUM/HIGH detection risk ratings
- **Desktop Organization**: Auto-organized folder structure

### 🧠 Anti-Detection Technology
- **Gaussian + Weibull Distributions**: Natural timing variation
- **User Baseline Randomization**: 0.88-1.12x multiplier
- **Drift Accumulation**: ±0.35 max variance shift
- **Rhythm Oscillation**: Sine wave pattern (22ms amplitude)
- **Consecutive Click Fatigue**: Realistic slowdown simulation
- **Pattern Break Detection**: 20-click window monitoring
- **Burst Mode**: 15% probability, 3-8 click bursts
- **Pause Mode**: 8% probability, 250-450ms pauses

---

## 📁 File Organization

All exports save to `Desktop/training_data/`:

Desktop/
└── training_data/
├── clickerData/ ← Auto-clicker session data (F5/F6)
│ ├── clicker_stats_enhanced_YYYYMMDD_HHMMSS.txt
│ └── clicker_data_enhanced_YYYYMMDD_HHMMSS.csv
│
├── butterfly/ ← Human training data (F8)
│ ├── butterfly_baseline_YYYYMMDD_HHMMSS.txt
│ └── butterfly_baseline_YYYYMMDD_HHMMSS.csv
│
├── jitter/ ← Human training data (F8)
│ ├── jitter_baseline_YYYYMMDD_HHMMSS.txt
│ └── jitter_baseline_YYYYMMDD_HHMMSS.csv
│
├── normal/ ← Human training data (F8)
│ ├── normal_baseline_YYYYMMDD_HHMMSS.txt
│ └── normal_baseline_YYYYMMDD_HHMMSS.csv
│
└── mixed/ ← Mixed technique training (F8)

text

---

## ⌨️ Keyboard Controls

| Key      | Action                          |
|----------|---------------------------------|
| **F4**   | Toggle clicker ON/OFF           |
| **Enter**| Quick toggle                    |
| **MB5**  | Hold to click (side mouse button)|
| **F5**   | Export TXT stats report         |
| **F6**   | Export CSV data                 |
| **F7**   | Start/Stop training mode        |
| **F8**   | Export training baseline        |
| **F9**   | Toggle Enhanced/Standard mode   |
| **F10**  | Mini-mode (coming in v3.6)      |
| **← →**  | Navigate pages                  |

---

## 🚀 Installation

### Prerequisites

pip install keyboard
pip install pywin32

text

### Setup
1. Download `minecraft_autoclicker_v3.5.1_final.py`
2. **Run as Administrator** (required for keyboard hooks)
3. Navigate through pages with arrow keys
4. Press F4 to activate, hold MB5 to click

---

## 📖 Usage Guide

### 1️⃣ Auto-Clicker Mode
1. Press **F4** to activate
2. Hold **MB5** (side mouse button) to click
3. Monitor stats on Dashboard
4. Press **F5** to export session report
5. Press **F6** to export CSV data

### 2️⃣ Training Mode (Human Baseline)
1. Navigate to **Training** page (page 5)
2. Select click type: **Butterfly** / **Jitter** / **Normal**
3. Press **F7** to start recording
4. Click naturally (aim for 100+ clicks)
   - Minimum: 100 clicks
   - Recommended: 200 clicks
   - Complete: 250+ clicks
5. Press **F7** to stop recording
6. Press **F8** to export training data

### 3️⃣ Analytics Review
- **Page 1 (Dashboard)**: Quick stats overview
- **Page 2 (Settings)**: Mode controls and hotkeys
- **Page 3 (Analytics)**: Session metrics and history
- **Page 4 (Graphs)**: Real-time CPS + histogram
- **Page 5 (Training)**: Human baseline recording

---

## 🔍 Understanding Risk Levels

### ✅ LOW RISK
- Variance > 250
- Max CPS ≤ 12
- High randomness
- Anti-cheat compliant

### ⚡ MEDIUM RISK
- Variance 120-250
- Acceptable variation
- Monitor performance

### ⚠️ HIGH RISK
- Variance < 120
- Too consistent
- Enable Enhanced Mode (F9)

---

## 🧪 Training Data for AI

### Purpose
Record human clicking patterns to train AI models that can distinguish between:
- Human clicking (butterfly/jitter/normal)
- Auto-clicker patterns

### Best Practices
1. **Butterfly**: 100+ clicks, 2-finger alternating
2. **Jitter**: 100+ clicks, rapid wrist tension
3. **Normal**: 100+ clicks, single finger tapping
4. Export both TXT and CSV for analysis

---

## 🐛 Troubleshooting

### Export Error
✅ **FIXED in v3.5.1**: UTF-8 encoding now handles all Unicode characters

### High Risk Detection
- Enable **Enhanced Chaos Mode** (F9)
- Variance should be 1,500-2,500 for butterfly simulation

### No Clicks Registering
- Ensure running as **Administrator**
- Check MB5 button is working
- Verify clicker is **ACTIVE** (green indicator)

---

## 📊 Technical Details

### Distributions
- **70% Gaussian**: Box-Muller transform
- **30% Weibull**: Shape parameter 2.0-2.2

### Timing Parameters
- **Base delay**: 100ms (enhanced) / 108ms (standard)
- **Variance**: ±28ms (enhanced) / ±22ms (standard)
- **Burst CPS**: Up to 20 CPS for 3-8 clicks
- **Pause duration**: 250-450ms

### Safety Features
- **CPS limiter**: Prevents >11 CPS spikes
- **Pattern detection**: 20-click window monitoring
- **Variance adjustment**: Every 10 seconds

---

## 📝 Version History

### v3.5.1 FINAL (December 18, 2025)
- ✅ Fixed UTF-8 encoding for all file exports
- ✅ Updated training thresholds: 100/200/250
- ✅ Clicker data organized in `clickerData/` folder
- ✅ Fixed header text cutoff (expanded dimensions)
- ✅ Enhanced error messages
- ✅ Production-ready release

### v3.5 (December 18, 2025)
- Added real-time CPS line graph
- Session comparison tool
- CSV export functionality
- Training progress indicators
- Danger zone visualization
- Quick stats cards
- 5-page navigation system

---

## ⚠️ Disclaimer

This tool is for **educational purposes only**. Use of auto-clickers may violate Minecraft server rules and Terms of Service. The developer is not responsible for any bans or penalties resulting from use of this software.

**Use at your own risk.**

---

## 🎯 Future Plans (v3.6+)

- 🎮 Mini-mode overlay for in-game use
- 📈 AI-powered pattern optimization
- 🔄 Batch export of all sessions
- 📊 Advanced statistical analysis
- 🌐 Multi-language support

---

## 💡 Tips for Best Results

1. **Use Enhanced Mode** for butterfly simulation
2. **Record training data** for comparison
3. **Monitor variance** - aim for 1,500-2,500
4. **Export CSV** for detailed analysis
5. **Review session history** to track improvements

---

## 📧 Support

For issues or feature requests, review the code comments or analyze export data for insights.

**Version**: 3.5.1 FINAL  
**Release Date**: December 18, 2025  
**Status**: Production Ready ✅

---

**Happy clicking! ⚔️**
