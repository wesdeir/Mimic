#pragma once

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <atomic>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <thread>

#include "GlobalHotkeys.h"
#include "InputHook.h"
#include "StatsSnapshot.h"
#include "engine/AdaptiveClickerEngine.h"

// Owns the one AdaptiveClickerEngine instance and the single dedicated click
// thread that is allowed to touch it (see the engine's own threading
// contract). The UI thread never calls into the engine directly -- it reads
// StatsSnapshot and requests config changes via setPreset()/setEnhancedMode()/
// setEnabled(), which are queued and applied by the click thread itself.

namespace mimic::app {

class AppController {
public:
    // hwnd must already exist (needed by GlobalHotkeys/RegisterHotKey) and
    // this constructor must run on the thread pumping the app's Win32
    // message loop (needed by GlobalHotkeys' WM_HOTKEY delivery). InputHook
    // installs its WH_MOUSE_LL hook on its own dedicated thread and has no
    // such requirement -- see InputHook.h.
    explicit AppController(HWND hwnd);
    ~AppController();

    AppController(const AppController&) = delete;
    AppController& operator=(const AppController&) = delete;

    void handleHotkeyMessage(WPARAM hotkeyId) { hotkeys_.handleHotkeyMessage(hotkeyId); }
    void refreshHotkey() { hotkeys_.refresh(); }

    bool isEnabled() const { return enabled_.load(std::memory_order_relaxed); }
    void setEnabled(bool enabled) { enabled_.store(enabled, std::memory_order_relaxed); }
    void toggleEnabled() { enabled_.store(!isEnabled(), std::memory_order_relaxed); }

    bool isPhysicallyHeld() const { return inputHook_.isLeftButtonPhysicallyHeld(); }

    // Queued: applied by the click thread on its next loop iteration, never
    // touches the engine from the calling (UI) thread.
    void requestPreset(const std::string& presetName);
    void requestEnhancedMode(bool enabled);

    std::string currentPresetName() const;
    bool currentEnhancedMode() const { return enhancedModeDisplay_.load(std::memory_order_relaxed); }
    mimic::core::engine::EngineStats currentStats() const { return statsSnapshot_.read(); }

private:
    void clickThreadMain();
    void applyPendingConfig();  // click-thread-only

    mimic::core::engine::AdaptiveClickerEngine engine_;
    mutable std::mutex presetNameMutex_;
    std::string presetName_;
    std::atomic<bool> enhancedModeDisplay_{true};  // click-thread-written, UI-thread-read; single bool, safe as a relaxed atomic

    InputHook inputHook_;
    GlobalHotkeys hotkeys_;
    StatsSnapshot statsSnapshot_;

    std::atomic<bool> enabled_{false};
    std::atomic<bool> running_{true};

    std::mutex pendingMutex_;
    std::optional<std::string> pendingPreset_;
    std::optional<bool> pendingEnhancedMode_;

    std::thread clickThread_;
};

} // namespace mimic::app
