// Entry point for the v1 "hacked client" style GUI: one compact panel
// (MainPanel) driven by AppController, which owns the click thread, the
// physical-hold input hook, and the F4 global toggle. Window/DX11
// boilerplate follows Dear ImGui's standard examples/example_win32_directx11
// layout.

#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <d3d11.h>
#include <tchar.h>

#include <imgui.h>
#include <imgui_impl_dx11.h>
#include <imgui_impl_win32.h>

#include "AppController.h"
#include "app_info.h"
#include "AppTheme.h"
#include "GlobalHotkeys.h"
#include "MainPanel.h"

extern IMGUI_IMPL_API LRESULT ImGui_ImplWin32_WndProcHandler(
    HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam);

namespace {

ID3D11Device* g_pd3dDevice = nullptr;
ID3D11DeviceContext* g_pd3dDeviceContext = nullptr;
IDXGISwapChain* g_pSwapChain = nullptr;
bool g_SwapChainOccluded = false;
UINT g_ResizeWidth = 0, g_ResizeHeight = 0;
ID3D11RenderTargetView* g_mainRenderTargetView = nullptr;
mimic::app::AppController* g_controller = nullptr;
mimic::app::GlobalHotkeys* g_visibilityHotkey = nullptr;
bool g_panelVisible = true;

// Insert (global) and Backspace (local, see MainPanel::consumeHideRequest)
// both funnel through here so there's exactly one place that actually
// touches window visibility.
//
// KNOWN OPEN ISSUE (found via automated testing, unconfirmed with real
// hardware input): hiding the window via ShowWindow(SW_HIDE) while it holds
// focus, specifically when that focus was granted via an external process's
// SetForegroundWindow() call, was observed to permanently stop delivering
// WM_HOTKEY for the rest of the process's life -- re-registering the hotkey
// (GlobalHotkeys::refresh(), called below) did not fix it. Every attempt to
// reproduce this with realistic input (the window's natural launch focus, a
// simulated mouse click) failed to reproduce it, so this may be a testing-
// harness artifact rather than a real bug -- SetForegroundWindow from an
// unrelated process is a different code path than how a real user's click/
// Alt-Tab grants focus. Needs a real hands-on-keyboard check.
void SetPanelVisible(HWND hwnd, bool visible) {
    ::ShowWindow(hwnd, visible ? SW_SHOW : SW_HIDE);
    g_panelVisible = visible;

    // Defensive (see GlobalHotkeys::refresh()): re-arm both hotkeys after
    // every visibility change so a dropped registration can't leave the
    // panel permanently stuck.
    if (g_visibilityHotkey) g_visibilityHotkey->refresh();
    if (g_controller) g_controller->refreshHotkey();
}

void CreateRenderTarget() {
    ID3D11Texture2D* pBackBuffer = nullptr;
    g_pSwapChain->GetBuffer(0, IID_PPV_ARGS(&pBackBuffer));
    if (pBackBuffer) {
        g_pd3dDevice->CreateRenderTargetView(pBackBuffer, nullptr, &g_mainRenderTargetView);
        pBackBuffer->Release();
    }
}

void CleanupRenderTarget() {
    if (g_mainRenderTargetView) {
        g_mainRenderTargetView->Release();
        g_mainRenderTargetView = nullptr;
    }
}

bool CreateDeviceD3D(HWND hWnd) {
    DXGI_SWAP_CHAIN_DESC sd = {};
    sd.BufferCount = 2;
    sd.BufferDesc.Width = 0;
    sd.BufferDesc.Height = 0;
    sd.BufferDesc.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    sd.BufferDesc.RefreshRate.Numerator = 60;
    sd.BufferDesc.RefreshRate.Denominator = 1;
    sd.Flags = DXGI_SWAP_CHAIN_FLAG_ALLOW_MODE_SWITCH;
    sd.BufferUsage = DXGI_USAGE_RENDER_TARGET_OUTPUT;
    sd.OutputWindow = hWnd;
    sd.SampleDesc.Count = 1;
    sd.SampleDesc.Quality = 0;
    sd.Windowed = TRUE;
    sd.SwapEffect = DXGI_SWAP_EFFECT_DISCARD;

    UINT createDeviceFlags = 0;
    D3D_FEATURE_LEVEL featureLevel;
    const D3D_FEATURE_LEVEL featureLevelArray[2] = {D3D_FEATURE_LEVEL_11_0, D3D_FEATURE_LEVEL_10_0};
    HRESULT res = D3D11CreateDeviceAndSwapChain(
        nullptr, D3D_DRIVER_TYPE_HARDWARE, nullptr, createDeviceFlags, featureLevelArray, 2,
        D3D11_SDK_VERSION, &sd, &g_pSwapChain, &g_pd3dDevice, &featureLevel, &g_pd3dDeviceContext);
    if (res == DXGI_ERROR_UNSUPPORTED) {
        res = D3D11CreateDeviceAndSwapChain(
            nullptr, D3D_DRIVER_TYPE_WARP, nullptr, createDeviceFlags, featureLevelArray, 2,
            D3D11_SDK_VERSION, &sd, &g_pSwapChain, &g_pd3dDevice, &featureLevel, &g_pd3dDeviceContext);
    }
    if (res != S_OK) {
        return false;
    }

    CreateRenderTarget();
    return true;
}

void CleanupDeviceD3D() {
    CleanupRenderTarget();
    if (g_pSwapChain) {
        g_pSwapChain->Release();
        g_pSwapChain = nullptr;
    }
    if (g_pd3dDeviceContext) {
        g_pd3dDeviceContext->Release();
        g_pd3dDeviceContext = nullptr;
    }
    if (g_pd3dDevice) {
        g_pd3dDevice->Release();
        g_pd3dDevice = nullptr;
    }
}

LRESULT WINAPI WndProc(HWND hWnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    if (ImGui_ImplWin32_WndProcHandler(hWnd, msg, wParam, lParam)) {
        return true;
    }

    switch (msg) {
        case WM_SIZE:
            if (wParam != SIZE_MINIMIZED) {
                g_ResizeWidth = static_cast<UINT>(LOWORD(lParam));
                g_ResizeHeight = static_cast<UINT>(HIWORD(lParam));
            }
            return 0;
        case WM_SYSCOMMAND:
            if ((wParam & 0xfff0) == SC_KEYMENU) {
                return 0; // Disable ALT application menu
            }
            break;
        case WM_HOTKEY:
            if (g_controller) {
                g_controller->handleHotkeyMessage(wParam);
            }
            if (g_visibilityHotkey) {
                g_visibilityHotkey->handleHotkeyMessage(wParam);
            }
            return 0;
        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
        default:
            break;
    }
    return DefWindowProc(hWnd, msg, wParam, lParam);
}

} // namespace

