#include "AppController.h"

#include <chrono>

namespace mimic::app {

using namespace std::chrono_literals;

AppController::AppController(HWND hwnd)
    : engine_(/*enhancedMode=*/true, /*presetName=*/"Balanced"),
      presetName_("Balanced"),
      hotkeys_(hwnd, VK_F4, [this] { toggleEnabled(); }) {
    clickThread_ = std::thread(&AppController::clickThreadMain, this);
}

AppController::~AppController() {
    running_.store(false, std::memory_order_relaxed);
    if (clickThread_.joinable()) {
        clickThread_.join();
    }
}

void AppController::requestPreset(const std::string& presetName) {
    std::lock_guard<std::mutex> lock(pendingMutex_);
    pendingPreset_ = presetName;
}

void AppController::requestEnhancedMode(bool enabled) {
    std::lock_guard<std::mutex> lock(pendingMutex_);
    pendingEnhancedMode_ = enabled;
}

std::string AppController::currentPresetName() const {
    std::lock_guard<std::mutex> lock(presetNameMutex_);
    return presetName_;
}

void AppController::applyPendingConfig() {
    std::optional<std::string> preset;
    std::optional<bool> enhanced;
    {
        std::lock_guard<std::mutex> lock(pendingMutex_);
        preset.swap(pendingPreset_);
        enhanced.swap(pendingEnhancedMode_);
    }
    if (preset) {
        engine_.setPreset(*preset);
        std::lock_guard<std::mutex> lock(presetNameMutex_);
        presetName_ = *preset;
    }
    if (enhanced) {
        engine_.setEnhancedMode(*enhanced);
        enhancedModeDisplay_.store(*enhanced, std::memory_order_relaxed);
    }
}

void AppController::clickThreadMain() {
    while (running_.load(std::memory_order_relaxed)) {
        applyPendingConfig();

        const bool shouldClick = isEnabled() && inputHook_.isLeftButtonPhysicallyHeld();
        if (shouldClick) {
            if (!engine_.isActivelyClicking()) {
                engine_.startClicking();
            }
            engine_.click();  // blocking: sleeps out the drawn interval itself
        } else {
            if (engine_.isActivelyClicking()) {
                engine_.stopClicking();
            }
            std::this_thread::sleep_for(10ms);  // idle poll rate while not clicking
        }

        statsSnapshot_.publish(engine_.getDetailedStats());
    }
}

} // namespace mimic::app
