#include "HumanClickTracker.h"

#include <algorithm>
#include <cmath>
#include <ctime>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>

#include "../PlatformClock.h"
#include "../config/Config.h"

namespace mimic::core::session {

namespace fs = std::filesystem;
using mimic::core::PlatformClock;

HumanClickTracker* HumanClickTracker::s_active = nullptr;

HumanClickTracker::HumanClickTracker(SessionManager& sessionManager) : sessionManager_(sessionManager) {}

HumanClickTracker::~HumanClickTracker() { uninstallHook(); }

void HumanClickTracker::startTracking(const std::string& trainingType) {
    isTracking_ = true;
    trainingType_ = trainingType;
    sessionStartSeconds_ = PlatformClock::nowSeconds();
    clickTimes_.clear();
    clickDelays_.clear();
    lastClickTime_.reset();
    totalClicks_ = 0;

    installHook();
}

void HumanClickTracker::stopTracking() {
    isTracking_ = false;
    uninstallHook();
}

void HumanClickTracker::installHook() {
    s_active = this;
    hookHandle_ = SetWindowsHookExW(WH_MOUSE_LL, &HumanClickTracker::hookProc, GetModuleHandleW(nullptr), 0);
}

void HumanClickTracker::uninstallHook() {
    if (hookHandle_) {
        UnhookWindowsHookEx(hookHandle_);
        hookHandle_ = nullptr;
    }
    if (s_active == this) {
        s_active = nullptr;
    }
}

LRESULT CALLBACK HumanClickTracker::hookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0 && s_active && s_active->isTracking_ && wParam == WM_LBUTTONDOWN) {
        s_active->recordClick(PlatformClock::nowSeconds());
    }
    HHOOK handle = s_active ? s_active->hookHandle_ : nullptr;
    return CallNextHookEx(handle, nCode, wParam, lParam);
}

void HumanClickTracker::recordClick(double timestampSeconds) {
    clickTimes_.push_back(timestampSeconds);
    ++totalClicks_;

    if (lastClickTime_) {
        const double delayMs = (timestampSeconds - *lastClickTime_) * 1000.0;
        // Lowered to 1ms (from a stricter floor) to capture ultra-fast
        // butterfly clicks, matching session.py's _record_click_precise().
        if (delayMs >= 1.0 && delayMs < 2000.0) {
            clickDelays_.push_back(delayMs);
        }
    }
    lastClickTime_ = timestampSeconds;
}

double HumanClickTracker::getRollingCps(double windowSeconds) const {
    if (clickTimes_.size() < 2) return 0.0;
    const double lastClick = clickTimes_.back();
    const double cutoff = lastClick - windowSeconds;
    long long recent = 0;
    for (double t : clickTimes_) {
        if (t >= cutoff) ++recent;
    }
    return recent / windowSeconds;
}

double HumanClickTracker::getMaxRollingCps(double windowSeconds) const {
    if (clickTimes_.size() < 10) return 0.0;
    double maxCps = 0.0;
    // O(n^2), matching session.py::get_max_rolling_cps() exactly (not fixed
    // here: sessions are capped at a few thousand clicks, so this is not a
    // practical bottleneck, and it's not a behavioral bug worth diverging on).
    for (std::size_t i = 0; i < clickTimes_.size(); ++i) {
        const double timestamp = clickTimes_[i];
        const double cutoff = timestamp - windowSeconds;
        long long count = 0;
        for (double t : clickTimes_) {
            if (t >= cutoff && t <= timestamp) ++count;
        }
        maxCps = std::max(maxCps, count / windowSeconds);
    }
    return maxCps;
}

double HumanClickTracker::calculateVariance() const {
    if (clickDelays_.size() < 10) return 0.0;
    double mean = 0.0;
    for (double d : clickDelays_) mean += d;
    mean /= static_cast<double>(clickDelays_.size());
    double sum = 0.0;
    for (double d : clickDelays_) sum += (d - mean) * (d - mean);
    return sum / static_cast<double>(clickDelays_.size());
}

