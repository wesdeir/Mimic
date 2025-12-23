# Mimic: Statistical Ghost Clicker & Benchmark Suite

Mimic is an advanced automation framework designed to simulate human clicking patterns with high statistical fidelity. Unlike traditional macro software that uses fixed delays or simple randomization, Mimic employs a statistical distribution engine (Gaussian and Weibull) to generate click timings that closely resemble human physiological performance.

This project includes two core components:
1. **Mimic v3.7**: The primary automation engine with real-time risk assessment and adaptive pattern switching.
2. **Mimic Benchmark Tool**: A standalone analytics utility for recording, analyzing, and benchmarking clicking performance (CPS, consistency, and fatigue).

## Features

### Mimic Engine (Mimic.py)
*   **Statistical Mimicry**: Utilizes Box-Muller transforms and Weibull distributions to generate non-deterministic click intervals.
*   **Adaptive Mixed Mode**: Dynamically switches between three distinct clicking techniques (Butterfly, Jitter, Normal) during operation to prevent pattern detection.
*   **Real-time Risk Assessment**: Continuously evaluates the generated click stream against common anti-cheat heuristics (Variance, Standard Deviation, Pattern Breaks) and assigns a safety score (0-100).
*   **Human Training Mode**: Records legitimate user input via low-level Windows hooks to build personalized baseline profiles.
*   **Preset System**: Includes pre-configured profiles (Conservative, Balanced, Aggressive) and supports custom user configurations.
*   **Visual Analytics**: Live CPS graphing and click delay distribution histograms.

### Benchmark Tool (MimicBenchmarkTool.py)
*   **Granular Analysis**: Detailed breakdown of click timings, including percentile analysis (P10, P50, P90).
*   **Fatigue Tracking**: Monitors CPS degradation over time to identify stamina limits.
*   **Burst Detection**: Identifies and analyzes high-frequency micro-bursts and double-click events.
*   **Data Export**: Automatically generates CSV datasets and detailed statistical text reports for every session.

## Prerequisites

*   Python 3.8 or higher
*   Windows OS (Required for `pywin32` hooks)

### Dependencies

Install the required Python packages:

```
pip install pynput pywin32 keyboard
```

*Note: Tkinter is required for the GUI and is typically included with standard Python installations.*

## Installation

1.  Clone the repository or download the source files.
2.  Ensure both `Mimic.py` and `MimicBenchmarkTool.py` are in the same directory.
3.  Run the scripts directly via Python.

## Usage

### Running the Auto-Clicker
Execute the main script:
```
python Mimic.py
```

**Controls:**
*   **F4**: Toggle Clicking On/Off
*   **F9**: Toggle Enhanced Adaptive Mode
*   **F7**: Start/Stop Training Mode (Recording)
*   **F8**: Export Training Data
*   **F5/F6**: Export Session Statistics (TXT/CSV)

**Dashboard Overview:**
The GUI provides real-time feedback on your risk level. Keep an eye on the **Risk Score**; a score below 50 indicates a clicking pattern that is mathematically unlikely to be human and may trigger detection systems.

### Running the Benchmark Tool
You can launch the benchmark tool directly from the Mimic GUI (Training Tab) or run it standalone:
```
python MimicBenchmarkTool.py
```
Select a test duration, click "Start Test", and click as fast as possible to generate a performance report.

## Configuration & Output

### Data Storage
All data is automatically organized in your user Desktop directory:
*   `Desktop/mimic_data/`: Stores session logs, training baselines, and configuration files.
*   `Desktop/click_data/`: Stores benchmark CSVs and analysis reports.

### Presets
Mimic ships with three default presets:
1.  **Conservative**: High variance, lower CPS caps. Designed for strict anti-cheat environments.
2.  **Balanced**: Moderate speed with standard deviation targets derived from average player data.
3.  **Aggressive**: Prioritizes speed over variance. Higher risk of detection but maximizes throughput.

Custom presets can be saved and will persist in `mimic_data/custom_presets.json`.

## Technical Architecture

### Event Injection
Mimic uses `win32api` and `win32con` for input injection rather than high-level wrappers. This allows for precise control over "press" and "release" timings, enabling the simulation of realistic pressure duration (mouse down/up intervals), which is a common vector for detection in simpler macro tools.

### Pattern Generation
The engine implements a **Drift and Rhythm** system. Instead of random noise, the click delay drifts over time (simulating focus loss/gain) and oscillates slightly (simulating natural biological rhythms), significantly increasing the complexity of the output data stream.

## Disclaimer

This software is for educational and research purposes only. Using automation tools in online games may violate Terms of Service and result in account bans. The authors accept no responsibility for damages resulting from the use of this tool.