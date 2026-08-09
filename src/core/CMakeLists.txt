add_library(mimic_core STATIC
    version.cpp
)

target_include_directories(mimic_core PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mimic_core PUBLIC nlohmann_json::nlohmann_json)
target_link_libraries(mimic_core PRIVATE User32 Winmm)

mimic_set_warnings(mimic_core)
