#include "PresetManager.h"

#include <filesystem>
#include <fstream>
#include <iostream>

#include <nlohmann/json.hpp>

#include "Config.h"

namespace mimic::core::config {

namespace fs = std::filesystem;

namespace {

fs::path toFsPath(const std::wstring& wide) { return fs::path(wide); }

} // namespace

void PresetManager::migrateLegacyFileIfNeeded() {
    const fs::path legacy = toFsPath(presetsFileLegacyPath());
    const fs::path current = toFsPath(presetsFilePath());
    if (fs::exists(legacy) && !fs::exists(current)) {
        std::error_code ec;
        fs::create_directories(current.parent_path(), ec);
        fs::copy_file(legacy, current, ec);
        if (ec) {
            std::cerr << "[WARNING] Could not migrate legacy presets file: " << ec.message() << "\n";
        }
    }
}

std::vector<std::pair<std::string, PresetConfig>> PresetManager::loadCustom() {
    std::vector<std::pair<std::string, PresetConfig>> result;
    const fs::path path = toFsPath(presetsFilePath());
    if (!fs::exists(path)) {
        return result;
    }
    try {
        std::ifstream in(path);
        nlohmann::json j;
        in >> j;
        for (auto it = j.begin(); it != j.end(); ++it) {
            result.emplace_back(it.key(), it.value().get<PresetConfig>());
        }
        std::cout << "[PRESET] Loaded " << result.size() << " custom presets\n";
    } catch (const std::exception& e) {
        std::cerr << "[WARNING] Could not load presets: " << e.what() << "\n";
    }
    return result;
}

std::vector<std::pair<std::string, PresetConfig>> PresetManager::loadAll() {
    migrateLegacyFileIfNeeded();

    std::vector<std::pair<std::string, PresetConfig>> merged = ClickEnginePresets::builtins();
    for (auto& [name, cfg] : loadCustom()) {
        bool replaced = false;
        for (auto& [existingName, existingCfg] : merged) {
            if (existingName == name) {
                existingCfg = cfg;
                replaced = true;
                break;
            }
        }
        if (!replaced) {
            merged.emplace_back(name, cfg);
        }
    }
    return merged;
}

bool PresetManager::savePreset(const std::string& name, const PresetConfig& config) {
    migrateLegacyFileIfNeeded();
    const fs::path path = toFsPath(presetsFilePath());

    nlohmann::json j;
    try {
        std::error_code ec;
        fs::create_directories(path.parent_path(), ec);

        if (fs::exists(path)) {
            std::ifstream in(path);
            in >> j;
        }
        j[name] = config;

        std::ofstream out(path);
        out << j.dump(2);
        std::cout << "[PRESET] Saved: " << name << "\n";
        return true;
    } catch (const std::exception& e) {
        std::cerr << "[ERROR] Could not save preset: " << e.what() << "\n";
        return false;
    }
}

} // namespace mimic::core::config
