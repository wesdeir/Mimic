add_library(mimic_core STATIC
    version.cpp
    PlatformClock.cpp
    mouse/SyntheticClick.cpp
    config/Config.cpp
    config/RiskAssessor.cpp
    config/PresetManager.cpp
    engine/AdaptiveClickerEngine.cpp
    session/SessionManager.cpp
    session/HumanClickTracker.cpp
)

target_include_directories(mimic_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mimic_core PUBLIC nlohmann_json::nlohmann_json)
target_link_libraries(mimic_core PRIVATE User32 Winmm Shell32 Ole32)

mimic_set_warnings(mimic_core)
