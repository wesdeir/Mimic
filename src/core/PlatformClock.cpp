#include "PlatformClock.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

namespace mimic::core {

namespace {

double qpcFrequency() {
    static const double freq = [] {
        LARGE_INTEGER f;
        QueryPerformanceFrequency(&f);
        return static_cast<double>(f.QuadPart);
    }();
    return freq;
}

// Sleeps for at most durationSeconds using a high-resolution waitable timer
// (the real analogue of what CPython 3.11+ does internally on Windows),
// falling back to Sleep() if the high-res timer can't be created (pre-1809
// systems).
void coarseSleep(double durationSeconds) {
    if (durationSeconds <= 0.0) return;

    static HANDLE timer = CreateWaitableTimerExW(
        nullptr, nullptr, CREATE_WAITABLE_TIMER_HIGH_RESOLUTION, TIMER_ALL_ACCESS);

    if (timer) {
        LARGE_INTEGER due;
        due.QuadPart = -static_cast<LONGLONG>(durationSeconds * 1e7);  // 100ns units, negative = relative
        SetWaitableTimer(timer, &due, 0, nullptr, nullptr, FALSE);
        WaitForSingleObject(timer, INFINITE);
    } else {
        Sleep(static_cast<DWORD>(durationSeconds * 1000.0));
    }
}

} // namespace

double PlatformClock::nowSeconds() {
    LARGE_INTEGER counter;
    QueryPerformanceCounter(&counter);
    return static_cast<double>(counter.QuadPart) / qpcFrequency();
}

void PlatformClock::preciseSleep(double durationSeconds) {
    if (durationSeconds <= 0.0) return;

    const double deadline = nowSeconds() + durationSeconds;
    const double coarse = durationSeconds - 0.0015;  // leave 1.5ms to spin
    if (coarse > 0.0) {
        coarseSleep(coarse);
    }
    while (nowSeconds() < deadline) {
        // spin
    }
}

} // namespace mimic::core
