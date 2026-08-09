#include "SyntheticClick.h"

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

namespace mimic::core::mouse {

namespace {

void sendMouseEvent(DWORD flags) {
    INPUT input{};
    input.type = INPUT_MOUSE;
    input.mi.dwFlags = flags;
    SendInput(1, &input, sizeof(INPUT));
}

} // namespace

void leftButtonDown() { sendMouseEvent(MOUSEEVENTF_LEFTDOWN); }
void leftButtonUp() { sendMouseEvent(MOUSEEVENTF_LEFTUP); }

} // namespace mimic::core::mouse