TrainingStats HumanClickTracker::getStats() const {
    TrainingStats stats;
    if (clickDelays_.size() < 10) return stats;

    const auto& delays = clickDelays_;
    double sum = 0.0;
    for (double d : delays) sum += d;
    const double avgDelay = sum / static_cast<double>(delays.size());

    std::vector<double> sorted = delays;
    std::sort(sorted.begin(), sorted.end());
    auto pct = [&](double frac) { return sorted[static_cast<std::size_t>(sorted.size() * frac)]; };
    const double p10 = pct(0.10);
    const double p50 = pct(0.50);
    const double p90 = pct(0.90);

    const double sessionDuration = PlatformClock::nowSeconds() - sessionStartSeconds_;
    const double captureRate = totalClicks_ > 0
                                    ? static_cast<double>(delays.size()) / static_cast<double>(totalClicks_)
                                    : 0.0;
    const double maxRollingCps = getMaxRollingCps(1.0);
    const double avgCps = sessionDuration > 0 ? static_cast<double>(clickTimes_.size()) / sessionDuration : 0.0;

    const auto [minDelayIt, maxDelayIt] = std::minmax_element(delays.begin(), delays.end());

    stats.valid = true;
    stats.total = totalClicks_;
    stats.validDelays = static_cast<std::int64_t>(delays.size());
    stats.captureRate = captureRate;
    stats.avgCps = avgCps;
    stats.minCps = 1000.0 / *maxDelayIt;
    stats.maxCps = 1000.0 / *minDelayIt;
    stats.medianCps = 1000.0 / p50;
    stats.peakCps = maxRollingCps;
    stats.variance = calculateVariance();
    stats.stdDev = std::sqrt(stats.variance);
    stats.sessionDurationSeconds = sessionDuration;
    stats.p10DelayMs = p10;
    stats.p50DelayMs = p50;
    stats.p90DelayMs = p90;
    stats.minDelayMs = *minDelayIt;
    stats.maxDelayMs = *maxDelayIt;
    stats.avgDelayMs = avgDelay;
    stats.trainingType = trainingType_;
    return stats;
}

bool HumanClickTracker::exportToCsv(const std::string& filename) const {
    std::ofstream fh(filename);
    if (!fh) return false;

    fh << "Click_Number,Delay_MS,CPS,Training_Type\n";
    fh << std::fixed << std::setprecision(2);
    int i = 1;
    for (double delay : clickDelays_) {
        const double cps = delay > 0 ? 1000.0 / delay : 0.0;
        fh << i << "," << delay << "," << cps << "," << trainingType_ << "\n";
        ++i;
    }
    return true;
}

