#pragma once

#include <mutex>

#include "engine/EngineStats.h"

// Mutex-guarded copy of EngineStats, not per-field atomics: EngineStats is a
// ~15-field aggregate that must be read/written as one consistent unit, or
// a reader can see e.g. avg_cps computed from a mean the writer already
// updated but n hasn't caught up to yet -- exactly the "atomics compose
// badly across related fields" trap. The click thread publishes after every
// click(); the UI thread reads a cheap copy, never touching the engine
// itself (see AdaptiveClickerEngine's single-writer-thread contract).

namespace mimic::app {

class StatsSnapshot {
public:
    void publish(const mimic::core::engine::EngineStats& stats) {
        std::lock_guard<std::mutex> lock(mutex_);
        stats_ = stats;
    }

    mimic::core::engine::EngineStats read() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return stats_;
    }

private:
    mutable std::mutex mutex_;
    mimic::core::engine::EngineStats stats_;
};

} // namespace mimic::app
