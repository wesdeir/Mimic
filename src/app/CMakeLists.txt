add_library(mimic_app STATIC
    app_info.cpp
    InputHook.cpp
    GlobalHotkeys.cpp
    AppController.cpp
)

target_include_directories(mimic_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mimic_app PUBLIC mimic_core)
target_link_libraries(mimic_app PRIVATE User32)

mimic_set_warnings(mimic_app)
