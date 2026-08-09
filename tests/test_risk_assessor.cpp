// Spot-checks RiskAssessor::assess()'s point ladder against hand-computed
// expected scores, ported mechanically from config.py's assess(). Pure
// function of an EngineStats struct, no RNG involved.

#include <catch2/catch_test_macros.hpp>

#include "config/RiskAssessor.h"

using namespace mimic::core::config;
using mimic::core::engine::EngineStats;

namespace {
EngineStats makeStats(double variance, double maxCps, double avgCps, double stdDev,
                       int patternBreaks, std::int64_t total, bool enhanced) {
    EngineStats s;
    s.variance = variance;
    s.maxCps = maxCps;
    s.avgCps = avgCps;
    s.stdDev = stdDev;
    s.patternBreaks = patternBreaks;
    s.total = total;
    s.enhancedMode = enhanced;
    return s;
}
}  // namespace

TEST_CASE("RiskAssessor scores a strong enhanced-mode session as LOW risk", "[risk]") {
    // enhanced thresholds: target_variance 2200, spike_cps 15, cps range
    // 7-13, target_std_dev 45; pattern_ratio = 45/(1000/20)=0.9.
    auto stats = makeStats(/*variance=*/2500, /*maxCps=*/16, /*avgCps=*/9, /*stdDev=*/50,
                           /*patternBreaks=*/45, /*total=*/1000, /*enhanced=*/true);
    auto result = RiskAssessor::assess(stats);

    // 40 (variance) + 25 (spike) + 15 (avg cps) + 20 (std dev) + 10 (pattern) = 110
    CHECK(result.score == 110);
    CHECK(result.risk == RiskLevel::Low);
    CHECK(result.issues.empty());
}

TEST_CASE("RiskAssessor scores a weak enhanced-mode session as HIGH risk", "[risk]") {
    auto stats = makeStats(/*variance=*/500, /*maxCps=*/5, /*avgCps=*/3, /*stdDev=*/10,
                           /*patternBreaks=*/0, /*total=*/1000, /*enhanced=*/true);
    auto result = RiskAssessor::assess(stats);

    // 10 (variance) + 5 (spike) + 5 (avg cps) + 5 (std dev) + 0 (pattern) = 25
    CHECK(result.score == 25);
    CHECK(result.risk == RiskLevel::High);
    CHECK_FALSE(result.issues.empty());
}

TEST_CASE("RiskAssessor scores a mid-tier standard-mode session as MEDIUM risk", "[risk]") {
    // standard thresholds: ideal_variance 600, target 900, max_cps 11,
    // spike_cps 13, cps range 5-8, min_std_dev 25, target_std_dev 30.
    auto stats = makeStats(/*variance=*/700, /*maxCps=*/12, /*avgCps=*/6, /*stdDev=*/27,
                           /*patternBreaks=*/10, /*total=*/500, /*enhanced=*/false);
    auto result = RiskAssessor::assess(stats);

    // 25 (variance, between ideal/target) + 15 (spike, between max/spike) +
    // 15 (avg cps in range) + 12 (std dev, between min/target) + 5 (pattern
    // ratio 10/25=0.4, between 0 and 0.5 threshold... actually 0.4 < 0.5 so
    // +0) = 25+15+15+12+0 = 67
    CHECK(result.score == 67);
    CHECK(result.risk == RiskLevel::Medium);
}

TEST_CASE("RiskVisualization tiers are ordered and cover the full 0-100 range", "[risk]") {
    CHECK(std::string(RiskVisualization::levelFor(100).label) == "EXCELLENT");
    CHECK(std::string(RiskVisualization::levelFor(0).label) == "CRITICAL");
    CHECK(std::string(RiskVisualization::levelFor(57).label) == "ACCEPTABLE");
}
