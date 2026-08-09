#include "GlobalHotkeys.h"

namespace mimic::app {

GlobalHotkeys::GlobalHotkeys(HWND hwnd, std::function<void()> onToggle)
    : hwnd_(hwnd), onToggle_(std::move(onToggle)) {
    RegisterHotKey(hwnd_, kToggleHotkeyId, 0, VK_F4);
}

GlobalHotkeys::~GlobalHotkeys() { UnregisterHotKey(hwnd_, kToggleHotkeyId); }

void GlobalHotkeys::handleHotkeyMessage(WPARAM hotkeyId) {
    if (static_cast<int>(hotkeyId) == kToggleHotkeyId && onToggle_) {
        onToggle_();
    }
}

} // namespace mimic::app
