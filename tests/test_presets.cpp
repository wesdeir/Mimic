// Pure closed-form checks (no RNG): StateParams::fromMoments's algebra is
// derived so that a log-normal(median, sigma) constructed from (mean, std)
// reproduces that exact mean/std analytically. This test verifies the
// closed-form identity directly -- if it fails, the derivation itself (not
// just an RNG sample) is wrong.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include <cmath>

#include <nlohmann/json.hpp>

#include "engine/StateParams.h"
#include "config/ClickEnginePresets.h"

using namespace mimic::core::engine;
using namespace mimic::core::config;
using Catch::Matchers::WithinRel;

namespace {
// Analytic mean/std of a log-normal(median, sigma) as engine.py's comments
// derive them: mean = median * exp(sigma^2/2), std = mean * sqrt(exp(sigma^2)-1).
double logNormalMean(double median, double sigma) { return median * std::exp(0.5 * sigma * sigma); }
double logNormalStd(double median, double sigma) {
    return logNormalMean(median, sigma) * std::sqrt(std::exp(sigma * sigma) - 1.0);
}
}  // namespace

TEST_CASE("StateParams::fromMoments reproduces the requested mean/std exactly", "[presets][math]") {
    for (double mean : {80.0, 137.0, 187.0, 300.0}) {
        for (double std : {20.0, 50.0, 70.0}) {
            StateParams p = StateParams::fromMoments(ClickState::Normal, mean, std, 0.1, 78.6, 0.359, 0.68, 0.0);
            const double actualMean = logNormalMean(p.baseRate, p.sigma);
            const double actualStd = logNormalStd(p.baseRate, p.sigma);

            INFO("mean=" << mean << " std=" << std << " -> median=" << p.baseRate << " sigma=" << p.sigma);
            CHECK_THAT(actualMean, WithinRel(mean, 1e-9));
            CHECK_THAT(actualStd, WithinRel(std, 1e-9));
        }
    }
}

TEST_CASE("Built-in presets moment-match without throwing and stay ordered Conservative<Balanced<Aggressive",
          "[presets]") {
    const auto& presets = ClickEnginePresets::builtins();
    REQUIRE(presets.size() == 3);

    const PresetConfig* conservative = ClickEnginePresets::find("Conservative");
    const PresetConfig* balanced = ClickEnginePresets::find("Balanced");
    const PresetConfig* aggressive = ClickEnginePresets::find("Aggressive");
    REQUIRE(conservative);
    REQUIRE(balanced);
    REQUIRE(aggressive);

    // Conservative is slower (higher mean delay) than Balanced, which is
    // slower than Aggressive -- this ordering is the whole point of the
    // three presets, so a regression that flips it is a real bug.
    CHECK(conservative->normalMean > balanced->normalMean);
    CHECK(balanced->normalMean > aggressive->normalMean);
    CHECK(conservative->butterflyMean > balanced->butterflyMean);
    CHECK(balanced->butterflyMean > aggressive->butterflyMean);

    for (const auto& [name, cfg] : presets) {
        INFO("preset: " << name);
        CHECK_NOTHROW(StateParams::fromMoments(ClickState::Butterfly, cfg.butterflyMean, cfg.butterflyStd,
                                                0.02, 33.6, 0.645, 0.43, 0.207));
        CHECK_NOTHROW(StateParams::fromMoments(ClickState::Jitter, cfg.jitterMean, cfg.jitterStd,
                                                0.06, 52.0, 0.500, 0.55, 0.090));
        CHECK_NOTHROW(StateParams::fromMoments(ClickState::Normal, cfg.normalMean, cfg.normalStd,
                                                0.10, 78.6, 0.359, 0.68, 0.000));
    }
}

TEST_CASE("PresetConfig round-trips through JSON, matching Python's dict.get(...) defaulting", "[presets][json]") {
    const PresetConfig* balanced = ClickEnginePresets::find("Balanced");
    REQUIRE(balanced);

    nlohmann::json j = *balanced;
    PresetConfig roundTripped = j.get<PresetConfig>();
    CHECK(roundTripped.normalMean == balanced->normalMean);
    CHECK(roundTripped.description == balanced->description);

    // A hand-edited file missing fields should default rather than throw
    // (mirrors Python's PresetManager loading a partial custom preset).
    nlohmann::json partial = {{"normal_mean", 200.0}};
    PresetConfig fromPartial = partial.get<PresetConfig>();
    CHECK(fromPartial.normalMean == 200.0);
    CHECK(fromPartial.butterflyMean == 0.0);
}

TEST_CASE("StateParams rejects invalid phi/sigma", "[presets][math]") {
    CHECK_THROWS_AS(StateParams(ClickState::Normal, 100.0, 0.3, 1.0), std::invalid_argument);
    CHECK_THROWS_AS(StateParams(ClickState::Normal, 100.0, 0.3, -1.0), std::invalid_argument);
    CHECK_THROWS_AS(StateParams(ClickState::Normal, 100.0, -0.1, 0.1), std::invalid_argument);
}
