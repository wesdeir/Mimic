#pragma once

#include <array>
#include <cmath>
#include <stdexcept>
#include <string>

// Ported from mimic/engine.py: StateParams, STATES, STATE_NAMES,
// STATE_INDEX, TRANSITION_MATRIX.

namespace mimic::core::engine {

enum class ClickState { Butterfly = 0, Jitter = 1, Normal = 2 };

inline constexpr std::array<ClickState, 3> kAllStates = {
    ClickState::Butterfly, ClickState::Jitter, ClickState::Normal};

inline const char* stateName(ClickState s) {
    switch (s) {
        case ClickState::Butterfly: return "butterfly";
        case ClickState::Jitter: return "jitter";
        case ClickState::Normal: return "normal";
    }
    return "normal";
}

inline ClickState stateFromName(const std::string& name) {
    if (name == "butterfly") return ClickState::Butterfly;
    if (name == "jitter") return ClickState::Jitter;
    return ClickState::Normal;
}

// Mathematical preset values for a clicking profile. Immutable once
// constructed (mirrors Python's @dataclass(frozen=True)); a preset change
// builds a NEW StateParams rather than mutating one in place.
//
// Hold time and switch doubling are properties of the TECHNIQUE, not the
// session, and differ enormously between techniques. Measured over two 60s
// recordings each:
//   butterfly  hold median 33.6ms (sigma 0.645), 0.207 doubles per press
//   normal     hold median 78.6ms (sigma 0.359), 0.000 doubles per press
// Normal clicking does not double at all -- the switch only bounces on
// butterfly's short sharp taps, never on a long deliberate press.
struct StateParams {
    ClickState state;
    double baseRate;    // median interval, ms
    double sigma;       // log-scale spread
    double phi;         // AR(1) coupling
    double holdMedianMs = 46.0;
    double holdSigma = 0.62;
    double holdRho = 0.35;      // coupling between hold and the next interval
    double doubleRate = 0.20;   // doubles per intentional press
    double sigmaShock;          // derived: sigma * sqrt(1 - phi^2)

    StateParams(ClickState s, double baseRate_, double sigma_, double phi_,
                double holdMedianMs_ = 46.0, double holdSigma_ = 0.62,
                double holdRho_ = 0.35, double doubleRate_ = 0.20)
        : state(s), baseRate(baseRate_), sigma(sigma_), phi(phi_),
          holdMedianMs(holdMedianMs_), holdSigma(holdSigma_),
          holdRho(holdRho_), doubleRate(doubleRate_) {
        if (!(phi > -1.0 && phi < 1.0)) {
            throw std::invalid_argument(std::string(stateName(s)) + ": phi must satisfy |phi| < 1");
        }
        if (sigma < 0.0) {
            throw std::invalid_argument(std::string(stateName(s)) + ": sigma must be >= 0");
        }
        sigmaShock = sigma * std::sqrt(1.0 - phi * phi);
    }
};

// base_rate is the median interval, sigma the log-scale spread, both derived
// from the measured mean/CV of each technique. butterfly and normal are
// measured over two 60s recordings each; jitter is INTERPOLATED between them
// and is the one set of numbers here with no data behind it.
inline const std::array<StateParams, 3>& defaultStates() {
    static const std::array<StateParams, 3> states = {
        StateParams(ClickState::Butterfly, /*baseRate=*/122.0, /*sigma=*/0.483, /*phi=*/0.02,
                     /*holdMedian=*/33.6, /*holdSigma=*/0.645, /*holdRho=*/0.43, /*doubleRate=*/0.207),
        StateParams(ClickState::Jitter, /*baseRate=*/150.0, /*sigma=*/0.380, /*phi=*/0.06,
                     /*holdMedian=*/52.0, /*holdSigma=*/0.500, /*holdRho=*/0.55, /*doubleRate=*/0.090),
        StateParams(ClickState::Normal, /*baseRate=*/181.0, /*sigma=*/0.264, /*phi=*/0.10,
                     /*holdMedian=*/78.6, /*holdSigma=*/0.359, /*holdRho=*/0.68, /*doubleRate=*/0.000),
    };
    return states;
}

inline int stateIndex(ClickState s) { return static_cast<int>(s); }

// Row-stochastic Markov transition matrix for clicking styles.
inline const std::array<std::array<double, 3>, 3>& transitionMatrix() {
    static const std::array<std::array<double, 3>, 3> m = {{
        {0.985, 0.012, 0.003},  // from Butterfly
        {0.008, 0.984, 0.008},  // from Jitter
        {0.002, 0.010, 0.988},  // from Normal
    }};
    return m;
}

// Cumulative-sum rows for the fast inverse-CDF state draw (searchsorted
// equivalent), with the last column float-guarded to exactly 1.0.
inline const std::array<std::array<double, 3>, 3>& transitionCdf() {
    static const std::array<std::array<double, 3>, 3> cdf = [] {
        std::array<std::array<double, 3>, 3> c{};
        const auto& m = transitionMatrix();
        for (int r = 0; r < 3; ++r) {
            double running = 0.0;
            for (int col = 0; col < 3; ++col) {
                running += m[r][col];
                c[r][col] = running;
            }
            c[r][2] = 1.0;
        }
        return c;
    }();
    return cdf;
}

} // namespace mimic::core::engine
