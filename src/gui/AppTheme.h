#pragma once

struct ImGuiIO;
struct ImGuiStyle;
struct ImFont;

namespace mimic::gui {

// Loads the single monospace font used everywhere in the app (no other font
// is ever added to the atlas, so nothing can accidentally end up proportional)
// and applies the dark "Ghost Stealth" palette carried over from the Tkinter
// GUI's bgcolor/panel_color/accent_color scheme.
class AppTheme {
public:
    static ImFont* loadFont(ImGuiIO& io);
    static void applyDarkPalette(ImGuiStyle& style);
};

} // namespace mimic::gui
