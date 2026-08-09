cmake_minimum_required(VERSION 3.24)
project(Mimic CXX)

if(NOT WIN32)
    message(FATAL_ERROR "Mimic is Windows-only (Win32 mouse/hook APIs, DirectX 11 renderer).")
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(MIMIC_BUILD_TESTS "Build the Catch2 test suite" ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
include(CompilerWarnings)

include(FetchContent)

FetchContent_Declare(
    nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
)
FetchContent_MakeAvailable(nlohmann_json)

if(MIMIC_BUILD_TESTS)
    FetchContent_Declare(
        catch2
        GIT_REPOSITORY https://github.com/catchorg/Catch2.git
        GIT_TAG v3.7.1
    )
    FetchContent_MakeAvailable(catch2)
    list(APPEND CMAKE_MODULE_PATH ${catch2_SOURCE_DIR}/extras)
endif()

add_subdirectory(src/core)
add_subdirectory(src/app)
add_subdirectory(src/gui)

if(MIMIC_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()