int APIENTRY WinMain(HINSTANCE, HINSTANCE, LPSTR, int) {
    WNDCLASSEXW wc = {
        sizeof(wc),        CS_CLASSDC, WndProc, 0L,    0L,
        GetModuleHandle(nullptr), nullptr,     nullptr, nullptr, nullptr,
        L"MimicWindowClass", nullptr};
    ::RegisterClassExW(&wc);
    HWND hwnd = ::CreateWindowW(
        wc.lpszClassName, L"Mimic", WS_OVERLAPPEDWINDOW, 100, 100, 560, 420,
        nullptr, nullptr, wc.hInstance, nullptr);

    if (!CreateDeviceD3D(hwnd)) {
        CleanupDeviceD3D();
        ::UnregisterClassW(wc.lpszClassName, wc.hInstance);
        return 1;
    }

    ::ShowWindow(hwnd, SW_SHOWDEFAULT);
    ::UpdateWindow(hwnd);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO& io = ImGui::GetIO();
    // Deliberately NOT setting ImGuiConfigFlags_NavEnableKeyboard: MainPanel
    // implements its own arrow/Enter focus model by reading key state
    // directly (see FocusGrid-style handling in MainPanel::draw()). Enabling
    // ImGui's built-in keyboard nav here made both systems respond to the
    // same arrow presses independently, producing two different, desynced
    // highlighted rows (ImGui's own nav rectangle plus this app's highlight)
    // -- found via playtesting.

    mimic::gui::AppTheme::applyDarkPalette(ImGui::GetStyle());
    mimic::gui::AppTheme::loadFont(io);

    ImGui_ImplWin32_Init(hwnd);
    ImGui_ImplDX11_Init(g_pd3dDevice, g_pd3dDeviceContext);

    // Constructed after the window exists (GlobalHotkeys needs the HWND) and
    // on this thread specifically (InputHook's WH_MOUSE_LL hook and
    // GlobalHotkeys' WM_HOTKEY both require the installing thread to pump
    // messages, which is exactly what this loop below does).
    mimic::app::AppController controller(hwnd);
    g_controller = &controller;
    mimic::gui::MainPanel mainPanel(controller);

    // Global Insert toggle: works while the game (or anything else) has
    // focus, unlike MainPanel's local Backspace hide (see GlobalHotkeys.h
    // for why Backspace itself can't safely be global).
    mimic::app::GlobalHotkeys visibilityHotkey(hwnd, VK_INSERT,
                                                [hwnd] { SetPanelVisible(hwnd, !g_panelVisible); });
    g_visibilityHotkey = &visibilityHotkey;

    bool done = false;
    while (!done) {
        MSG msg;
        while (::PeekMessage(&msg, nullptr, 0U, 0U, PM_REMOVE)) {
            ::TranslateMessage(&msg);
            ::DispatchMessage(&msg);
            if (msg.message == WM_QUIT) {
                done = true;
            }
        }
        if (done) {
            break;
        }

        // Skip the frame entirely while hidden -- no point spending
        // GPU/CPU time drawing something nobody can see, and this is
        // meant to sit hidden during most of an actual play session.
        // Messages (so hotkeys still work) are still pumped above.
        if (!g_panelVisible) {
            ::Sleep(10);
            continue;
        }

        if (g_SwapChainOccluded && g_pSwapChain->Present(0, DXGI_PRESENT_TEST) == DXGI_STATUS_OCCLUDED) {
            ::Sleep(10);
            continue;
        }
        g_SwapChainOccluded = false;

        if (g_ResizeWidth != 0 && g_ResizeHeight != 0) {
            CleanupRenderTarget();
            g_pSwapChain->ResizeBuffers(0, g_ResizeWidth, g_ResizeHeight, DXGI_FORMAT_UNKNOWN, 0);
            g_ResizeWidth = g_ResizeHeight = 0;
            CreateRenderTarget();
        }

        ImGui_ImplDX11_NewFrame();
        ImGui_ImplWin32_NewFrame();
        ImGui::NewFrame();

        mainPanel.draw();
        if (mainPanel.consumeHideRequest()) {
            SetPanelVisible(hwnd, false);
        }

        ImGui::Render();
        const float clearColor[4] = {0.05f, 0.05f, 0.05f, 1.00f};
        g_pd3dDeviceContext->OMSetRenderTargets(1, &g_mainRenderTargetView, nullptr);
        g_pd3dDeviceContext->ClearRenderTargetView(g_mainRenderTargetView, clearColor);
        ImGui_ImplDX11_RenderDrawData(ImGui::GetDrawData());

        HRESULT hr = g_pSwapChain->Present(1, 0);
        g_SwapChainOccluded = (hr == DXGI_STATUS_OCCLUDED);
    }

    ImGui_ImplDX11_Shutdown();
    ImGui_ImplWin32_Shutdown();
    ImGui::DestroyContext();

    CleanupDeviceD3D();
    ::DestroyWindow(hwnd);
    ::UnregisterClassW(wc.lpszClassName, wc.hInstance);

    return 0;
}
