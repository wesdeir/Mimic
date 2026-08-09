#pragma once

#include <cstdint>
#include <filesystem>
#include <optional>
#include <string>
#include <vector>

#include "../engine/EngineStats.h"
#include "TrainingStats.h"

// Ported from mimic/session.py::SessionManager. Manages session history
// persistence (sessions.json: {"training": [...], "clicker": [...]}).
// UI-agnostic like the Python original -- no popups here, unlike
// HumanClickTracker's original tkinter leak (fixed in this port instead).

namespace mimic::core::session {

struct TrainingSessionRecord {
    std::string timestamp;  // ISO 8601
    std::string type;
    std::int64_t totalClicks = 0;
    double avgCps = 0.0;
    double variance = 0.0;
    double stdDev = 0.0;
    std::string filepath;
};

struct ClickerSessionRecord {
    std::string timestamp;
    std::string mode;  // "enhanced" | "standard"
    std::int64_t totalClicks = 0;
    double avgCps = 0.0;
    double variance = 0.0;
    double stdDev = 0.0;
    std::string risk;  // "LOW" | "MEDIUM" | "HIGH"
    int score = 0;
    std::string filepath;
};

class SessionManager {
public:
    // sessionsFilePath defaults to Config::sessionsFilePath() (the real
    // %USERPROFILE%\Desktop\Mimic\mimic_data\sessions.json); overridable so
    // tests don't have to write into the user's actual Desktop.
    explicit SessionManager(std::optional<std::string> sessionsFilePath = std::nullopt);

    TrainingSessionRecord addTrainingSession(const TrainingStats& stats, const std::string& filepath);
    // Computes the risk assessment internally via RiskAssessor::assess(stats),
    // matching session.py::add_clicker_session (the caller doesn't pass one in).
    ClickerSessionRecord addClickerSession(const mimic::core::engine::EngineStats& stats,
                                            const std::string& filepath);

    std::vector<TrainingSessionRecord> trainingSessions(std::optional<std::string> type = std::nullopt) const;
    std::vector<ClickerSessionRecord> clickerSessions(std::optional<std::string> mode = std::nullopt) const;

private:
    void load();
    bool save();

    std::filesystem::path sessionsFilePath_;
    std::vector<TrainingSessionRecord> training_;
    std::vector<ClickerSessionRecord> clicker_;
};

} // namespace mimic::core::session
