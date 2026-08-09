#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <functional>

// Replaces the Python `keyboard` library's global hotkeys
// (gui.py::setup_hotkeys) with RegisterHotKey/WM_HOTKEY -- works even when
// a game window has focus, not just Mimic's own window. Generic over the
// virtual-key code so it can back both the F4 click-enable toggle
// (AppController) and the Insert panel-visibility toggle (main.cpp).

namespace mimic::app {

class GlobalHotkeys {
public:
    // onPressed fires when virtualKey is pressed anywhere in the system.
    // hwnd must be the window whose message loop will receive WM_HOTKEY
    // (forward it via handleHotkeyMessage from that window's WndProc).
    GlobalHotkeys(HWND hwnd, UINT virtualKey, std::function<void()> onPressed);
    ~GlobalHotkeys();

    GlobalHotkeys(const GlobalHotkeys&) = delete;
    GlobalHotkeys& operator=(const GlobalHotkeys&) = delete;

    // Call from WndProc on WM_HOTKEY; no-ops for any id it doesn't own, so
    // it's safe to call on every registered GlobalHotkeys instance.
    void handleHotkeyMessage(WPARAM hotkeyId);

    // Re-issues Unregister+RegisterHotKey with the same id/key. Defensive:
    // playtesting turned up one case (via simulated input toggling the
    // owning window's visibility) where the registration seemed to stop
    // delivering WM_HOTKEY afterward; cheap to call after any visibility
    // change regardless of whether that turns out to be a real-world issue
    // or a test-harness artifact.
    void refresh();

private:
    int hotkeyId_;
    HWND hwnd_;
    UINT virtualKey_;
    std::function<void()> onPressed_;
};

} // namespace mimic::app
