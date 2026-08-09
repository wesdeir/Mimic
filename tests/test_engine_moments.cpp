// Phase 1 parity gate (port plan §2.3): validates the C++ engine against
// TWO independent references rather than chasing bit-exact replay, which is
// unreachable across RNG implementations regardless of generator choice:
//   (a) a frozen golden run of the ORIGINAL, unmodified Python engine
//       (tools/python_reference/golden/*.csv) -- catches "the port subtly
//       changed a formula" even though no single value matches.
//   (b) closed-form math that needs no RNG at all (moment-matching algebra,
//       transition-matrix row sums, Welford vs a naive reference).

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include <cmath>

#include "golden_helpers.h"

#include "engine/AdaptiveClickerEngine.h"
#include "engine/StateParams.h"
#include "config/ClickEnginePresets.h"

using namespace mimic::core::engine;
using namespace mimic::core::config;
using mimic::test::computeMoments;
using mimic::test::loadDelayColumn;
using mimic::test::relativeDiff;

namespace {
constexpr int kStreamLen = 50000;
// Mean sampling error at n=50000 is small for these distributions; 8%/12%
// leaves headroom for genuine cross-RNG sampling noise (esp. std dev, which
// is more sensitive to the fat right tail from pauses/outliers) while still
// catching a real formula regression, which tends to shift results by much
// more than this.
constexpr double kMeanTolerance = 0.08;
constexpr double kStdDevTolerance = 0.12;
}  // namespace

TEST_CASE("Engine output moments match the Python golden reference", "[engine][parity]") {
    const std::string goldenDir = MIMIC_GOLDEN_DIR;

    for (const std::string& preset : {"Conservative", "Balanced", "Aggressive"}) {
        for (bool enhanced : {true, false}) {
            std::string modeTag = enhanced ? "enhanced" : "standard";
            std::string presetLower = preset;
            for (auto& c : presetLower) c = static_cast<char>(std::tolower(c));
            std::string goldenPath = goldenDir + "/" + presetLower + "_" + modeTag + ".csv";

            auto goldenValues = loadDelayColumn(goldenPath, "delay_ms");
            INFO("golden file: " << goldenPath);
            REQUIRE(goldenValues.size() > 1000);
            auto goldenMoments = computeMoments(goldenValues);

            AdaptiveClickerEngine engine(enhanced, preset, /*rngSeed=*/12345);
            auto cppStream = engine.simulateStream(kStreamLen);
            auto cppMoments = computeMoments(cppStream);

            INFO("preset=" << preset << " enhanced=" << enhanced
                            << " golden mean=" << goldenMoments.mean << " cpp mean=" << cppMoments.mean
                            << " golden std=" << goldenMoments.stdDev << " cpp std=" << cppMoments.stdDev);
            CHECK(relativeDiff(cppMoments.mean, goldenMoments.mean) < kMeanTolerance);
            CHECK(relativeDiff(cppMoments.stdDev, goldenMoments.stdDev) < kStdDevTolerance);
        }
    }
}

TEST_CASE("calculateDelay output stays within configured delay bounds", "[engine]") {
    // Checked against calculateDelay() directly, not simulateStream(): once
    // double-click emulation splits a delay into [gap, d-gap] sub-events,
    // those pieces represent hardware switch-chatter timing, not a full
    // click interval, so they are NOT bound by ENHANCED_MIN/MAX_DELAY_MS
    // (e.g. the ~34.4ms+/-1.6 gap can occasionally dip under 30ms) -- that
    // is expected, matching the Python original's simulate_stream() docstring.
    AdaptiveClickerEngine engine(true, "Balanced", 777);
    for (int i = 0; i < 20000; ++i) {
        double d = engine.calculateDelay();
        CHECK(d >= 30.0);
        CHECK(d <= 450.0);
    }
}

TEST_CASE("TRANSITION_MATRIX rows are stochastic (sum to 1)", "[engine][math]") {
    for (const auto& row : transitionMatrix()) {
        double sum = row[0] + row[1] + row[2];
        CHECK_THAT(sum, Catch::Matchers::WithinAbs(1.0, 1e-9));
    }
}

TEST_CASE("Markov chain long-run occupancy matches the analytic stationary distribution", "[engine][math]") {
    // Solve for the stationary distribution pi (pi * P = pi, sum(pi) = 1) via
    // power iteration -- simple and adequate for a well-conditioned 3-state
    // chain with strong diagonal dominance like this one.
    std::array<double, 3> pi = {1.0 / 3, 1.0 / 3, 1.0 / 3};
    const auto& P = transitionMatrix();
    for (int iter = 0; iter < 100000; ++iter) {
        std::array<double, 3> next = {0, 0, 0};
        for (int i = 0; i < 3; ++i)
            for (int j = 0; j < 3; ++j) next[j] += pi[i] * P[i][j];
        pi = next;
    }

    double sum = pi[0] + pi[1] + pi[2];
    CHECK_THAT(sum, Catch::Matchers::WithinAbs(1.0, 1e-6));

    // Empirical: drive advanceState() (via calculateDelay(), its only public
    // path) many times and tally occupancy, independent of the delay-value
    // math entirely -- this exercises the actual CDF-search code, not just
    // the matrix in isolation.
    AdaptiveClickerEngine engine(true, "Balanced", 999);
    constexpr int kSteps = 300000;
    std::array<long long, 3> occupancy = {0, 0, 0};
    for (int i = 0; i < kSteps; ++i) {
        engine.calculateDelay();
        ++occupancy[stateIndex(engine.currentState())];
    }

    for (int i = 0; i < 3; ++i) {
        double empirical = static_cast<double>(occupancy[i]) / kSteps;
        INFO("state " << i << " empirical=" << empirical << " analytic=" << pi[i]);
        CHECK(std::abs(empirical - pi[i]) < 0.03);
    }
}
