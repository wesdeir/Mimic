#include "GlobalHotkeys.h"

#include <atomic>

namespace mimic::app {

namespace {
int nextHotkeyId() {
    static std::atomic<int> counter{1};
    return counter.fetch_add(1, std::memory_order_relaxed);
}
} // namespace

GlobalHotkeys::GlobalHotkeys(HWND hwnd, UINT virtualKey, std::function<void()> onPressed)
    : hotkeyId_(nextHotkeyId()), hwnd_(hwnd), virtualKey_(virtualKey), onPressed_(std::move(onPressed)) {
    RegisterHotKey(hwnd_, hotkeyId_, 0, virtualKey_);
}

GlobalHotkeys::~GlobalHotkeys() { UnregisterHotKey(hwnd_, hotkeyId_); }

void GlobalHotkeys::handleHotkeyMessage(WPARAM hotkeyId) {
    if (static_cast<int>(hotkeyId) == hotkeyId_ && onPressed_) {
        onPressed_();
    }
}

void GlobalHotkeys::refresh() {
    UnregisterHotKey(hwnd_, hotkeyId_);
    RegisterHotKey(hwnd_, hotkeyId_, 0, virtualKey_);
}

} // namespace mimic::app
