#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <functional>

// Replaces the Python `keyboard` library's global F4 toggle
// (gui.py::setup_hotkeys) with RegisterHotKey/WM_HOTKEY -- works even when
// a game window has focus, not just Mimic's own window, matching the
// original's "toggle it in game" behavior.

namespace mimic::app {

class GlobalHotkeys {
public:
    // onToggle fires when F4 is pressed anywhere in the system. hwnd must be
    // the window whose message loop will receive WM_HOTKEY (forward it via
    // handleHotkeyMessage from that window's WndProc).
    GlobalHotkeys(HWND hwnd, std::function<void()> onToggle);
    ~GlobalHotkeys();

    GlobalHotkeys(const GlobalHotkeys&) = delete;
    GlobalHotkeys& operator=(const GlobalHotkeys&) = delete;

    // Call from WndProc on WM_HOTKEY; no-ops for any id it doesn't own.
    void handleHotkeyMessage(WPARAM hotkeyId);

private:
    static constexpr int kToggleHotkeyId = 1;

    HWND hwnd_;
    std::function<void()> onToggle_;
};

} // namespace mimic::app
