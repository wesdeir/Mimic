#pragma once

#include "AppController.h"

// The entire v1 GUI: one compact "hacked client" style panel. Per the
// user's explicit scope cut (2026-08-09): clicker on/off status, a few live
// stats, and the 3 built-in presets -- nothing else for now. Analytics/
// Graphs/History/Compare/Training are deferred, not built; RiskAssessor is
// the one piece of that deferred core already wired in (the live risk
// indicator).
//
// Keyboard model: Up/Down moves focus across a small vertical list (mode
// toggle, then the 3 presets); Enter activates the focused row. Backspace
// requests hiding the panel, but only fires while Mimic's own window has
// focus (see consumeHideRequest()) -- the global, works-while-the-game-has-
// focus version of "hide the panel" is the separate Insert hotkey in
// main.cpp, which doesn't go through this class at all.

namespace mimic::gui {

class MainPanel {
public:
    explicit MainPanel(mimic::app::AppController& controller) : controller_(controller) {}

    // Called once per frame, after ImGui::NewFrame(). Reads keyboard state
    // itself (arrows/Enter) rather than relying on ImGui's built-in nav, per
    // the port plan's custom focus-grid model.
    void draw();

    // True at most once per Backspace press (edge-triggered, like the
    // Enter/activate check in draw()). main.cpp polls this after draw() and
    // acts on it by hiding the actual Win32 window -- this class has no
    // window-visibility concept of its own.
    bool consumeHideRequest();

private:
    void handleKeyboardNav();

    mimic::app::AppController& controller_;
    int focusedIndex_ = 0;  // 0 = mode toggle, 1..3 = presets
    static constexpr int kItemCount = 4;
    bool hideRequested_ = false;
};

} // namespace mimic::gui
