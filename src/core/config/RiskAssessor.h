#pragma once

#include <string>
#include <vector>

#include "../engine/EngineStats.h"

// Ported from mimic/config.py::RiskAssessor. Comprehensive risk assessment
// with realistic thresholds -- the scoring ladder (variance/CPS-spike/avg-CPS
// /std-dev/pattern-break point buckets summing to 100) is ported mechanically
// from the Python `assess()` method.

namespace mimic::core::config {

enum class RiskMode { Enhanced, Standard };

struct RiskThresholds {
    double idealVariance;
    double targetVariance;
    double maxVariance;
    double minCps;
    double targetCps;
    double maxCps;
    double spikeCps;
    double minStdDev;
    double targetStdDev;
};

inline const RiskThresholds& thresholdsFor(RiskMode mode) {
    static const RiskThresholds enhanced{1500, 2200, 3500, 7, 10, 13, 15, 35, 45};
    static const RiskThresholds standard{600, 900, 1500, 5, 8, 11, 13, 25, 30};
    return mode == RiskMode::Enhanced ? enhanced : standard;
}

enum class RiskLevel { Low, Medium, High };

struct RiskAssessment {
    RiskLevel risk;
    int score = 0;
    std::string colorHex;
    std::string status;
    std::vector<std::string> issues;
    std::vector<std::string> recommendations;
};

class RiskAssessor {
public:
    static RiskAssessment assess(const mimic::core::engine::EngineStats& stats);
};

} // namespace mimic::core::config
