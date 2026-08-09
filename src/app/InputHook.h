#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <atomic>

// Drives the "hold left click to auto-click" activation (README: "Hold LEFT
// CLICK to auto-click, Release to stop"). A single WH_MOUSE_LL hook,
// distinguishing the user's real presses from Mimic's own synthetic
// SendInput clicks via MSLLHOOKSTRUCT::flags & LLMHF_INJECTED -- this is
// the port-plan's recommended unification of what the Python original did
// with two separate mechanisms (pynput's `injected` check for hold
// detection, a second raw hook in session.py for recording).
//
// Must be constructed on the thread that pumps the app's Win32 message
// loop -- WH_MOUSE_LL callbacks only fire on that thread.

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

    static InputHook* s_active;
};

} // namespace mimic::app
