add_library(mimic_core STATIC
    version.cpp
    PlatformClock.cpp
    mouse/SyntheticClick.cpp
    config/RiskAssessor.cpp
    engine/AdaptiveClickerEngine.cpp
)

target_include_directories(mimic_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mimic_core PRIVATE User32)

mimic_set_warnings(mimic_core)
