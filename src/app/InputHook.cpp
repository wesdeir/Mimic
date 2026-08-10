#include "InputHook.h"

namespace mimic::app {

InputHook* InputHook::s_active = nullptr;

InputHook::InputHook() {
    s_active = this;

    // Manual-reset, initially unsignaled: the constructor blocks on it so
    // isLeftButtonPhysicallyHeld() is reliable the moment InputHook exists,
    // same as before this was split onto its own thread.
    HANDLE readyEvent = CreateEventW(nullptr, TRUE, FALSE, nullptr);
    thread_ = std::thread([this, readyEvent] {
        threadId_ = GetCurrentThreadId();
        hook_ = SetWindowsHookExW(WH_MOUSE_LL, &InputHook::hookProc, GetModuleHandleW(nullptr), 0);
        SetEvent(readyEvent);

        // Nothing but message pumping happens on this thread, ever --
        // that's the whole point: the hook stays serviced immediately no
        // matter what the GUI thread is doing (rendering, occluded,
        // sleeping).
        MSG msg;
        while (GetMessageW(&msg, nullptr, 0, 0) > 0) {
            TranslateMessage(&msg);
            DispatchMessageW(&msg);
        }

        if (hook_) {
            UnhookWindowsHookEx(hook_);
            hook_ = nullptr;
        }
    });

    WaitForSingleObject(readyEvent, INFINITE);
    CloseHandle(readyEvent);
}

InputHook::~InputHook() {
    if (thread_.joinable()) {
        PostThreadMessageW(threadId_, WM_QUIT, 0, 0);
        thread_.join();
    }
    if (s_active == this) {
        s_active = nullptr;
    }
}

LRESULT CALLBACK InputHook::hookProc(int nCode, WPARAM wParam, LPARAM lParam) {
    if (nCode >= 0 && s_active) {
        const auto* info = reinterpret_cast<const MSLLHOOKSTRUCT*>(lParam);
        const bool injected = (info->flags & LLMHF_INJECTED) != 0;

        // Only real presses drive hold detection -- Mimic's own synthetic
        // clicks (injected) must never be mistaken for the user releasing
        // or re-pressing the physical button.
        if (!injected) {
            if (wParam == WM_LBUTTONDOWN) {
                s_active->held_.store(true, std::memory_order_relaxed);
            } else if (wParam == WM_LBUTTONUP) {
                s_active->held_.store(false, std::memory_order_relaxed);
            }
        }
    }

    HHOOK handle = s_active ? s_active->hook_ : nullptr;
    return CallNextHookEx(handle, nCode, wParam, lParam);
}

} // namespace mimic::app
