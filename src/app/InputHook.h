#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <atomic>
#include <thread>

// Drives the "hold left click to auto-click" activation (README: "Hold LEFT
// CLICK to auto-click, Release to stop"). A single WH_MOUSE_LL hook,
// distinguishing the user's real presses from Mimic's own synthetic
// SendInput clicks via MSLLHOOKSTRUCT::flags & LLMHF_INJECTED -- this is
// the port-plan's recommended unification of what the Python original did
// with two separate mechanisms (pynput's `injected` check for hold
// detection, a second raw hook in session.py for recording).
//
// Owns a dedicated thread that does nothing but install the hook and pump
// its message queue. WH_MOUSE_LL callbacks run synchronously and
// system-wide on whichever thread installed the hook, so sharing that
// thread with the GUI's render loop meant every mouse event on the whole
// machine stalled behind main.cpp's occlusion-poll Sleep(10) whenever
// another app took the display (e.g. a fullscreened game) -- real, global
// mouse input lag, found via playtesting. A thread with no Present()/
// Sleep() of its own keeps the hook responsive no matter what the render
// loop is doing.

namespace mimic::app {

class InputHook {
public:
    InputHook();
    ~InputHook();

    InputHook(const InputHook&) = delete;
    InputHook& operator=(const InputHook&) = delete;

    bool isLeftButtonPhysicallyHeld() const { return held_.load(std::memory_order_relaxed); }

private:
    static LRESULT CALLBACK hookProc(int nCode, WPARAM wParam, LPARAM lParam);

    HHOOK hook_ = nullptr;
    std::atomic<bool> held_{false};

    // Set inside the hook thread before it signals ready; safe to read
    // from the constructing thread afterward (the ready-event wait below
    // is the synchronizing acquire/release pair), and only ever touched
    // by the hook thread itself thereafter (PostThreadMessageW targets it
    // by value, not through a data race).
    std::thread thread_;
    DWORD threadId_ = 0;

    static InputHook* s_active;
};

} // namespace mimic::app
