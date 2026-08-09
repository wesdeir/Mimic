#include "SessionManager.h"

#include <chrono>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <sstream>

#include <nlohmann/json.hpp>

#include "../config/Config.h"
#include "../config/RiskAssessor.h"

namespace mimic::core::session {

namespace fs = std::filesystem;
using nlohmann::json;

// NOT in an anonymous namespace: nlohmann's adl_serializer finds these via
// ADL rooted at TrainingSessionRecord/ClickerSessionRecord's actual
// enclosing namespace (mimic::core::session), and MSVC does not reliably
// look into an unnamed namespace nested inside it for that purpose.
void to_json(json& j, const TrainingSessionRecord& r) {
    j = json{{"timestamp", r.timestamp}, {"type", r.type},          {"total_clicks", r.totalClicks},
             {"avg_cps", r.avgCps},      {"variance", r.variance},  {"std_dev", r.stdDev},
             {"filepath", r.filepath}};
}

void from_json(const json& j, TrainingSessionRecord& r) {
    r.timestamp = j.value("timestamp", std::string());
    r.type = j.value("type", std::string("unknown"));
    r.totalClicks = j.value("total_clicks", std::int64_t{0});
    r.avgCps = j.value("avg_cps", 0.0);
    r.variance = j.value("variance", 0.0);
    r.stdDev = j.value("std_dev", 0.0);
    r.filepath = j.value("filepath", std::string());
}

void to_json(json& j, const ClickerSessionRecord& r) {
    j = json{{"timestamp", r.timestamp}, {"mode", r.mode},         {"total_clicks", r.totalClicks},
             {"avg_cps", r.avgCps},      {"variance", r.variance}, {"std_dev", r.stdDev},
             {"risk", r.risk},           {"score", r.score},       {"filepath", r.filepath}};
}

void from_json(const json& j, ClickerSessionRecord& r) {
    r.timestamp = j.value("timestamp", std::string());
    r.mode = j.value("mode", std::string("enhanced"));
    r.totalClicks = j.value("total_clicks", std::int64_t{0});
    r.avgCps = j.value("avg_cps", 0.0);
    r.variance = j.value("variance", 0.0);
    r.stdDev = j.value("std_dev", 0.0);
    r.risk = j.value("risk", std::string());
    r.score = j.value("score", 0);
    r.filepath = j.value("filepath", std::string());
}

namespace {

std::string isoNow() {
    const auto now = std::chrono::system_clock::now();
    const std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tmBuf;
    localtime_s(&tmBuf, &t);
    std::ostringstream ss;
    ss << std::put_time(&tmBuf, "%Y-%m-%dT%H:%M:%S");
    return ss.str();
}

} // namespace

SessionManager::SessionManager(std::optional<std::string> sessionsFilePath) {
    sessionsFilePath_ =
        sessionsFilePath ? fs::path(*sessionsFilePath) : fs::path(mimic::core::config::sessionsFilePath());
    load();
}

void SessionManager::load() {
    const fs::path path = sessionsFilePath_;
    if (!fs::exists(path)) return;

    try {
        std::ifstream in(path);
        json j;
        in >> j;
        if (j.contains("training")) {
            for (const auto& item : j["training"]) training_.push_back(item.get<TrainingSessionRecord>());
        }
        if (j.contains("clicker")) {
            for (const auto& item : j["clicker"]) clicker_.push_back(item.get<ClickerSessionRecord>());
        }
    } catch (const std::exception& e) {
        std::cerr << "[WARNING] Could not load sessions: " << e.what() << "\n";
        training_.clear();
        clicker_.clear();
    }
}

bool SessionManager::save() {
    try {
        const fs::path path = sessionsFilePath_;
        std::error_code ec;
        fs::create_directories(path.parent_path(), ec);

        json j;
        j["training"] = training_;
        j["clicker"] = clicker_;

        std::ofstream out(path);
        out << j.dump(2);
        return true;
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Could not save sessions: " << e.what() << "\n";
        return false;
    }
}

TrainingSessionRecord SessionManager::addTrainingSession(const TrainingStats& stats,
                                                          const std::string& filepath) {
    TrainingSessionRecord record;
    record.timestamp = isoNow();
    record.type = stats.trainingType;
    record.totalClicks = stats.total;
    record.avgCps = stats.avgCps;
    record.variance = stats.variance;
    record.stdDev = stats.stdDev;
    record.filepath = filepath;

    training_.push_back(record);
    save();
    return record;
}

ClickerSessionRecord SessionManager::addClickerSession(const mimic::core::engine::EngineStats& stats,
                                                        const std::string& filepath) {
    const auto assessment = mimic::core::config::RiskAssessor::assess(stats);

    ClickerSessionRecord record;
    record.timestamp = isoNow();
    record.mode = stats.enhancedMode ? "enhanced" : "standard";
    record.totalClicks = stats.total;
    record.avgCps = stats.avgCps;
    record.variance = stats.variance;
    record.stdDev = stats.stdDev;
    record.risk = mimic::core::config::riskLevelName(assessment.risk);
    record.score = assessment.score;
    record.filepath = filepath;

    clicker_.push_back(record);
    save();
    return record;
}

std::vector<TrainingSessionRecord> SessionManager::trainingSessions(std::optional<std::string> type) const {
    if (!type) return training_;
    std::vector<TrainingSessionRecord> out;
    for (const auto& r : training_) {
        if (r.type == *type) out.push_back(r);
    }
    return out;
}

std::vector<ClickerSessionRecord> SessionManager::clickerSessions(std::optional<std::string> mode) const {
    if (!mode) return clicker_;
    std::vector<ClickerSessionRecord> out;
    for (const auto& r : clicker_) {
        if (r.mode == *mode) out.push_back(r);
    }
    return out;
}

} // namespace mimic::core::session
