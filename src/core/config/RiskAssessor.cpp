#include "RiskAssessor.h"

#include <cmath>

namespace mimic::core::config {

using mimic::core::engine::EngineStats;

RiskAssessment RiskAssessor::assess(const EngineStats& stats) {
    const RiskMode mode = stats.enhancedMode ? RiskMode::Enhanced : RiskMode::Standard;
    const RiskThresholds& t = thresholdsFor(mode);

    const double variance = stats.variance;
    const double maxCps = stats.maxCps;
    const double avgCps = stats.avgCps;
    const double stdDev = stats.stdDev;
    const int patternBreaks = stats.patternBreaks;
    const std::int64_t totalClicks = stats.total > 0 ? stats.total : 1;

    int score = 0;
    std::vector<std::string> issues;
    std::vector<std::string> recommendations;

    // === VARIANCE CHECK (40 points) ===
    if (variance >= t.targetVariance) {
        score += 40;
    } else if (variance >= t.idealVariance) {
        score += 25;
        int gap = static_cast<int>((t.targetVariance / variance - 1.0) * 100);
        recommendations.push_back("Increase variance by +" + std::to_string(gap) +
                                   "% to reach " + std::to_string(static_cast<int>(t.targetVariance)));
    } else {
        score += 10;
        issues.push_back("Variance critically low (" + std::to_string(static_cast<int>(variance)) +
                          " vs " + std::to_string(static_cast<int>(t.idealVariance)) + " minimum)");
        int gap = variance > 0 ? static_cast<int>((t.targetVariance / variance - 1.0) * 100) : 0;
        recommendations.push_back("CRITICAL: Increase variance by +" + std::to_string(gap) + "%");
    }

    // === CPS SPIKE CHECK (25 points) ===
    if (maxCps >= t.spikeCps) {
        score += 25;
    } else if (maxCps >= t.maxCps) {
        score += 15;
        recommendations.push_back("Allow higher CPS spikes (target: " +
                                   std::to_string(static_cast<int>(t.spikeCps)) + "+)");
    } else {
        score += 5;
        char buf[64];
        std::snprintf(buf, sizeof(buf), "No CPS spikes detected (max: %.1f)", maxCps);
        issues.push_back(buf);
        recommendations.push_back("Enable CPS spikes up to " + std::to_string(static_cast<int>(t.spikeCps)) + "-16");
    }

    // === AVERAGE CPS (15 points) ===
    if (avgCps >= t.minCps && avgCps <= t.maxCps) {
        score += 15;
    } else {
        score += 5;
        char buf[64];
        if (avgCps > t.maxCps) {
            std::snprintf(buf, sizeof(buf), "Average CPS too high (%.1f)", avgCps);
        } else {
            std::snprintf(buf, sizeof(buf), "Average CPS too low (%.1f)", avgCps);
        }
        issues.push_back(buf);
    }

    // === STANDARD DEVIATION (20 points) ===
    if (stdDev >= t.targetStdDev) {
        score += 20;
    } else if (stdDev >= t.minStdDev) {
        score += 12;
        recommendations.push_back("Increase std dev to " + std::to_string(static_cast<int>(t.targetStdDev)) + "ms");
    } else {
        score += 5;
        char buf[64];
        std::snprintf(buf, sizeof(buf), "Std dev too low (%.1fms)", stdDev);
        issues.push_back(buf);
        recommendations.push_back("Target std dev: " + std::to_string(static_cast<int>(t.targetStdDev)) + "ms");
    }

    // === PATTERN BREAKS (bonus 10 points) ===
    double patternRatio = totalClicks > 20 ? patternBreaks / (totalClicks / 20.0) : 0.0;
    if (patternRatio >= 0.8) {
        score += 10;
    } else if (patternRatio >= 0.5) {
        score += 5;
    }

    RiskAssessment result;
    result.score = score;
    result.issues = std::move(issues);
    result.recommendations = std::move(recommendations);

    if (score >= 80) {
        result.risk = RiskLevel::Low;
        result.colorHex = "#4CAF50";
        result.status = "SAFE - Anti-cheat compliant";
    } else if (score >= 50) {
        result.risk = RiskLevel::Medium;
        result.colorHex = "#FFA500";
        result.status = "ACCEPTABLE - Room for improvement";
    } else {
        result.risk = RiskLevel::High;
        result.colorHex = "#f44336";
        result.status = "DANGEROUS - Click Normally for 10 or more minutes";
    }
    return result;
}

const std::array<RiskVisualizationLevel, 6>& RiskVisualization::levels() {
    static const std::array<RiskVisualizationLevel, 6> kLevels = {{
        {85, "EXCELLENT", "#00e676", "Indistinguishable"},
        {70, "GOOD", "#4CAF50", "Safe Range"},
        {55, "ACCEPTABLE", "#FFC107", "Acceptable"},
        {40, "CAUTION", "#FF9800", "Needs Improvement"},
        {25, "RISKY", "#F44336", "High Detection Risk"},
        {0, "CRITICAL", "#b71c1c", "Extremely Dangerous"},
    }};
    return kLevels;
}

const RiskVisualizationLevel& RiskVisualization::levelFor(int score) {
    const auto& lv = levels();
    for (const auto& level : lv) {
        if (score >= level.minScore) {
            return level;
        }
    }
    return lv.back();
}

} // namespace mimic::core::config
