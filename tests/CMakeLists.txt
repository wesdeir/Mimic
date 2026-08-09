add_executable(mimic_tests
    test_scaffold.cpp
    test_engine_moments.cpp
    test_presets.cpp
    test_risk_assessor.cpp
    test_click_data_calibration.cpp
)

target_link_libraries(mimic_tests PRIVATE mimic_core Catch2::Catch2WithMain)
target_include_directories(mimic_tests PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
mimic_set_warnings(mimic_tests)

target_compile_definitions(mimic_tests PRIVATE
    MIMIC_GOLDEN_DIR="${CMAKE_SOURCE_DIR}/tools/python_reference/golden"
    MIMIC_CLICK_DATA_DIR="${CMAKE_SOURCE_DIR}/click_data"
)

include(CTest)
include(Catch)
catch_discover_tests(mimic_tests)
