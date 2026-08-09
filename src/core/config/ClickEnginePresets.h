#pragma once

#include <string>
#include <vector>
#include <utility>

#include <nlohmann/json.hpp>

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

inline void to_json(nlohmann::json& j, const PresetConfig& p) {
    j = nlohmann::json{
        {"description", p.description},
        {"butterfly_mean", p.butterflyMean}, {"butterfly_std", p.butterflyStd},
        {"jitter_mean", p.jitterMean}, {"jitter_std", p.jitterStd},
        {"normal_mean", p.normalMean}, {"normal_std", p.normalStd},
        {"burst_mean", p.burstMean}, {"burst_std", p.burstStd}, {"burst_max_clamp", p.burstMaxClamp},
        {"variance_target", p.varianceTarget}, {"risk_level", p.riskLevel},
    };
}

// Uses j.value(key, default) rather than a strict macro so a hand-edited or
// older custom_presets.json missing a field degrades gracefully, matching
// Python's dict.get(key, default) semantics in set_preset()/apply_preset().
inline void from_json(const nlohmann::json& j, PresetConfig& p) {
    p.description = j.value("description", std::string());
    p.butterflyMean = j.value("butterfly_mean", 0.0);
    p.butterflyStd = j.value("butterfly_std", 0.0);
    p.jitterMean = j.value("jitter_mean", 0.0);
    p.jitterStd = j.value("jitter_std", 0.0);
    p.normalMean = j.value("normal_mean", 0.0);
    p.normalStd = j.value("normal_std", 0.0);
    p.burstMean = j.value("burst_mean", 0.0);
    p.burstStd = j.value("burst_std", 0.0);
    p.burstMaxClamp = j.value("burst_max_clamp", 0.0);
    p.varianceTarget = j.value("variance_target", 0.0);
    p.riskLevel = j.value("risk_level", std::string());
}

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
