#pragma once

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

#include "EngineStats.h"
#include "RingBuffer.h"
#include "RngPool.h"
#include "StateParams.h"

// Ported from mimic/engine.py::AdaptiveClickerEngine. Markov-chain state
// model + log-normal delay draw, blended across state transitions via a
// smoothstep crossfade, with AR(1)-correlated noise, Ornstein-Uhlenbeck
// drift, rhythmic oscillation, boundary reflection, USB-poll-rate
// quantization, and bimodal (switch-bounce-vs-genuine) hold-time drawing.
//
// Threading contract (see port plan §2.3/§4.6): exactly ONE thread may call
// click()/calculate_delay()/set_preset()/reset_state()/start_clicking()/
// stop_clicking() on a given instance. Other threads must only read state
// via getDetailedStats(), and even then only through a synchronized snapshot
// (app::StatsSnapshot) -- this class itself has no internal locking.

namespace mimic::core::engine {

class AdaptiveClickerEngine {
public:
    explicit AdaptiveClickerEngine(bool enhancedMode = true,
                                    const std::string& presetName = "Balanced",
                                    std::uint64_t rngSeed = 0);

    // Retunes the three states from a ClickEnginePresets/PresetManager
    // entry (mean/std absolute-ms -> log-normal median/sigma, exact
    // moment-matching conversion). No-op if presetName is unknown.
    void setPreset(const std::string& presetName);
    const std::string& presetName() const { return presetName_; }

    void resetState(ClickState initial = ClickState::Normal);
    void startClicking();
    void stopClicking();
    bool isActivelyClicking() const { return isActivelyClicking_; }

    // Draws the next inter-event interval in ms. Advances internal state
    // (Markov position, AR(1) noise, drift, rhythm) but does no I/O and
    // consumes no wall-clock time.
    double calculateDelay();

    // Performs one full click: draws a delay + hold, actually presses/
    // releases the mouse button (and possibly emits a hardware-double),
    // and sleeps out the remainder of the interval. Blocking.
    void click();

    // Produces n inter-event intervals exactly as the GAME would observe
    // them (double-click emulation merges the motor sequence into the
    // event stream the same way click() does), without driving the mouse
    // or advancing wall-clock time. Used for offline validation/parity
    // testing and the differential-analysis screen.
    std::vector<double> simulateStream(int n);

    // Writes the retained delay buffer as CSV; schema matches
    // HumanClickTracker's export so sessions are cross-comparable. Returns
    // rows written, or -1 on I/O failure.
    int exportToCsv(const std::string& filepath) const;

    double calculateVariance() const;          // recent-window variance
    double calculateOverallVariance() const;   // whole-session, O(1) via Welford
    double calculateStdDev() const;
    double getCurrentCps() const;              // short-window, from modelled delays
    double getMeasuredCps() const;             // ground-truth, from wall-clock presses

    EngineStats getDetailedStats() const;

    bool enhancedMode() const { return enhancedMode_; }
    std::int64_t totalClicks() const { return totalClicks_; }
    ClickState currentState() const { return static_cast<ClickState>(idx_); }

private:
    double drawHold(double delayMs, bool willDouble);
    double currentDoubleRate() const;
    void advanceState();
    void advanceBlend();
    double checkCpsSafety();  // returns extra sleep (s) to enforce the sustained-CPS cap, else 0

    double uniform01() { return uniforms_.next(); }
    double uniformInRange(double lo, double hi) { return lo + (hi - lo) * uniforms_.next(); }
    double gaussian(double mean, double std) { return mean + std * normals_.next(); }

    bool enhancedMode_;
    std::string presetName_;
    std::array<StateParams, 3> states_;

    std::int64_t totalClicks_ = 0;
    double sessionStartSeconds_;
    bool isActivelyClicking_ = false;

    RingBuffer<double> clickHistory_{50};
    RingBuffer<double> recentClickTimes_{20};
    RingBuffer<double> allDelays_{3000};
    RingBuffer<double> cpsHistory_{60};
    RingBuffer<double> cpsTimestamps_{60};

    std::int64_t n_ = 0;
    double mean_ = 0.0;
    double m2_ = 0.0;  // Welford sum of squared deviations

    double userBaseline_;
    double drift_ = 0.0;
    double rhythmPhase_ = 0.0;
    int consecutiveClicks_ = 0;
    int patternBreaks_ = 0;
    std::optional<double> lastClickWallSeconds_;

    int burstCount_ = 0;
    int pauseCount_ = 0;
    int outlierCount_ = 0;
    mutable double peakCps_ = 0.0;  // updated from getDetailedStats(), matching Python's get_detailed_stats()
    int doubleCount_ = 0;
    double doubleSessionFactor_;

    static constexpr int kBlendSteps = 20;

    Xoshiro256PP rng_;
    RngPool normals_;
    RngPool uniforms_;

    // Markov/crossfade state.
    int idx_ = 2;  // Normal
    double phi_ = 0.0, sigma_ = 0.0, base_ = 0.0;
    double fromPhi_ = 0.0, fromSigma_ = 0.0, fromBase_ = 0.0;
    int blendRemaining_ = 0;
    double u_ = 0.0;  // AR(1) unit-variance noise line
};

} // namespace mimic::core::engine
