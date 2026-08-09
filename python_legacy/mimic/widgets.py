"""Canvas widgets: live CPS line graph and delay histogram.

Part of Mimic. Split out of the original single-file Mimic.py.
"""

import math
import time
import tkinter as tk


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
