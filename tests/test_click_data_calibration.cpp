// Sanity-checks that click_data/ (the calibration ground truth every
// constant in Config.h/StateParams.h cites) is still readable and still
// looks like human clicking data -- a coarse guard against the reference
// data silently rotting or being misparsed, not a tight regression test
// (real recordings are noisy by nature).

#include <catch2/catch_test_macros.hpp>

#include "golden_helpers.h"

using mimic::test::computeMoments;
using mimic::test::loadDelayColumn;

TEST_CASE("click_data/ recordings parse and fall in a plausible human range", "[calibration]") {
    const std::string path = std::string(MIMIC_CLICK_DATA_DIR) + "/ClickData_20260807_193042.csv";
    auto delays = loadDelayColumn(path, "delay_ms");

    REQUIRE(delays.size() > 50);
    // First row is always 0.0 (relative_time_ms/delay_ms of the first click)
    // per engine.py/session.py's export format; drop it before computing
    // interval statistics.
    delays.erase(delays.begin());

    auto m = computeMoments(delays);
    INFO("mean=" << m.mean << " std=" << m.stdDev << " min=" << m.min << " max=" << m.max);

    // Config.h's ABSOLUTE_MIN/MAX_DELAY_MS (30/450ms) were fitted to these
    // recordings with a small margin -- real data should sit inside that
    // envelope, and Config's target mean (111ms enhanced) should be in the
    // same ballpark as at least one real recorded session.
    CHECK(m.min >= 0.0);
    CHECK(m.max < 2000.0);  // session.py's own capture filter is 1-2000ms
    CHECK(m.mean > 20.0);
    CHECK(m.mean < 500.0);
}
