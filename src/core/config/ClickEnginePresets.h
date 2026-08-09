#pragma once

#include <string>
#include <vector>
#include <utility>

// Ported from mimic/config.py::ClickEnginePresets. Predefined configurations
// for different clicking styles, anchored to the operator's own 60s
// recordings (one pair per technique): butterfly measured 137.2ms +/- 70.4,
// normal 187.0ms +/- 50.2; jitter is interpolated between them.
//
// mean/std are absolute milliseconds; AdaptiveClickerEngine::setPreset()
// moment-matches them onto its log-normal draw.

namespace mimic::core::config {

struct PresetConfig {
    std::string description;
    double butterflyMean = 0, butterflyStd = 0;
    double jitterMean = 0, jitterStd = 0;
    double normalMean = 0, normalStd = 0;
    double burstMean = 0, burstStd = 0, burstMaxClamp = 0;
    double varianceTarget = 0;
    std::string riskLevel;
};

class ClickEnginePresets {
public:
    // Preserves the Python dict's declaration order (Conservative, Balanced,
    // Aggressive) since the Settings screen displays them in this order.
    static const std::vector<std::pair<std::string, PresetConfig>>& builtins() {
        static const std::vector<std::pair<std::string, PresetConfig>> kPresets = {
            {"Conservative", PresetConfig{
                "Slower than your baseline - safest, lowest variance flags",
                151, 77, 176, 64, 206, 55, 92, 26, 70, 2400, "Low"}},
            {"Balanced", PresetConfig{
                "(Recommended) - matches your measured human baseline",
                137, 70, 160, 58, 187, 50, 82, 24, 60, 2800, "Medium"}},
            {"Aggressive", PresetConfig{
                "Faster than your baseline - stays under the CPS cap",
                121, 62, 141, 51, 165, 44, 70, 20, 52, 3000, "High"}},
        };
        return kPresets;
    }

    static const PresetConfig* find(const std::string& name) {
        for (const auto& [presetName, cfg] : builtins()) {
            if (presetName == name) return &cfg;
        }
        return nullptr;
    }
};

} // namespace mimic::core::config
