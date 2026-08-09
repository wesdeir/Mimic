#pragma once

#include <cstdint>

#include "StateParams.h"

// Snapshot returned by AdaptiveClickerEngine::getDetailedStats(), mirroring
// engine.py::get_detailed_stats()'s dict. A plain, copyable struct so it can
// be handed across threads by value (see app::StatsSnapshot).

namespace mimic::core::engine {

struct EngineStats {
    bool valid = false;  // false when n < 2, matching Python's `if self._n < 2: return {}`

    std::int64_t total = 0;
    double mean = 0.0;
    double variance = 0.0;
    double stdDev = 0.0;
    double minDelay = 0.0;
    double maxDelay = 0.0;
    double avgCps = 0.0;
    double currentCps = 0.0;
    double maxCps = 0.0;   // == peakCps
    double measuredCps = 0.0;
    double sessionSeconds = 0.0;
    ClickState state = ClickState::Normal;
    int patternBreaks = 0;
    int burstCount = 0;
    int doubleCount = 0;
    double effectiveCps = 0.0;
    int pauseCount = 0;
    int outlierCount = 0;
    bool enhancedMode = true;
};

} // namespace mimic::core::engine
