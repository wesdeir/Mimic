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

// ----------------------------------------------------------------------
// Constructor
// ----------------------------------------------------------------------
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
      uniforms_(rng_, RngPool::Kind::Uniform),
      d_param_(0.0),
      last_weights_d_(-1.0),
      fgn_memory_length_(100),
      fgn_innovations_(fgn_memory_length_, 0.0),
      fgn_weights_(fgn_memory_length_, 0.0),
      fgn_index_(0),
      fatigueLambda_(0.0),
      fatigueMax_(0.0),
      rhythmAmount_(0.0),
      doubleClickAlpha_(0.0),
      motorSigma_(0.0),
      exGaussAlpha_(0.0),
      exGaussLambda_(10.0),
      weberCV_(0.0),
      pollPhaseDrift_(0.0),
      pollDriftRate_(0.0),
      effectivePollPeriod_(cfg::kPollRateHz > 0 ? 1000.0 / cfg::kPollRateHz : 0.0),
      targetCps_(12.0)
{
    d_param_ = uniformInRange(0.2, 0.4);
    userBaseline_ = uniformInRange(0.88, 1.12);
    doubleSessionFactor_ = uniformInRange(cfg::kDoubleSessionMin, cfg::kDoubleSessionMax);

    fatigueLambda_ = uniformInRange(8.0, 18.0);
    fatigueMax_    = uniformInRange(0.15, 0.30);

    rhythmAmount_ = uniformInRange(0.025, 0.075);
    doubleClickAlpha_ = uniformInRange(0.15, 0.35);

    motorSigma_ = uniformInRange(8.0, 15.0);
    weberCV_    = uniformInRange(0.04, 0.08);
    exGaussAlpha_ = uniformInRange(0.3, 0.7);
    pollDriftRate_ = uniformInRange(-50.0, 50.0);

    updateFracWeights();

    // ---- FIX: pre‑seed the FGN innovation buffer ----
    for (int i = 0; i < fgn_memory_length_; ++i) {
        fgn_innovations_[i] = normals_.next();
    }

    resetState(ClickState::Normal);
    if (!presetName.empty()) setPreset(presetName);
}

