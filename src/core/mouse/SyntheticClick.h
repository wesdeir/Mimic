#pragma once

// Replaces mimic/engine.py's win32api.mouse_event(MOUSEEVENTF_LEFTDOWN/UP,
// ...) calls with SendInput, the modern equivalent (mouse_event is a legacy
// API). Functionally equivalent for this use case (port-plan risk #4).

namespace mimic::core::mouse {

void leftButtonDown();
void leftButtonUp();

} // namespace mimic::core::mouse
