#pragma once

#include <string>

// Ported from mimic/config.py::Config. Every constant here encodes a
// measured fact from click_data/ or a deliberately chosen anti-detection
// threshold -- see the comment on each for what it is anchored to. Do not
// "clean up" a value without re-checking it against click_data/.

namespace mimic::core::config {

// Bounds fitted to click_data/ (chatter-free sessions only).
// Real observed: min 33.5ms, p01 58ms, p99 308ms, max 475ms.
inline constexpr double kAbsoluteMinDelayMs = 30.0;   // 33.3 CPS spike max
inline constexpr double kAbsoluteMaxDelayMs = 450.0;  // was 250, which clipped 1.85% of real pauses
inline constexpr double kSustainedCpsCap = 11.0;      // true human peak was 9.67 CPS once chatter removed

// Enhanced Mode has a wider range.
inline constexpr double kEnhancedMinDelayMs = 30.0;
inline constexpr double kEnhancedMaxDelayMs = 450.0;

// Gaussian distribution parameters (measured, not guessed).
inline constexpr double kEnhancedTargetMeanMs = 111.0;
inline constexpr double kEnhancedTargetStdDevMs = 42.0;

// Realistic variance targets -- real clean-session variance is ~2789.
inline constexpr double kEnhancedIdealVariance = 1800.0;
inline constexpr double kEnhancedTargetVariance = 2800.0;
inline constexpr double kEnhancedMaxVariance = 4200.0;

inline constexpr double kStandardIdealVariance = 600.0;
inline constexpr double kStandardTargetVariance = 900.0;
inline constexpr double kStandardMaxVariance = 1500.0;

inline constexpr double kMinVarianceThreshold = 800.0;
inline constexpr int kPatternCheckWindow = 20;

// Hardware emulation: a real mouse only raises events on a USB polling
// boundary, so human intervals cluster near whole milliseconds. Set to the
// polling rate of the mouse to imitate (125 / 500 / 1000), or 0 to disable
// quantization entirely.
inline constexpr double kPollRateHz = 1000.0;
inline constexpr double kPollJitterMs = 0.19;  // measured spread around the grid in click_data/

// Drift is an Ornstein-Uhlenbeck process: reversion is the per-click
// retention (closer to 1.0 = slower wander), sigma its steady-state
// amplitude as a fraction of the base interval.
inline constexpr double kDriftReversion = 0.985;
inline constexpr double kDriftSigma = 0.055;

// Double-click (switch bounce) emulation. A double-clicking mouse is
// standard kit: each physical press registers twice, so effective CPS is
// roughly 1 + doubleRate times the hand rate. Measured from the operator's
// own recordings in click_data/: doubles land 34.4ms +/- 1.6ms after the
// real press; the rate is drawn fresh per session (measured sessions ran
// 0.20, 0.21, 0.26, 0.43, 0.47, 0.79 per press).
inline constexpr bool kDoubleClickEmulation = true;
inline constexpr double kDoubleSessionMin = 0.70;
inline constexpr double kDoubleSessionMax = 1.80;
inline constexpr double kDoubleGapMs = 34.4;
inline constexpr double kDoubleGapStdMs = 1.6;
inline constexpr double kDoubleHoldMs = 17.0;

// Button hold time, measured from 1052 samples across two 60s butterfly
// recordings. Real holds are bimodal:
//   presses that get doubled : 17.27ms +/- 1.50  (the switch, not the hand)
//   every other press        : 46.14ms +/- 26.73 (lognormal, median 46)
inline constexpr double kHoldMedianMs = 46.0;
inline constexpr double kHoldSigma = 0.625;
inline constexpr double kHoldMinMs = 15.0;
inline constexpr double kHoldDelayRho = 0.35;  // tuned so realised corr lands near +0.27
inline constexpr double kDoublePressHoldMs = 17.0;
inline constexpr double kDoublePressHoldStdMs = 1.5;
// A double must leave a plausible interval behind it. Measured remainders
// after a real double run a median of 122ms with only 6.7% under 50ms.
inline constexpr double kDoubleMinRemainderMs = 50.0;

// Adaptive mode parameters.
inline constexpr int kTechniqueTransitionMin = 5;
inline constexpr int kTechniqueTransitionMax = 15;

// Click mode parameters.
inline constexpr double kBurstProbability = 0.40;
inline constexpr double kPauseProbability = 0.02;

// Outlier injection.
inline constexpr double kOutlierProbability = 0.02;

// Training thresholds.
inline constexpr int kTrainingMinClicks = 100;
inline constexpr int kTrainingRecommendedClicks = 200;
inline constexpr int kTrainingCompleteClicks = 250;

// Resolves %USERPROFILE%\Desktop\Mimic\mimic_data (via SHGetKnownFolderPath,
// so redirected/OneDrive-relocated Desktops are respected -- unlike Python's
// os.path.expanduser("~") which is not Desktop-redirection-aware).
std::wstring trainingDataPath();
std::wstring clickerDataPath();
std::wstring sessionsFilePath();
// Presets historically saved to a DIFFERENT path than everything else
// (~/Desktop/mimic_data/custom_presets.json instead of
// ~/Desktop/Mimic/mimic_data/...) -- a pre-existing Python bug. This is the
// corrected path; presetsFileLegacyPath() is kept only for one-time migration.
std::wstring presetsFilePath();
std::wstring presetsFileLegacyPath();

} // namespace mimic::core::config
