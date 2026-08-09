#pragma once

#include <array>
#include <cmath>
#include <cstdint>
#include <random>
#include <vector>

// Replaces mimic/engine.py's numpy-backed _Pool. Exact bit-for-bit parity
// with numpy's PCG64 is unreachable from C++ regardless of generator choice
// (see the port plan's parity-testing rationale), so this targets a fast,
// well-tested, EXPLICIT algorithm instead: xoshiro256++ for the bit stream,
// Box-Muller for the normal transform, both chosen so the test suite's
// expected moments are derived from a known, documented method rather than
// "whatever the standard library happens to implement."

namespace mimic::core::engine {

inline constexpr double kTwoPi = 6.283185307179586476925286766559;

// xoshiro256++ 1.0 (David Blackman & Sebastiano Vigna, public domain).
class Xoshiro256PP {
public:
    explicit Xoshiro256PP(std::uint64_t seed) {
        // Seed the state via SplitMix64, the standard way to expand a single
        // 64-bit seed into xoshiro's 256-bit state without weak initial
        // correlations.
        std::uint64_t sm = seed;
        auto splitmix64 = [&sm]() {
            sm += 0x9E3779B97F4A7C15ULL;
            std::uint64_t z = sm;
            z = (z ^ (z >> 30)) * 0xBF58476D1CE4E5B9ULL;
            z = (z ^ (z >> 27)) * 0x94D049BB133111EBULL;
            return z ^ (z >> 31);
        };
        for (auto& s : state_) s = splitmix64();
    }

    std::uint64_t next() {
        const std::uint64_t result = rotl(state_[0] + state_[3], 23) + state_[0];
        const std::uint64_t t = state_[1] << 17;

        state_[2] ^= state_[0];
        state_[3] ^= state_[1];
        state_[1] ^= state_[2];
        state_[0] ^= state_[3];
        state_[2] ^= t;
        state_[3] = rotl(state_[3], 45);

        return result;
    }

    // Uniform double in [0, 1).
    double nextUniform() {
        // Top 53 bits -> exact double mantissa precision.
        return static_cast<double>(next() >> 11) * (1.0 / 9007199254740992.0);
    }

private:
    static std::uint64_t rotl(std::uint64_t x, int k) {
        return (x << k) | (x >> (64 - k));
    }

    std::array<std::uint64_t, 4> state_{};
};

// Batches draws (default block 8192) to amortize call overhead, mirroring
// the Python _Pool's rationale, and to isolate the Box-Muller transform's
// two-values-per-call shape behind a one-value-per-call interface.
class RngPool {
public:
    enum class Kind { Normal, Uniform };

    RngPool(Xoshiro256PP& rng, Kind kind, std::size_t block = 8192)
        : rng_(rng), kind_(kind), block_(block) {}

    double next() {
        if (index_ >= buffer_.size()) {
            refill();
        }
        return buffer_[index_++];
    }

private:
    void refill() {
        buffer_.resize(block_);
        if (kind_ == Kind::Uniform) {
            for (auto& v : buffer_) v = rng_.nextUniform();
        } else {
            // Box-Muller, generated in pairs; block_ is always even-friendly
            // (8192), so no partial-pair edge case in practice.
            for (std::size_t i = 0; i + 1 < buffer_.size(); i += 2) {
                double u1 = rng_.nextUniform();
                double u2 = rng_.nextUniform();
                u1 = std::max(u1, 1e-300);  // guard log(0)
                const double mag = std::sqrt(-2.0 * std::log(u1));
                buffer_[i] = mag * std::cos(2.0 * kTwoPi * u2);
                buffer_[i + 1] = mag * std::sin(2.0 * kTwoPi * u2);
            }
            if (buffer_.size() % 2 != 0) {
                buffer_.back() = rng_.nextUniform();  // unreachable at block=8192
            }
        }
        index_ = 0;
    }

    Xoshiro256PP& rng_;
    Kind kind_;
    std::size_t block_;
    std::vector<double> buffer_;
    std::size_t index_ = 0;
};

} // namespace mimic::core::engine
