add_executable(mimic_tests
    test_scaffold.cpp
)

target_link_libraries(mimic_tests PRIVATE mimic_core Catch2::Catch2WithMain)
mimic_set_warnings(mimic_tests)

include(CTest)
include(Catch)
catch_discover_tests(mimic_tests)
