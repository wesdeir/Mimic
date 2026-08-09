#include "MainPanel.h"

#include <imgui.h>

#include "config/ClickEnginePresets.h"
#include "config/RiskAssessor.h"

namespace mimic::gui {

namespace cfg = mimic::core::config;
using mimic::core::engine::EngineStats;

namespace {

ImVec4 hexToColor(const std::string& hex, float alpha = 1.0f) {
    unsigned int r = 0, g = 0, b = 0;
    if (hex.size() == 7 && hex[0] == '#') {
        sscanf_s(hex.c_str() + 1, "%02x%02x%02x", &r, &g, &b);
    }
    return ImVec4(r / 255.0f, g / 255.0f, b / 255.0f, alpha);
}

// Draws one keyboard-focusable row: a highlighted border when focused, plain
// text otherwise. Mouse clicks also focus+activate it, so nothing is lost
// for anyone who reaches for the mouse anyway.
bool focusableRow(const char* label, bool focused, bool* clicked) {
    ImVec4 bg = focused ? ImVec4(0.30f, 0.30f, 0.10f, 1.0f) : ImVec4(0.0f, 0.0f, 0.0f, 0.0f);
    ImGui::PushStyleColor(ImGuiCol_Header, bg);
    ImGui::PushStyleColor(ImGuiCol_HeaderHovered, bg);
    ImGui::PushStyleColor(ImGuiCol_HeaderActive, bg);
    bool wasClicked = ImGui::Selectable(label, focused, 0, ImVec2(0, 0));
    ImGui::PopStyleColor(3);
    if (clicked) *clicked = wasClicked;
    return wasClicked;
}

} // namespace

void MainPanel::handleKeyboardNav() {
    if (ImGui::IsKeyPressed(ImGuiKey_DownArrow)) {
        focusedIndex_ = (focusedIndex_ + 1) % kItemCount;
    }
    if (ImGui::IsKeyPressed(ImGuiKey_UpArrow)) {
        focusedIndex_ = (focusedIndex_ - 1 + kItemCount) % kItemCount;
    }
}

void MainPanel::draw() {
    handleKeyboardNav();

    const bool activate = ImGui::IsKeyPressed(ImGuiKey_Enter) || ImGui::IsKeyPressed(ImGuiKey_KeypadEnter);

    ImGuiIO& io = ImGui::GetIO();
    ImGui::SetNextWindowPos(ImVec2(0, 0));
    ImGui::SetNextWindowSize(io.DisplaySize);
    ImGui::Begin("Mimic", nullptr,
                  ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                      ImGuiWindowFlags_NoBringToFrontOnFocus);

    const bool enabled = controller_.isEnabled();
    const bool held = controller_.isPhysicallyHeld();
    ImGui::TextUnformatted("MIMIC");
    ImGui::SameLine();
    if (enabled && held) {
        ImGui::TextColored(ImVec4(0.30f, 0.69f, 0.31f, 1.0f), "[ CLICKING ]");
    } else if (enabled) {
        ImGui::TextColored(ImVec4(0.30f, 0.69f, 0.31f, 1.0f), "[ ENABLED ]");
    } else {
        ImGui::TextColored(ImVec4(0.55f, 0.55f, 0.55f, 1.0f), "[ DISABLED ]");
    }

    ImGui::TextDisabled("F4 toggle | Hold Left Click to attack | Up/Down + Enter to navigate");
    ImGui::Separator();

    const EngineStats stats = controller_.currentStats();
    if (stats.valid) {
        ImGui::Text("Current CPS:  %.1f", stats.currentCps);
        ImGui::Text("Total Clicks: %lld", static_cast<long long>(stats.total));

        auto assessment = cfg::RiskAssessor::assess(stats);
        ImGui::Text("Risk:");
        ImGui::SameLine();
        ImGui::TextColored(hexToColor(assessment.colorHex), "%s (%d)",
                            assessment.risk == cfg::RiskLevel::Low     ? "LOW"
                            : assessment.risk == cfg::RiskLevel::Medium ? "MEDIUM"
                                                                        : "HIGH",
                            assessment.score);
    } else {
        ImGui::TextDisabled("Waiting for clicks...");
        ImGui::Spacing();
        ImGui::Spacing();
    }

    ImGui::Separator();
    ImGui::Spacing();

    // Row 0: mode toggle.
    const bool enhanced = controller_.currentEnhancedMode();
    char modeLabel[64];
    std::snprintf(modeLabel, sizeof(modeLabel), "Mode: %s", enhanced ? "Enhanced" : "Standard");
    if (focusableRow(modeLabel, focusedIndex_ == 0, nullptr) || (activate && focusedIndex_ == 0)) {
        focusedIndex_ = 0;
        controller_.requestEnhancedMode(!enhanced);
    }

    ImGui::Spacing();
    ImGui::TextDisabled("Presets");

    // Rows 1-3: the built-in presets.
    const auto& presets = cfg::ClickEnginePresets::builtins();
    const std::string currentPreset = controller_.currentPresetName();
    for (std::size_t i = 0; i < presets.size(); ++i) {
        const int itemIndex = static_cast<int>(i) + 1;
        const auto& [name, config] = presets[i];
        const bool isCurrent = (name == currentPreset);

        char label[128];
        std::snprintf(label, sizeof(label), "%s%s", name.c_str(), isCurrent ? "  <- active" : "");
        if (focusableRow(label, focusedIndex_ == itemIndex, nullptr) ||
            (activate && focusedIndex_ == itemIndex)) {
            focusedIndex_ = itemIndex;
            controller_.requestPreset(name);
        }
        if (focusedIndex_ == itemIndex) {
            ImGui::TextDisabled("  %s", config.description.c_str());
        }
    }

    ImGui::End();
}

} // namespace mimic::gui
