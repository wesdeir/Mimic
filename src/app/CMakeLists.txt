add_library(mimic_app STATIC
    app_info.cpp
)

target_include_directories(mimic_app PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(mimic_app PUBLIC mimic_core)

mimic_set_warnings(mimic_app)
