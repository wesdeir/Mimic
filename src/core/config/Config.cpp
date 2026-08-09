#include "Config.h"

#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shlobj.h>

namespace mimic::core::config {

namespace {

std::wstring desktopPath() {
    PWSTR path = nullptr;
    std::wstring result;
    if (SUCCEEDED(SHGetKnownFolderPath(FOLDERID_Desktop, 0, nullptr, &path))) {
        result = path;
    }
    if (path) {
        CoTaskMemFree(path);
    }
    return result;
}

} // namespace

std::wstring trainingDataPath() {
    return desktopPath() + L"\\Mimic\\mimic_data";
}

std::wstring clickerDataPath() {
    return trainingDataPath() + L"\\mimicSessions";
}

std::wstring sessionsFilePath() {
    return trainingDataPath() + L"\\sessions.json";
}

std::wstring presetsFilePath() {
    return trainingDataPath() + L"\\custom_presets.json";
}

std::wstring presetsFileLegacyPath() {
    return desktopPath() + L"\\mimic_data\\custom_presets.json";
}

} // namespace mimic::core::config
