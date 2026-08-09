#pragma once

#include "AppController.h"

// The entire v1 GUI: one compact "hacked client" style panel. Per the
// user's explicit scope cut (2026-08-09): clicker on/off status, a few live
// stats, and the 3 built-in presets -- nothing else for now. Analytics/
// Graphs/History/Compare/Training are deferred, not deleted; their C++
// core (RiskAssessor, SessionManager, HumanClickTracker) already exists and
// is tested, just not wired to a screen yet.
//
// Keyboard model: Up/Down moves focus across a small vertical list (mode
// toggle, then the 3 presets); Enter activates the focused row; Backspace
// is reserved (no-op) until a second screen exists to go back from.

namespace mimic::gui {

class MainPanel {
public:
    explicit MainPanel(mimic::app::AppController& controller) : controller_(controller) {}

    // Called once per frame, after ImGui::NewFrame(). Reads keyboard state
    // itself (arrows/Enter) rather than relying on ImGui's built-in nav, per
    // the port plan's custom focus-grid model.
    void draw();

private:
    void handleKeyboardNav();

    mimic::app::AppController& controller_;
    int focusedIndex_ = 0;  // 0 = mode toggle, 1..3 = presets
    static constexpr int kItemCount = 4;
};

} // namespace mimic::gui
