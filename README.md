# Undetectable Auto Clicker

> **Closet Cheat** | **7-12 CPS Range**

A sophisticated auto-clicker designed specifically for Minecraft PvP that mimics human clicking patterns to remain undetectable by anti-cheat systems. Built with advanced statistical algorithms and real-time monitoring.

---

## Features

### Core Functionality
- **Smart CPS Control**: Dynamically maintains 7-12 CPS with natural variation
- **Human-Like Patterns**: Combines Gaussian and Weibull distributions for realistic timing
- **Anti-Detection System**: Multiple layers of randomness to evade pattern detection
- **Real-Time Monitoring**: Live statistics dashboard with variance tracking
- **Session Analytics**: Comprehensive post-session reports with performance analysis

### Advanced Anti-Detection
- **Pattern Breaking**: Automatically detects and disrupts robotic patterns
- **Variance Monitoring**: Maintains variance above bot-detection thresholds
- **Temporal Drift**: Simulates natural speed variations over time
- **Momentum Simulation**: Realistic acceleration during click combos
- **Rhythmic Variation**: Natural human rhythm patterns

### System Requirements
- Windows 10/11
- Python 3.7 or higher (this version uses Python 3.14.x
- Administrator privileges

### Python Dependencies

pip install keyboard
pip install pywin32

## Installation

1. **Clone or download** this repository
2. **Install dependencies**:

pip install keyboard pywin32

text
3. **Run as Administrator**:
- Right-click Command Prompt
- Select "Run as administrator"
- Navigate to the script directory
- Execute: `python minecraft_clicker.py`

---

## How to Use

### Controls reference
1. **Launch the program** (must run as Administrator)
2. **Press F4** to activate the clicker
3. **Hold MB5** (side mouse button) to start clicking
4. **Release MB5** to stop clicking
5. **Press F4** again to deactivate and end session
6. **Press F5** to export detailed statistics

### GUI Indicators
- **● INACTIVE** (Red): Clicker is off
- **● ACTIVE** (Green): Clicker is ready
- **⚔️ CLICKING** (Green): Currently auto-clicking
- **Waiting for MB5...**: Ready and waiting for button press

---

## Understanding Statistics

### Live Statistics (GUI)
- **Total Clicks**: Number of clicks in current session
- **Current CPS**: Real-time clicks per second
- **Variance**: Statistical variance (higher = more human-like)
- **Session Avg**: Average CPS across entire session

### Exported Statistics (F5)
Detailed report includes:
- **Session Overview**: Duration, active time, idle time, uptime %
- **CPS Statistics**: Min, max, average, median CPS
- **Delay Statistics**: Timing analysis with percentiles
- **Anti-Detection Metrics**: Variance, pattern breaks, adjustments
- **Performance Analysis**: Color-coded GREEN/YELLOW/RED zones
- **Recommendations**: Specific advice based on your performance

---

## Safe Usage Guidelines

### Critical Thresholds
- **Maximum CPS**: Never exceed 12.0 (anti-cheat hard limit)
- **Minimum Variance**: Stay above 120 (below this = bot-like)

### Optimal Ranges (GREEN ZONE)
- **Average CPS**: 8.5 - 10.5
- **Variance**: 250+
- **Max CPS**: ≤ 11.9

### What to Watch For
⚠️ **High Risk Indicators**:
- Variance below 120
- Maximum CPS above 12.0
- Zero pattern breaks with low variance

**Good Session Indicators**:
- Variance above 250
- Average CPS between 8.5-10.5
- Natural variation in click patterns

---

## Technical Details

### Randomness Algorithm
The clicker uses a multi-layered approach:
1. **Base Distribution**: 70% Gaussian, 30% Weibull
2. **User Baseline**: Personal speed multiplier (0.88-1.12x)
3. **Momentum Effect**: Acceleration during combos
4. **Temporal Drift**: Gradual speed changes
5. **Rhythmic Variation**: Sine wave modulation
6. **Variance Adjustment**: ML evasion layer
7. **Random Noise**: Final randomization
8. **Pattern Breaking**: Chaos injection when patterns detected

### Safety Features
- **CPS Limiter**: Hard enforcement of 12 CPS maximum
- **Variance Monitor**: Auto-adjusts if variance drops too low
- **Pattern Detection**: Identifies and breaks robotic patterns
- **Session Tracking**: Accurate time tracking with edge case handling

---

## Troubleshooting

### "Need Administrator Privileges" Error
**Solution**: Run Command Prompt as Administrator before launching

### Clicks Not Registering
**Solution**: 
- Ensure clicker is ACTIVE (green indicator)
- Verify you're holding MB5 (not clicking it)
- Check that your mouse has an MB5 button

### Stats Export Failed
**Solution**: 
- Check console for actual stats (even if file save fails)
- Ensure write permissions in current directory
- Try running from a different folder

### High Detection Risk Warning
**Solution**:
- Run longer sessions (variance needs time to build)
- Don't click too consistently
- Let the algorithm work naturally

---

## Disclaimer

This tool is for **educational purposes** and authorized use only. Using auto-clickers on servers that prohibit them may result in bans. Always:
- Check server rules before use
- Use responsibly in approved environments
- Understand the risks involved
- Respect community guidelines

The developers assume no responsibility for misuse or consequences of using this software.

---

## Contributing

Found a bug? Have a feature suggestion? Please open an issue with:
- Detailed description of the problem/feature
- Steps to reproduce (for bugs)
- Your system specifications
- Any error messages or logs

---

## License

This project is provided as-is for educational purposes. Use at your own risk.

---

## Learning Resources

### Understanding the Algorithm
- **Gaussian Distribution**: Models normal human reaction times
- **Weibull Distribution**: Models "time to failure" - good for click fatigue
- **Variance**: Statistical measure of spread in data
- **Pattern Detection**: ML technique to identify repetitive behavior

### Anti-Cheat Systems
Modern anti-cheat uses:
- Statistical analysis of click patterns
- ML models trained on human vs. bot behavior
- Variance thresholds to detect automation
- Temporal analysis of consistency

This clicker combats these by maintaining high variance and natural patterns.

---

## Support

Need help? 
1. Check the troubleshooting section above
2. Review your exported stats (F5) for performance insights
3. Ensure you're following safe usage guidelines
4. Verify all dependencies are properly installed

---

**Made for competitive Minecraft PvP** | **Stay safe, click smart** 🎮⚔️

*Last Updated: December 18, 2025*
