#include "AdaptiveClickerEngine.h"

#include <algorithm>
#include <cmath>
#include <fstream>

#include "../PlatformClock.h"
#include "../config/ClickEnginePresets.h"
#include "../config/Config.h"
#include "../mouse/SyntheticClick.h"

namespace mimic::core::engine {

namespace cfg = mimic::core::config;
using mimic::core::PlatformClock;

namespace {
std::array<StateParams, 3> copyDefaultStates() {
    const auto& d = defaultStates();
    return {d[0], d[1], d[2]};
}
}  // namespace

AdaptiveClickerEngine::AdaptiveClickerEngine(bool enhancedMode, const std::string& presetName,
                                              std::uint64_t rngSeed)
    : enhancedMode_(enhancedMode),
      presetName_(presetName),
      states_(copyDefaultStates()),
      sessionStartSeconds_(PlatformClock::nowSeconds()),
      userBaseline_(0.0),
      doubleSessionFactor_(0.0),
      rng_(rngSeed != 0 ? rngSeed
                         : static_cast<std::uint64_t>(PlatformClock::nowSeconds() * 1e6)),
      normals_(rng_, RngPool::Kind::Normal),
      uniforms_(rng_, RngPool::Kind::Uniform) {
    userBaseline_ = uniformInRange(0.88, 1.12);
    doubleSessionFactor_ = uniformInRange(cfg::kDoubleSessionMin, cfg::kDoubleSessionMax);

    resetState(ClickState::Normal);
    if (!presetName.empty()) {
        setPreset(presetName);
    }
}

void AdaptiveClickerEngine::setPreset(const std::string& presetName) {
    const cfg::PresetConfig* preset = cfg::ClickEnginePresets::find(presetName);
    if (!preset) return;

    auto rebuild = [&](ClickState s, double mean, double std) {
        const StateParams& base = states_[stateIndex(s)];
        return StateParams::fromMoments(s, mean, std, base.phi, base.holdMedianMs, base.holdSigma,
                                         base.holdRho, base.doubleRate);
    };

    states_[stateIndex(ClickState::Butterfly)] =
        rebuild(ClickState::Butterfly, preset->butterflyMean, preset->butterflyStd);
    states_[stateIndex(ClickState::Jitter)] =
        rebuild(ClickState::Jitter, preset->jitterMean, preset->jitterStd);
    states_[stateIndex(ClickState::Normal)] =
        rebuild(ClickState::Normal, preset->normalMean, preset->normalStd);

    presetName_ = presetName;
    resetState(static_cast<ClickState>(idx_));
}

void AdaptiveClickerEngine::resetState(ClickState initial) {
    idx_ = stateIndex(initial);
    const StateParams& params = states_[idx_];

    phi_ = params.phi;
    sigma_ = params.sigma;
    base_ = params.baseRate;

    fromPhi_ = phi_;
    fromSigma_ = sigma_;
    fromBase_ = base_;
    blendRemaining_ = 0;

    u_ = normals_.next();  // stationary unit-variance seeding, breaks burn-in signatures
    consecutiveClicks_ = 0;
}

void AdaptiveClickerEngine::startClicking() {
    if (isActivelyClicking_) return;
    isActivelyClicking_ = true;

    userBaseline_ = uniformInRange(0.88, 1.12);
    doubleSessionFactor_ = uniformInRange(cfg::kDoubleSessionMin, cfg::kDoubleSessionMax);
    drift_ = uniformInRange(-0.15, 0.15);
    rhythmPhase_ = uniformInRange(0.0, kTwoPi);

    resetState(ClickState::Normal);

    const double startupDelay = std::abs(gaussian(0.09, 0.025));
    PlatformClock::preciseSleep(startupDelay);
}

void AdaptiveClickerEngine::stopClicking() {
    if (!isActivelyClicking_) return;
    isActivelyClicking_ = false;
    resetState(ClickState::Normal);
}

void AdaptiveClickerEngine::advanceState() {
    const auto& row = transitionCdf()[idx_];
    const double v = uniform01();  // ONE draw, checked against all thresholds --
                                    // a previous version drew fresh per threshold,
                                    // which biased the chain's stationary occupancy.
    int next = 2;
    for (int col = 0; col < 3; ++col) {
        if (v <= row[col]) {
            next = col;
            break;
        }
    }
    if (next == idx_) return;

    fromPhi_ = phi_;
    fromSigma_ = sigma_;
    fromBase_ = base_;
    idx_ = next;
    blendRemaining_ = kBlendSteps;
    ++patternBreaks_;
    if (static_cast<ClickState>(next) == ClickState::Butterfly) {
        ++burstCount_;
    }
}

void AdaptiveClickerEngine::advanceBlend() {
    const StateParams& target = states_[idx_];
    if (blendRemaining_ <= 0) {
        phi_ = target.phi;
        sigma_ = target.sigma;
        base_ = target.baseRate;
        return;
    }

    const double done = kBlendSteps - blendRemaining_ + 1;
    const double alpha = done / kBlendSteps;
    const double w = alpha * alpha * (3.0 - 2.0 * alpha);  // smoothstep

    phi_ = (1.0 - w) * fromPhi_ + w * target.phi;
    sigma_ = (1.0 - w) * fromSigma_ + w * target.sigma;
    base_ = (1.0 - w) * fromBase_ + w * target.baseRate;
    --blendRemaining_;
}

double AdaptiveClickerEngine::checkCpsSafety() {
    const double now = PlatformClock::nowSeconds();
    while (!recentClickTimes_.empty() && now - recentClickTimes_.front() > 5.0) {
        recentClickTimes_.popFront();
    }

    if (recentClickTimes_.size() >= 2) {
        int recent1s = 0;
        for (std::size_t i = 0; i < recentClickTimes_.size(); ++i) {
            if (now - recentClickTimes_[i] <= 1.0) ++recent1s;
        }
        if (recent1s >= 16) return 0.08;

        const double timeSpan = now - recentClickTimes_.front();
        const double avgCps = timeSpan > 0 ? recentClickTimes_.size() / timeSpan : 0.0;
        if (avgCps > cfg::kSustainedCpsCap) return 0.05;
    }
    return 0.0;
}

double AdaptiveClickerEngine::calculateDelay() {
    advanceState();
    advanceBlend();

    // 1. Update unit-variance core noise line.
    u_ = phi_ * u_ + std::sqrt(1.0 - phi_ * phi_) * normals_.next();

    // Log-normal: base_ is the median, sigma_ the relative spread -- gives
    // the right-skewed shape real clicking has instead of a symmetric bell.
    double base = base_ * std::exp(sigma_ * u_);

    // 2. Continuous exponential fatigue decay. consecutiveClicks_ decays
    // while idle (see click()), so this recovers during pauses instead of
    // staying pinned at the max multiplier all session.
    constexpr double kLambdaRate = 12.0;
    constexpr double kMaxFatigueSlowdown = 0.22;
    const double fatigueMultiplier =
        1.0 + kMaxFatigueSlowdown * (1.0 - std::exp(-consecutiveClicks_ / kLambdaRate));
    base *= fatigueMultiplier;

    // 3. User baseline multiplier and mean-reverting (Ornstein-Uhlenbeck)
    // drift -- decays back to centre so it only contributes short-range
    // autocorrelation, unlike an unbounded random walk.
    base *= userBaseline_;
    const double rho = cfg::kDriftReversion;
    const double shock = cfg::kDriftSigma * std::sqrt(1.0 - rho * rho);
    drift_ = rho * drift_ + shock * normals_.next();
    base *= (1.0 + drift_);

    // 4. Rhythmic sinusoidal oscillation. Stepping most of the way around
    // the circle each click keeps rhythm texture without long-range memory.
    rhythmPhase_ = std::fmod(rhythmPhase_ + uniformInRange(1.1, 2.6), kTwoPi);
    const double rhythmAmount = enhancedMode_ ? 0.055 : 0.038;
    base *= (1.0 + std::sin(rhythmPhase_) * rhythmAmount);

    // 5. Occasional long pause -- real sessions put 1.85% of clicks past
    // 250ms and reach 475ms.
    if (uniform01() < 0.018) {
        base += std::abs(gaussian(0.0, 95.0));
        ++pauseCount_;
    }

    if (sigma_ > 0 && std::abs(u_) > 2.5) {
        ++outlierCount_;
    }

    // 6. Reflect at the boundaries rather than clamp, so the histogram
    // doesn't spike exactly at the bound.
    const double lo = enhancedMode_ ? cfg::kEnhancedMinDelayMs : cfg::kAbsoluteMinDelayMs;
    const double hi = enhancedMode_ ? cfg::kEnhancedMaxDelayMs : cfg::kAbsoluteMaxDelayMs;

    double final = base;
    for (int i = 0; i < 4; ++i) {
        if (final < lo) {
            final = lo + (lo - final);
        } else if (final > hi) {
            final = hi - (final - hi);
        } else {
            break;
        }
    }
    final = std::min(hi, std::max(lo, final));

    // 7. Snap onto the USB polling grid, then re-jitter by the amount real
    // hardware jitters -- a busy-wait loop has no polling-boundary
    // constraint, which is a free synthetic-vs-hardware discriminator.
    if (cfg::kPollRateHz > 0.0) {
        const double grid = 1000.0 / cfg::kPollRateHz;
        final = std::round(final / grid) * grid + gaussian(0.0, cfg::kPollJitterMs);
        final = std::min(hi, std::max(lo, final));
    }

    clickHistory_.push(final);
    allDelays_.push(final);

    // Welford update.
    ++n_;
    const double d = final - mean_;
    mean_ += d / static_cast<double>(n_);
    m2_ += d * (final - mean_);

    return final;
}

double AdaptiveClickerEngine::drawHold(double delayMs, bool willDouble) {
    if (willDouble) {
        return std::max(1.0, gaussian(cfg::kDoublePressHoldMs, cfg::kDoublePressHoldStdMs));
    }

    // Hold parameters follow the CURRENT technique; u_ is the AR(1) noise
    // that drove this interval, so blending it into the hold's own noise
    // reproduces the observed positive hold/next-interval coupling without
    // modelling the joint distribution explicitly.
    const StateParams& st = states_[idx_];
    const double rho = st.holdRho;
    const double z = rho * u_ + std::sqrt(std::max(0.0, 1.0 - rho * rho)) * normals_.next();

    double hold = st.holdMedianMs * std::exp(st.holdSigma * z);
    hold = std::max(cfg::kHoldMinMs, hold);
    return std::min(hold, delayMs * 0.6);
}

double AdaptiveClickerEngine::currentDoubleRate() const {
    return std::min(0.85, states_[idx_].doubleRate * doubleSessionFactor_);
}

void AdaptiveClickerEngine::click() {
    const double safety = checkCpsSafety();
    if (safety > 0) {
        PlatformClock::preciseSleep(safety);
    }

    const double now = PlatformClock::nowSeconds();

    // Fatigue recovery: if idle for a moment, the hand relaxes.
    if (lastClickWallSeconds_) {
        const double idle = now - *lastClickWallSeconds_;
        if (idle > 0.35) {
            consecutiveClicks_ = static_cast<int>(consecutiveClicks_ * std::exp(-idle / 2.5));
        }
    }
    lastClickWallSeconds_ = now;

    // Full press-to-press period, matching how HumanClickTracker records
    // training data (on physical press only).
    const double delayMs = calculateDelay();

    // Decide the double BEFORE the hold: a press that gets doubled holds
    // ~17ms, one that doesn't holds ~46ms -- that structure drives most of
    // the measured +0.425 hold/next-interval correlation.
    const double gap = gaussian(cfg::kDoubleGapMs, cfg::kDoubleGapStdMs);
    const bool willDouble = cfg::kDoubleClickEmulation && uniform01() < currentDoubleRate() &&
                             delayMs - (gap + cfg::kDoubleHoldMs) >= cfg::kDoubleMinRemainderMs;

    const double pressureMs = drawHold(delayMs, willDouble);

    mimic::core::mouse::leftButtonDown();
    PlatformClock::preciseSleep(pressureMs / 1000.0);
    mimic::core::mouse::leftButtonUp();

    recentClickTimes_.push(now);
    ++totalClicks_;
    ++consecutiveClicks_;

    const double currentCps = getCurrentCps();
    cpsHistory_.push(currentCps);
    cpsTimestamps_.push(PlatformClock::nowSeconds());

    // Optional hardware-double emulation: reproduces a double-clicking
    // mouse's second actuation so the synthetic stream matches what this
    // account's hardware has always produced.
    double consumed = pressureMs;
    if (willDouble && gap > pressureMs) {
        const double budget = delayMs - gap - cfg::kDoubleMinRemainderMs;
        const double bounceHold = std::min(drawHold(delayMs, false), std::max(1.0, budget));

        PlatformClock::preciseSleep((gap - pressureMs) / 1000.0);
        mimic::core::mouse::leftButtonDown();
        PlatformClock::preciseSleep(bounceHold / 1000.0);
        mimic::core::mouse::leftButtonUp();
        consumed = gap + bounceHold;
        ++totalClicks_;
        ++doubleCount_;
    }

    // The hold is PART of the interval, not additional to it.
    PlatformClock::preciseSleep(std::max(0.0, delayMs - consumed) / 1000.0);
}

std::vector<double> AdaptiveClickerEngine::simulateStream(int n) {
    std::vector<double> out;
    out.reserve(n);
    for (int i = 0; i < n; ++i) {
        const double d = calculateDelay();
        if (cfg::kDoubleClickEmulation && uniform01() < currentDoubleRate()) {
            const double gap = gaussian(cfg::kDoubleGapMs, cfg::kDoubleGapStdMs);
            if (gap > 0 && d - gap >= cfg::kDoubleMinRemainderMs) {
                out.push_back(gap);
                out.push_back(d - gap);
                continue;
            }
        }
        out.push_back(d);
    }
    return out;
}

int AdaptiveClickerEngine::exportToCsv(const std::string& filepath) const {
    std::ofstream fh(filepath);
    if (!fh) return -1;

    fh << "click_number,relative_time_ms,delay_ms,button,click_type\n";
    const auto delays = allDelays_.toVector();
    double t = 0.0;
    int i = 1;
    fh.precision(3);
    fh << std::fixed;
    for (double d : delays) {
        t += d;
        fh << i << "," << t << "," << d << ",left,single-click\n";
        ++i;
    }
    return static_cast<int>(delays.size());
}

double AdaptiveClickerEngine::calculateVariance() const {
    if (clickHistory_.size() < 2) return 0.0;
    const auto w = clickHistory_.toVector();
    double m = 0.0;
    for (double x : w) m += x;
    m /= static_cast<double>(w.size());
    double sum = 0.0;
    for (double x : w) sum += (x - m) * (x - m);
    return sum / static_cast<double>(w.size());
}

double AdaptiveClickerEngine::calculateOverallVariance() const {
    return n_ > 1 ? m2_ / static_cast<double>(n_) : 0.0;
}

double AdaptiveClickerEngine::calculateStdDev() const {
    return std::sqrt(calculateOverallVariance());
}

double AdaptiveClickerEngine::getCurrentCps() const {
    if (clickHistory_.size() < 5) return 0.0;
    const auto recent = clickHistory_.lastN(10);
    double sum = 0.0;
    for (double d : recent) sum += d;
    const double avgDelay = sum / static_cast<double>(recent.size());
    return avgDelay > 0 ? 1000.0 / avgDelay : 0.0;
}

double AdaptiveClickerEngine::getMeasuredCps() const {
    if (recentClickTimes_.size() < 2) return 0.0;
    const double span = recentClickTimes_.back() - recentClickTimes_.front();
    return span > 0 ? (static_cast<double>(recentClickTimes_.size()) - 1) / span : 0.0;
}

EngineStats AdaptiveClickerEngine::getDetailedStats() const {
    EngineStats stats;
    if (n_ < 2) return stats;

    const double var = calculateOverallVariance();
    const double std = std::sqrt(var);
    const auto window = clickHistory_.toVector();
    const double elapsed = PlatformClock::nowSeconds() - sessionStartSeconds_;
    const double cur = getCurrentCps();
    peakCps_ = std::max(peakCps_, cur);

    stats.valid = true;
    stats.total = n_;
    stats.mean = mean_;
    stats.variance = var;
    stats.stdDev = std;
    stats.minDelay = window.empty() ? 0.0 : *std::min_element(window.begin(), window.end());
    stats.maxDelay = window.empty() ? 0.0 : *std::max_element(window.begin(), window.end());
    stats.avgCps = mean_ > 0 ? 1000.0 / mean_ : 0.0;
    stats.currentCps = cur;
    stats.maxCps = std::max(peakCps_, cur);
    stats.measuredCps = getMeasuredCps();
    stats.sessionSeconds = elapsed;
    stats.state = static_cast<ClickState>(idx_);
    stats.patternBreaks = patternBreaks_;
    stats.burstCount = burstCount_;
    stats.doubleCount = doubleCount_;
    stats.effectiveCps = stats.avgCps * (1.0 + (n_ ? static_cast<double>(doubleCount_) / n_ : 0.0));
    stats.pauseCount = pauseCount_;
    stats.outlierCount = outlierCount_;
    stats.enhancedMode = enhancedMode_;
    return stats;
}

} // namespace mimic::core::engine
