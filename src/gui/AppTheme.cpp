#include "AppTheme.h"

#include <imgui.h>

namespace mimic::gui {

ImFont* AppTheme::loadFont(ImGuiIO& io) {
    // TEMPORARY (Phase 0 scaffolding): Consolas ships with every Windows
    // install, so it unblocks "one monospace font, nothing else in the atlas"
    // without a licensing decision yet. Per the port plan (risk #5), this
    // should be replaced with a bundled OFL-licensed font (JetBrains Mono or
    // Cascadia Mono) before Phase 6 ships, with its license file included.
    ImFontConfig cfg;
    cfg.SizePixels = 16.0f;
    ImFont* font = io.Fonts->AddFontFromFileTTF(
        "C:\\Windows\\Fonts\\consola.ttf", 16.0f, &cfg);

    // AddFontDefault() is deliberately never called: the atlas must contain
    // only this one font so no screen can end up non-monospace by accident.
    if (!font) {
        font = io.Fonts->AddFontDefault();
    }
    return font;
}

void AppTheme::applyDarkPalette(ImGuiStyle& style) {
    ImGui::StyleColorsDark(&style);

    // Ported from mimic/gui.py's "Ghost Stealth" palette (self.bgcolor,
    // self.panel_color, self.accent_color, self.secondary_color,
    // self.tech_accent) so the new GUI keeps the same visual identity.
    ImVec4* colors = style.Colors;
    const ImVec4 bg        = ImVec4(0x0D / 255.0f, 0x0D / 255.0f, 0x0D / 255.0f, 1.00f);
    const ImVec4 panel     = ImVec4(0x1E / 255.0f, 0x1E / 255.0f, 0x1E / 255.0f, 1.00f);
    const ImVec4 accent    = ImVec4(0x4C / 255.0f, 0xAF / 255.0f, 0x50 / 255.0f, 1.00f);
    const ImVec4 accentHov = ImVec4(0x5D / 255.0f, 0xC7 / 255.0f, 0x61 / 255.0f, 1.00f);
    const ImVec4 accentAct = ImVec4(0x3D / 255.0f, 0x8B / 255.0f, 0x40 / 255.0f, 1.00f);
    const ImVec4 techAccent= ImVec4(0x00 / 255.0f, 0xE5 / 255.0f, 0xFF / 255.0f, 1.00f);

    colors[ImGuiCol_WindowBg]        = bg;
    colors[ImGuiCol_ChildBg]         = panel;
    colors[ImGuiCol_PopupBg]         = panel;
    colors[ImGuiCol_Border]          = ImVec4(0.20f, 0.20f, 0.20f, 1.00f);
    colors[ImGuiCol_FrameBg]         = panel;
    colors[ImGuiCol_Button]          = accent;
    colors[ImGuiCol_ButtonHovered]   = accentHov;
    colors[ImGuiCol_ButtonActive]    = accentAct;
    colors[ImGuiCol_Header]          = accent;
    colors[ImGuiCol_HeaderHovered]   = accentHov;
    colors[ImGuiCol_HeaderActive]    = accentAct;
    colors[ImGuiCol_CheckMark]       = accent;
    colors[ImGuiCol_SliderGrab]      = accent;
    colors[ImGuiCol_SliderGrabActive]= accentAct;
    colors[ImGuiCol_PlotLines]       = accent;
    colors[ImGuiCol_PlotHistogram]   = techAccent;
    colors[ImGuiCol_Text]            = ImVec4(0.92f, 0.92f, 0.92f, 1.00f);

    // Sharp corners read closer to a terminal/monospace aesthetic than
    // ImGui's default rounded look; larger frame padding gives keyboard
    // focus outlines more room to be clearly visible.
    style.WindowRounding = 0.0f;
    style.FrameRounding  = 0.0f;
    style.FramePadding   = ImVec2(8.0f, 6.0f);
    style.ItemSpacing    = ImVec2(10.0f, 8.0f);
}

} // namespace mimic::gui
