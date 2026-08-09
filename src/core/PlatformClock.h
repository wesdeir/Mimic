#pragma once

// Ported from mimic/engine.py::AdaptiveClickerEngine.precise_sleep. Python
// 3.11+ backs time.sleep() with a high-resolution waitable timer on Windows;
// std::this_thread::sleep_for has NO such guarantee (Sleep()'s default
// ~15.6ms timer granularity), so this ports the underlying mechanism
// directly rather than assuming sleep_for is equivalent (port-plan risk #1).

namespace mimic::core {

class PlatformClock {
public:
    // Monotonic clock in seconds, backed by QueryPerformanceCounter.
    static double nowSeconds();

    // Sleeps for duration_seconds with sub-millisecond accuracy: coarse-sleeps
    // via a high-resolution waitable timer to within ~1.5ms of the deadline,
    // then spins the remainder on nowSeconds(). No-ops for duration <= 0.
    static void preciseSleep(double durationSeconds);
};

} // namespace mimic::core
