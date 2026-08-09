"""Mimic - adaptive human-like clicking engine.

Part of Mimic. Split out of the original single-file Mimic.py.
"""

__version__ = "4.0.0"

from .config import Config, RiskAssessor, RiskVisualization, ClickEnginePresets, PresetManager
from .engine import AdaptiveClickerEngine, StateParams, STATES, STATE_NAMES, TRANSITION_MATRIX
from .session import SessionManager, HumanClickTracker
from .widgets import CPSLineGraph, HistogramCanvas

__all__ = [
    "Config", "RiskAssessor", "RiskVisualization", "ClickEnginePresets",
    "PresetManager", "AdaptiveClickerEngine", "StateParams", "STATES",
    "STATE_NAMES", "TRANSITION_MATRIX", "SessionManager", "HumanClickTracker",
    "CPSLineGraph", "HistogramCanvas",
]