// ----------------------------------------------------------------------
// Preset management
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::setPreset(const std::string& presetName) {
    const cfg::PresetConfig* preset = cfg::ClickEnginePresets::find(presetName);
    if (!preset) return;

    auto rebuild = [&](ClickState s, double mean, double std) {
        const StateParams& base = states_[stateIndex(s)];
        return StateParams::fromMoments(s, mean, std, base.phi, base.holdMedianMs,
                                         base.holdSigma, base.holdRho, base.doubleRate);
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
    phi_   = params.phi;
    sigma_ = params.sigma;
    base_  = computeBaseForTarget();   // target‑CPS calibrated
    fromPhi_ = phi_; fromSigma_ = sigma_; fromBase_ = base_;
    blendRemaining_ = 0;
    u_ = normals_.next();
    consecutiveClicks_ = 0;
    motorDelayPrev_ = 0.0;
}

// ----------------------------------------------------------------------
// Target CPS setter
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::setTargetCps(double cps) {
    targetCps_ = std::max(1.0, std::min(cps, 20.0));
    if (isActivelyClicking_) {
        base_ = computeBaseForTarget();
    }
}

// ----------------------------------------------------------------------
// Compute base median to meet target CPS
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::computeBaseForTarget() const {
    double weberFactor = std::exp(0.5 * weberCV_ * weberCV_);
    double fatigueFactor = 1.0 + fatigueMax_;   // steady‑state average
    double multiplier = weberFactor * fatigueFactor;
    double targetMs = 1000.0 / targetCps_;
    return targetMs / std::max(multiplier, 0.7);
}

// ----------------------------------------------------------------------
// Session start/stop
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::startClicking() {
    if (isActivelyClicking_) return;
    isActivelyClicking_ = true;

    userBaseline_ = uniformInRange(0.88, 1.12);
    doubleSessionFactor_ = uniformInRange(cfg::kDoubleSessionMin, cfg::kDoubleSessionMax);
    drift_ = uniformInRange(-0.15, 0.15);
    rhythmPhase_ = uniformInRange(0.0, kTwoPi);

    fatigueLambda_ = uniformInRange(8.0, 18.0);
    fatigueMax_    = uniformInRange(0.15, 0.30);
    rhythmAmount_  = uniformInRange(0.025, 0.075);
    doubleClickAlpha_ = uniformInRange(0.15, 0.35);
    motorSigma_    = uniformInRange(8.0, 15.0);
    weberCV_       = uniformInRange(0.04, 0.08);
    exGaussAlpha_  = uniformInRange(0.3, 0.7);
    pollDriftRate_ = uniformInRange(-50.0, 50.0);
    pollPhaseDrift_ = 0.0;
    effectivePollPeriod_ = cfg::kPollRateHz > 0 ? 1000.0 / cfg::kPollRateHz : 0.0;

    resetState(ClickState::Normal);
    const double startupDelay = std::abs(gaussian(0.09, 0.025));
    PlatformClock::preciseSleep(startupDelay);
}

void AdaptiveClickerEngine::stopClicking() {
    if (!isActivelyClicking_) return;
    isActivelyClicking_ = false;
    resetState(ClickState::Normal);
}

// ----------------------------------------------------------------------
// State blending
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::advanceState() {
    const auto& row = transitionCdf()[idx_];
    const double v = uniform01();
    int next = 2;
    for (int col = 0; col < 3; ++col) {
        if (v <= row[col]) { next = col; break; }
    }
    if (next == idx_) return;

    fromPhi_ = phi_; fromSigma_ = sigma_; fromBase_ = base_;
    idx_ = next;
    blendRemaining_ = kBlendSteps;
    ++patternBreaks_;
    if (static_cast<ClickState>(next) == ClickState::Butterfly) ++burstCount_;
}

void AdaptiveClickerEngine::advanceBlend() {
    const StateParams& target = states_[idx_];
    if (blendRemaining_ <= 0) {
        phi_ = target.phi; sigma_ = target.sigma; base_ = computeBaseForTarget();
        return;
    }
    const double done = kBlendSteps - blendRemaining_ + 1;
    const double alpha = done / kBlendSteps;
    const double w = alpha * alpha * (3.0 - 2.0 * alpha);
    phi_   = (1.0 - w) * fromPhi_   + w * target.phi;
    sigma_ = (1.0 - w) * fromSigma_ + w * target.sigma;
    base_  = (1.0 - w) * fromBase_  + w * computeBaseForTarget();
    --blendRemaining_;
}

// ----------------------------------------------------------------------
// CPS safety (soft probabilistic)
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::checkCpsSafety() {
    const double now = PlatformClock::nowSeconds();
    while (!recentClickTimes_.empty() && now - recentClickTimes_.front() > 5.0)
        recentClickTimes_.popFront();

    if (recentClickTimes_.size() >= 2) {
        int recent1s = 0;
        for (std::size_t i = 0; i < recentClickTimes_.size(); ++i)
            if (now - recentClickTimes_[i] <= 1.0) ++recent1s;

        if (recent1s >= 15) {
            const double excess = (recent1s - 14.0) / 3.0;
            const double scale = std::max(0.0, excess) * 0.09;
            const double extra = gaussian(scale, scale * 0.5);
            if (extra > 0) return extra;
        }
        const double timeSpan = now - recentClickTimes_.front();
        if (timeSpan > 3.0) {
            const double avgCps = recentClickTimes_.size() / timeSpan;
            if (avgCps > 14.5) return gaussian(0.015, 0.005);
        }
    }
    return 0.0;
}

// ----------------------------------------------------------------------
// Fractional Gaussian noise helpers
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::updateFracWeights() {
    const double d = d_param_;
    double sum_sq = 0.0;
    double psi = 1.0;
    fgn_weights_[0] = psi;
    sum_sq += psi * psi;
    for (int k = 1; k < fgn_memory_length_; ++k) {
        psi *= (k - 1 + d) / k;
        fgn_weights_[k] = psi;
        sum_sq += psi * psi;
    }
    const double inv_norm = 1.0 / std::sqrt(sum_sq);
    for (int k = 0; k < fgn_memory_length_; ++k)
        fgn_weights_[k] *= inv_norm;
    last_weights_d_ = d;
}

double AdaptiveClickerEngine::generateFracNoise() {
    const double eps = normals_.next();
    fgn_innovations_[fgn_index_] = eps;
    fgn_index_ = (fgn_index_ + 1) % fgn_memory_length_;

    double u = 0.0;
    int idx = fgn_index_ - 1;
    for (int k = 0; k < fgn_memory_length_; ++k) {
        if (idx < 0) idx += fgn_memory_length_;
        u += fgn_weights_[k] * fgn_innovations_[idx];
        --idx;
    }
    return u;
}

// ----------------------------------------------------------------------
// Ex‑Gaussian generation
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::generateExGaussian(double mu, double sigma,
                                                 double alpha, double lambda) {
    double u = uniform01();
    double expVal = -std::log(1.0 - u) / lambda;
    double normVal = gaussian(0.0, sigma);
    return mu + alpha * (expVal - 1.0 / lambda) + normVal;
}

// ----------------------------------------------------------------------
// Soft boundary reflection (FIX: no FGN consumption)
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::softReflect(double value, double lo, double hi) {
    for (int attempt = 0; attempt < 10; ++attempt) {
        // Use an independent normal draw instead of generateFracNoise()
        double u = gaussian(0.0, 1.0);   // independent, does not advance FGN state
        double redraw = base_ * std::exp(weberCV_ * u) * userBaseline_;
        redraw *= 1.0 + fatigueMax_ * (1.0 - std::exp(-consecutiveClicks_ / fatigueLambda_));
        if (redraw >= lo && redraw <= hi) return redraw;
    }
    if (value < lo) return lo + uniformInRange(0.0, (lo - value) * 0.5);
    else            return hi - uniformInRange(0.0, (value - hi) * 0.5);
}

// ----------------------------------------------------------------------
// Core delay calculation (full pipeline)
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::calculateDelay() {
    advanceState();
    advanceBlend();

    // Diffuse fractional parameter d
    d_param_ += gaussian(0.0, 0.00015);
    d_param_ = std::max(0.15, std::min(0.45, d_param_));
    if (std::fabs(d_param_ - last_weights_d_) > 0.005) updateFracWeights();

    // Drift all non‑stationary parameters
    fatigueLambda_  += gaussian(0.0, 0.0002);
    fatigueLambda_   = std::max(7.0, std::min(20.0, fatigueLambda_));
    fatigueMax_     += gaussian(0.0, 0.0001);
    fatigueMax_      = std::max(0.12, std::min(0.35, fatigueMax_));
    rhythmAmount_   += gaussian(0.0, 0.0002);
    rhythmAmount_    = std::max(0.015, std::min(0.095, rhythmAmount_));
    userBaseline_   += gaussian(0.0, 0.0001);
    if (userBaseline_ < 0.85) userBaseline_ += 0.001;
    if (userBaseline_ > 1.15) userBaseline_ -= 0.001;
    doubleClickAlpha_ += gaussian(0.0, 0.00015);
    doubleClickAlpha_  = std::max(0.1, std::min(0.4, doubleClickAlpha_));
    motorSigma_     += gaussian(0.0, 0.02);
    motorSigma_      = std::max(5.0, std::min(20.0, motorSigma_));
    weberCV_        += gaussian(0.0, 0.0003);
    weberCV_         = std::max(0.03, std::min(0.10, weberCV_));
    exGaussAlpha_   += gaussian(0.0, 0.002);
    exGaussAlpha_    = std::max(0.2, std::min(0.9, exGaussAlpha_));

    // Polling drift & occasional skips
    pollPhaseDrift_ += pollDriftRate_ * 1e-6 * effectivePollPeriod_;
    effectivePollPeriod_ = (cfg::kPollRateHz > 0)
        ? (1000.0 / cfg::kPollRateHz) * (1.0 + pollDriftRate_ * 1e-6 * totalClicks_) : 0.0;
    pollSkipNext_ = (uniform01() < 0.005);

    u_ = generateFracNoise();                       // fractional Gaussian

    double mu = base_ * std::exp(weberCV_ * u_);    // Weber core
    mu *= 1.0 + fatigueMax_ * (1.0 - std::exp(-consecutiveClicks_ / fatigueLambda_));
    mu *= userBaseline_;

    // Economic drift (mean-reverting)
    const double rho = cfg::kDriftReversion;
    const double shock = cfg::kDriftSigma * std::sqrt(1.0 - rho * rho);
    drift_ = rho * drift_ + shock * normals_.next();
    mu *= (1.0 + drift_);

    // Rhythmic modulation
    rhythmPhase_ = std::fmod(rhythmPhase_ + uniformInRange(1.1, 2.6), kTwoPi);
    mu *= (1.0 + std::sin(rhythmPhase_) * rhythmAmount_);

    // Rare missed swing (single‑interval elongation)
    if (uniform01() < 0.001) {
        mu *= uniformInRange(1.8, 2.2);
        ++pauseCount_;
    }

    // Central clock interval (ex‑Gaussian, with FGN in the normal part)
    double clockInterval = generateExGaussian(mu, weberCV_ * mu, exGaussAlpha_, exGaussLambda_);

    // Motor delay M_k (Gamma(2, motorSigma_/2) via sum of two exponentials)
    double e1 = -std::log(1.0 - uniform01());
    double e2 = -std::log(1.0 - uniform01());
    double motorDelay = (e1 + e2) * (motorSigma_ / 2.0);

    // Wing‑Kristofferson output
    double interval = clockInterval + motorDelay - motorDelayPrev_;
    motorDelayPrev_ = motorDelay;

    if (sigma_ > 0 && std::abs(u_) > 2.5) ++outlierCount_;

    const double lo = enhancedMode_ ? cfg::kEnhancedMinDelayMs : cfg::kAbsoluteMinDelayMs;
    const double hi = enhancedMode_ ? cfg::kEnhancedMaxDelayMs : cfg::kAbsoluteMaxDelayMs;

    if (interval < lo || interval > hi) interval = softReflect(interval, lo, hi);
    interval = std::min(hi, std::max(lo, interval));

    // Polling quantisation with drift
    if (cfg::kPollRateHz > 0.0 && !pollSkipNext_) {
        const double grid = effectivePollPeriod_;
        interval = std::round(interval / grid) * grid + gaussian(0.0, cfg::kPollJitterMs);
        interval = std::min(hi, std::max(lo, interval));
    }

    clickHistory_.push(interval);
    allDelays_.push(interval);
    ++n_;
    const double d = interval - mean_;
    mean_ += d / static_cast<double>(n_);
    m2_ += d * (interval - mean_);
    return interval;
}

// ----------------------------------------------------------------------
// Hold time generation (correlated with u_)
// ----------------------------------------------------------------------
double AdaptiveClickerEngine::drawHold(double delayMs, bool willDouble) {
    if (willDouble) {
        return std::max(1.0, gaussian(cfg::kDoublePressHoldMs, cfg::kDoublePressHoldStdMs));
    }

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

// ----------------------------------------------------------------------
// Click execution (with coupled double‑click gap)
// ----------------------------------------------------------------------
void AdaptiveClickerEngine::click() {
    const double safety = checkCpsSafety();
    if (safety > 0) {
        PlatformClock::preciseSleep(safety);
    }

    const double now = PlatformClock::nowSeconds();

    if (lastClickWallSeconds_) {
        const double idle = now - *lastClickWallSeconds_;
        if (idle > 0.35) {
            consecutiveClicks_ = static_cast<int>(consecutiveClicks_ * std::exp(-idle / 2.5));
        }
    }
    lastClickWallSeconds_ = now;

    const double delayMs = calculateDelay();

    const double baseGap = doubleClickAlpha_ * delayMs;
    const double gap = baseGap + gaussian(0.0, cfg::kDoubleGapStdMs);
    const bool willDouble = cfg::kDoubleClickEmulation && uniform01() < currentDoubleRate() &&
                             gap > 0.0 && delayMs - (gap + cfg::kDoubleHoldMs) >= cfg::kDoubleMinRemainderMs;

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

    PlatformClock::preciseSleep(std::max(0.0, delayMs - consumed) / 1000.0);
}

// ----------------------------------------------------------------------
// Simulation & CSV export
// ----------------------------------------------------------------------
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

// ----------------------------------------------------------------------
// Statistics
// ----------------------------------------------------------------------
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