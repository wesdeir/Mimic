#pragma once

#include <cstdint>
#include <string>

// Produced by HumanClickTracker::getStats(), mirroring session.py's
// HumanClickTracker.get_stats() dict. Distinct from engine::EngineStats,
// which describes the CLICKING engine's own output, not a recorded human
// baseline session.

namespace mimic::core::session {

struct TrainingStats {
    bool valid = false;  // false when fewer than 10 valid delays, matching Python's `if len < 10: return None`

    std::int64_t total = 0;
    std::int64_t validDelays = 0;
    double captureRate = 0.0;
    double avgCps = 0.0;
    double minCps = 0.0;
    double maxCps = 0.0;
    double medianCps = 0.0;
    double peakCps = 0.0;
    double variance = 0.0;
    double stdDev = 0.0;
    double sessionDurationSeconds = 0.0;
    double p10DelayMs = 0.0;
    double p50DelayMs = 0.0;
    double p90DelayMs = 0.0;
    double minDelayMs = 0.0;
    double maxDelayMs = 0.0;
    double avgDelayMs = 0.0;
    std::string trainingType = "normal";  // "butterfly" | "jitter" | "normal" | other
};

} // namespace mimic::core::session
