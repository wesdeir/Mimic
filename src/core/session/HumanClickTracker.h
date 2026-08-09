#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "SessionManager.h"
#include "TrainingStats.h"

// Ported from mimic/session.py::HumanClickTracker. Tracks legitimate clicks
// for baseline analysis via a Win32 low-level mouse hook (WH_MOUSE_LL),
// same mechanism the Python original used via raw ctypes.
//
// Unlike the Python original, this class NEVER shows a popup itself
// (session.py imported tkinter.messagebox directly, a UI concern leaking
// into the data layer). exportHumanStats() instead returns a result the
// caller (the GUI layer) turns into whatever dialog it wants -- see
// ExportResult below.
//
// Threading note: WH_MOUSE_LL callbacks fire on whichever thread installed
// the hook, and that thread MUST be pumping messages (GetMessage/
// PeekMessage + DispatchMessage) for Windows to deliver them at all -- so
// startTracking()/stopTracking() must be called from the app's main message-
// loop thread, not an arbitrary worker thread.

namespace mimic::core::session {

class HumanClickTracker {
public:
    explicit HumanClickTracker(SessionManager& sessionManager);
    ~HumanClickTracker();

    void startTracking(const std::string& trainingType = "normal");
    void stopTracking();
    bool isTracking() const { return isTracking_; }

    double getRollingCps(double windowSeconds = 1.0) const;
    double getMaxRollingCps(double windowSeconds = 1.0) const;
    double calculateVariance() const;
    TrainingStats getStats() const;
    bool exportToCsv(const std::string& filename) const;

    // Records one click at the given monotonic timestamp (seconds). Public
    // so both the real hook callback and tests can drive it -- the hook
    // callback is a thin adapter that calls this with PlatformClock::nowSeconds().
    void recordClick(double timestampSeconds);

    enum class ExportOutcome { Ok, InsufficientData, LowCaptureRate, IoError };
    struct ExportResult {
        ExportOutcome outcome = ExportOutcome::Ok;
        TrainingStats stats;
        std::string reportText;
        std::string txtPath;
        std::string csvPath;
        double capturePct = 0.0;
        int missedClicks = 0;
        std::string errorMessage;
    };
    // Ported from session.py::export_human_stats(), minus the popups.
    ExportResult exportHumanStats();

    std::int64_t totalClicks() const { return totalClicks_; }

private:
    void installHook();
    void uninstallHook();
    static LRESULT CALLBACK hookProc(int nCode, WPARAM wParam, LPARAM lParam);

    SessionManager& sessionManager_;
    bool isTracking_ = false;
    std::string trainingType_ = "normal";
    std::vector<double> clickTimes_;   // monotonic seconds
    std::vector<double> clickDelays_;  // ms
    std::optional<double> lastClickTime_;
    std::int64_t totalClicks_ = 0;
    double sessionStartSeconds_ = 0.0;

    HHOOK hookHandle_ = nullptr;

    static HumanClickTracker* s_active;  // WH_MOUSE_LL calls a plain function pointer, not a member
};

// Builds the same multi-section plaintext report session.py's
// export_human_stats() printed/saved, given a completed TrainingStats.
std::string buildTrainingReport(const TrainingStats& stats);

} // namespace mimic::core::session
