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

namespace mimic::core::engine {

class AdaptiveClickerEngine {
public:
    explicit AdaptiveClickerEngine(bool enhancedMode = true,
                                    const std::string& presetName = "Balanced",
                                    std::uint64_t rngSeed = 0);

    void setPreset(const std::string& presetName);
    const std::string& presetName() const { return presetName_; }

    void resetState(ClickState initial = ClickState::Normal);
    void startClicking();
    void stopClicking();
    bool isActivelyClicking() const { return isActivelyClicking_; }

    double calculateDelay();
    void click();

    std::vector<double> simulateStream(int n);
    int exportToCsv(const std::string& filepath) const;

    double calculateVariance() const;
    double calculateOverallVariance() const;
    double calculateStdDev() const;
    double getCurrentCps() const;
    double getMeasuredCps() const;

    EngineStats getDetailedStats() const;

    bool enhancedMode() const { return enhancedMode_; }
    void setEnhancedMode(bool enabled) { enhancedMode_ = enabled; }
    std::int64_t totalClicks() const { return totalClicks_; }
    ClickState currentState() const { return static_cast<ClickState>(idx_); }

    // --- Target CPS (overrides preset mean) ---
    void setTargetCps(double cps);
    double targetCps() const { return targetCps_; }

private:
    double drawHold(double delayMs, bool willDouble);
    double currentDoubleRate() const;
    void advanceState();
    void advanceBlend();
    double checkCpsSafety();

    // Fractional Gaussian noise
    void updateFracWeights();
    double generateFracNoise();

    // Ex‑Gaussian generation
    double generateExGaussian(double mu, double sigma, double alpha, double lambda);

    // Compute base_ to meet target CPS under current parameters
    double computeBaseForTarget() const;

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
    double m2_ = 0.0;

    double userBaseline_;
    double drift_ = 0.0;
    double rhythmPhase_ = 0.0;
    int consecutiveClicks_ = 0;
    int patternBreaks_ = 0;
    std::optional<double> lastClickWallSeconds_;

    int burstCount_ = 0;
    int pauseCount_ = 0;
    int outlierCount_ = 0;
    mutable double peakCps_ = 0.0;
    int doubleCount_ = 0;
    double doubleSessionFactor_;

    static constexpr int kBlendSteps = 20;

    Xoshiro256PP rng_;
    RngPool normals_;
    RngPool uniforms_;

    int idx_ = 2;
    double phi_ = 0.0, sigma_ = 0.0, base_ = 0.0;
    double fromPhi_ = 0.0, fromSigma_ = 0.0, fromBase_ = 0.0;
    int blendRemaining_ = 0;
    double u_ = 0.0;

    // Fractional noise
    double d_param_;
    double last_weights_d_;
    int fgn_memory_length_;
    std::vector<double> fgn_innovations_;
    std::vector<double> fgn_weights_;
    int fgn_index_;

    // Drifting parameters
    double fatigueLambda_;
    double fatigueMax_;
    double rhythmAmount_;
    double doubleClickAlpha_;
    double motorSigma_;
    double exGaussAlpha_;
    double exGaussLambda_;
    double weberCV_;

    // Wing‑Kristofferson
    double motorDelayPrev_ = 0.0;

    // Polling drift
    double pollPhaseDrift_;
    double pollDriftRate_;
    double effectivePollPeriod_;
    bool pollSkipNext_ = false;

    // Target CPS (overrides preset mean)
    double targetCps_ = 12.0;

    double softReflect(double value, double lo, double hi);
};

} // namespace mimic::core::engine