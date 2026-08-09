// Phase 0 placeholder: proves the CMake + Catch2 + mimic_core toolchain
// links and runs. Replaced by the real engine/config parity suite in
// Phase 1 (test_engine_moments.cpp etc.).

#include <catch2/catch_test_macros.hpp>

#include "version.h"

TEST_CASE("mimic_core reports a version string", "[scaffold]") {
    REQUIRE(mimic::core::versionString() != nullptr);
}
