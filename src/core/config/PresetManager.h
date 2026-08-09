#pragma once

#include <string>
#include <vector>
#include <utility>

#include "ClickEnginePresets.h"

// Ported from mimic/config.py::PresetManager. Persists user-created presets
// to custom_presets.json. Unlike the Python original, this also migrates
// the file from its old (buggy) path -- see Config::presetsFileLegacyPath()
// -- to the corrected one, once, the first time it's touched.

namespace mimic::core::config {

class PresetManager {
public:
    // Runs the legacy-path migration (if needed), then returns the built-in
    // presets with any custom/saved presets overlaid on top (a custom preset
    // sharing a built-in's name replaces it, matching Python's
    // ClickEnginePresets.PRESETS.update(custom)).
    static std::vector<std::pair<std::string, PresetConfig>> loadAll();

    // Persists one preset (built-in name or new) to custom_presets.json.
    // Returns false on any I/O failure.
    static bool savePreset(const std::string& name, const PresetConfig& config);

private:
    static void migrateLegacyFileIfNeeded();
    static std::vector<std::pair<std::string, PresetConfig>> loadCustom();
};

} // namespace mimic::core::config