namespace {
std::string timestampForFilename() {
    const auto now = std::chrono::system_clock::now();
    const std::time_t t = std::chrono::system_clock::to_time_t(now);
    std::tm tmBuf;
    localtime_s(&tmBuf, &t);
    std::ostringstream ss;
    ss << std::put_time(&tmBuf, "%Y%m%d_%H%M%S");
    return ss.str();
}

std::string toLower(std::string s) {
    for (auto& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}
} // namespace

HumanClickTracker::ExportResult HumanClickTracker::exportHumanStats() {
    ExportResult result;
    const TrainingStats stats = getStats();

    if (!stats.valid) {
        result.outcome = ExportOutcome::InsufficientData;
        result.stats = stats;
        return result;
    }

    if (stats.captureRate < 0.95) {
        result.capturePct = stats.captureRate * 100.0;
        result.missedClicks = static_cast<int>(stats.total - stats.validDelays);
        result.outcome = ExportOutcome::LowCaptureRate;
        // Not returned early: Python only WARNS on low capture rate and
        // still proceeds to export, so this continues below too.
    }

    result.reportText = buildTrainingReport(stats);
    result.stats = stats;

    const std::string typeSafe = toLower(stats.trainingType);
    const std::string ts = timestampForFilename();
    const fs::path folder = fs::path(mimic::core::config::trainingDataPath()) / typeSafe;

    try {
        std::error_code ec;
        fs::create_directories(folder, ec);

        const fs::path txtPath = folder / (typeSafe + "_baseline_" + ts + ".txt");
        std::ofstream txtOut(txtPath);
        txtOut << result.reportText;
        result.txtPath = txtPath.string();

        const fs::path csvPath = folder / (typeSafe + "_baseline_" + ts + ".csv");
        exportToCsv(csvPath.string());
        result.csvPath = csvPath.string();

        sessionManager_.addTrainingSession(stats, result.txtPath);

        if (result.outcome != ExportOutcome::LowCaptureRate) {
            result.outcome = ExportOutcome::Ok;
        }
    } catch (const std::exception& e) {
        result.outcome = ExportOutcome::IoError;
        result.errorMessage = e.what();
    }

    return result;
}

std::string buildTrainingReport(const TrainingStats& stats) {
    std::string typeUpper = stats.trainingType;
    for (auto& c : typeUpper) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));

    std::string characteristics;
    if (stats.trainingType == "butterfly") {
        characteristics =
            "Butterfly (2 fingers alternating)";
    } else if (stats.trainingType == "jitter") {
        characteristics = "Jitter (rapid wrist/arm)";
    } else if (stats.trainingType == "normal") {
        characteristics = "Normal (single finger)";
    } else {
        characteristics = "Mixed Techniques";
    }

    std::string consistency = stats.variance < 200   ? "High"
                               : stats.variance < 400 ? "Moderate"
                               : stats.variance < 1500 ? "Variable"
                                                        : "Highly Variable";
    std::string patternConsistency = stats.variance < 300    ? "Very Consistent"
                                      : stats.variance < 1000 ? "Moderate"
                                                               : "Highly Variable";

    std::ostringstream out;
    out << std::fixed << std::setprecision(2);
    out << "\n"
        << "================================================================================\n"
        << "MIMIC - HUMAN CLICK ANALYSIS - " << typeUpper << " CLICKING PATTERN\n"
        << "================================================================================\n"
        << "Training Mode: " << typeUpper << "\n"
        << "Click Type: " << characteristics << "\n\n\n"
        << "SESSION OVERVIEW\n"
        << "--------------------------------------------------------------------------------\n"
        << "Total Clicks Recorded:     " << stats.total << "\n"
        << "Valid Click Intervals:     " << stats.validDelays << "\n"
        << "Capture Rate:              " << (stats.captureRate * 100.0) << "%\n"
        << "Session Duration:          " << stats.sessionDurationSeconds << " seconds\n\n\n"
        << "Peak CPS (1s window):      " << stats.peakCps << "\n"
        << "Session Average CPS:       " << stats.avgCps << "\n"
        << "Median CPS:                " << stats.medianCps << "\n\n\n"
        << "CPS STATISTICS\n"
        << "--------------------------------------------------------------------------------\n"
        << "Peak 1-Second CPS:         " << stats.peakCps << "\n"
        << "Session Average CPS:       " << stats.avgCps << "\n"
        << "Median CPS:                " << stats.medianCps << "\n"
        << "Minimum CPS:               " << stats.minCps << "\n"
        << "Maximum CPS (instant):     " << stats.maxCps << "\n"
        << "CPS Range:                 " << stats.minCps << " - " << stats.maxCps << "\n\n\n"
        << "DELAY STATISTICS (milliseconds)\n"
        << "--------------------------------------------------------------------------------\n"
        << "Average Delay:             " << stats.avgDelayMs << " ms\n"
        << "Median Delay (P50):        " << stats.p50DelayMs << " ms\n"
        << "10th Percentile (P10):     " << stats.p10DelayMs << " ms\n"
        << "90th Percentile (P90):     " << stats.p90DelayMs << " ms\n"
        << "Min Delay:                 " << stats.minDelayMs << " ms\n"
        << "Max Delay:                 " << stats.maxDelayMs << " ms\n\n\n"
        << "HUMAN BEHAVIOR METRICS\n"
        << "--------------------------------------------------------------------------------\n"
        << "Variance:                  " << std::setprecision(0) << stats.variance << std::setprecision(2)
        << "\n"
        << "Standard Deviation:        " << stats.stdDev << "\n"
        << "Consistency:               " << consistency << "\n\n\n"
        << "================================================================================\n"
        << "CLICK TYPE CHARACTERISTICS - " << typeUpper << "\n"
        << "================================================================================\n";

    if (stats.trainingType == "butterfly") {
        out << "\nBUTTERFLY CLICKING PATTERN:\n"
            << "- Expected: High CPS (10-20+), very high variance (1,800-3,500)\n"
            << "- Two-finger alternating technique\n"
            << "- Common variance: 1,800-3,500\n"
            << "- Burst patterns with occasional pauses\n";
    } else if (stats.trainingType == "jitter") {
        out << "\nJITTER CLICKING PATTERN:\n"
            << "- Expected: Moderate-High CPS (8-14), moderate variance (800-1,800)\n"
            << "- Rapid wrist/arm tension technique\n"
            << "- More consistent than butterfly\n"
            << "- Sustained clicking without bursts\n";
    } else if (stats.trainingType == "normal") {
        out << "\nNORMAL CLICKING PATTERN:\n"
            << "- Expected: Lower CPS (5-9), low-moderate variance (400-900)\n"
            << "- Single finger tapping\n"
            << "- Most consistent pattern\n"
            << "- Natural rhythm with occasional variation\n";
    } else {
        out << "\nMIXED CLICKING PATTERN:\n"
            << "- Combination of multiple techniques\n"
            << "- Varied CPS and variance depending on switching\n"
            << "- Adaptive clicking style\n";
    }

    out << "\n\nYOUR " << typeUpper << " PATTERN ANALYSIS:\n"
        << "--------------------------------------------------------------------------------\n"
        << "Your Peak CPS (1s):        " << stats.peakCps << "\n"
        << "Your Average CPS:          " << stats.avgCps << "\n"
        << "Your Variance:             " << std::setprecision(0) << stats.variance << std::setprecision(2)
        << "\n"
        << "Your Std Deviation:        " << stats.stdDev << "\n"
        << "Pattern Consistency:       " << patternConsistency << "\n\n\n"
        << "RECOMMENDATION FOR MIMIC:\n"
        << "--------------------------------------------------------------------------------\n";

    if (stats.variance > 2000) {
        out << "Use Enhanced Mode - Your variance matches butterfly clicking\n";
    } else if (stats.variance > 800) {
        out << "Use Enhanced Mode - Good for jitter-style clicking\n";
    } else {
        out << "Your variance is low for this technique - May need more practice\n";
    }

    out << "\n================================================================================\n"
        << "FILE SAVED TO DESKTOP\n"
        << "================================================================================\n";

    return out.str();
}

} // namespace mimic::core::session
