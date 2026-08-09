// Phase 2: SessionManager JSON round-trip and HumanClickTracker's stats
// math, driven directly via recordClick() (bypassing the real WH_MOUSE_LL
// hook, which needs a live message pump and cannot be exercised in a
// headless unit test) against a real click_data/ recording.

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include <filesystem>
#include <fstream>

#include "golden_helpers.h"
#include "session/HumanClickTracker.h"
#include "session/SessionManager.h"

using namespace mimic::core::session;
namespace fs = std::filesystem;

TEST_CASE("HumanClickTracker computes stats matching a real click_data/ recording", "[session][tracker]") {
    // Feed the tracker the exact inter-click gaps from a real recording (via
    // recordClick()'s public timestamp-driven API) and confirm its stats
    // math reproduces the session's own numbers -- this is the same
    // arithmetic MimicBenchmarkTool.py/session.py used to characterize
    // click_data/ in the first place.
    const std::string path = std::string(MIMIC_CLICK_DATA_DIR) + "/ClickData_20260807_193042.csv";
    auto delays = mimic::test::loadDelayColumn(path, "delay_ms");
    REQUIRE(delays.size() > 100);
    delays.erase(delays.begin());  // first row's delay_ms is always 0.0 (no prior click)

    SessionManager dummyManager;  // unused by recordClick(); required to construct the tracker
    HumanClickTracker tracker(dummyManager);

    double t = 0.0;
    tracker.recordClick(t);
    for (double d : delays) {
        t += d / 1000.0;
        tracker.recordClick(t);
    }

    auto stats = tracker.getStats();
    REQUIRE(stats.valid);
    CHECK(stats.total == static_cast<std::int64_t>(delays.size() + 1));
    CHECK(stats.validDelays > 0);
    CHECK(stats.avgDelayMs > 0.0);
    CHECK(stats.variance > 0.0);

    // Cross-check against the direct-computed moments of the same delay
    // column (independent of the tracker's own bookkeeping).
    auto direct = mimic::test::computeMoments(delays);
    CHECK_THAT(stats.avgDelayMs, Catch::Matchers::WithinRel(direct.mean, 0.05));
}

TEST_CASE("SessionManager persists and reloads clicker + training sessions", "[session][io]") {
    // Explicit path override so this test doesn't write into the user's
    // real Desktop\Mimic\mimic_data\sessions.json.
    const std::string testSessionsPath = (fs::temp_directory_path() / "mimic_test_sessions.json").string();
    fs::remove(testSessionsPath);
    SessionManager manager(testSessionsPath);

    mimic::core::engine::EngineStats stats;
    stats.valid = true;
    stats.total = 500;
    stats.avgCps = 9.0;
    stats.variance = 2500.0;
    stats.stdDev = 50.0;
    stats.maxCps = 16.0;
    stats.patternBreaks = 20;
    stats.enhancedMode = true;

    auto record = manager.addClickerSession(stats, "C:/tmp/test_export.csv");
    CHECK(record.totalClicks == 500);
    CHECK(record.mode == "enhanced");
    CHECK((record.risk == "LOW" || record.risk == "MEDIUM" || record.risk == "HIGH"));

    auto sessions = manager.clickerSessions();
    CHECK_FALSE(sessions.empty());
    CHECK(sessions.back().filepath == "C:/tmp/test_export.csv");

    // Reloading a fresh SessionManager should see the just-saved session
    // (round-trips through sessions.json on disk).
    SessionManager reloaded(testSessionsPath);
    auto reloadedSessions = reloaded.clickerSessions();
    CHECK_FALSE(reloadedSessions.empty());

    fs::remove(testSessionsPath);
}
