# Mimic

Mimic is a Windows-only auto-clicker that simulates human clicking patterns with high statistical fidelity, using a Markov-chain state model and log-normal delay draws instead of fixed or naively-randomized delays. It targets Minecraft-style combat clicking and is built to keep its output statistically close to real human recordings (see `click_data/`).

This is the active C++/Dear ImGui rewrite of the project. The original Python/Tkinter implementation lives in `python_legacy/` as a reference -- it's what the C++ engine's constants were fitted against, and it's kept for that reason, not for further development.

## Status

**v1 scope, by design:** the clicker running, live basic stats, and the 3 built-in presets, in one compact keyboard-navigated panel -- deliberately not the original Python GUI's full 7-tab feature set. That functionality (detailed analytics, graphs, session history, human-baseline training/benchmarking, differential comparison) is **deferred, not removed from the design** -- it can be added back as its own screen(s) later without redesigning the engine underneath it.

## Requirements

- Windows 10/11
- Visual Studio Build Tools (MSVC) with the Windows 10/11 SDK
- CMake 3.24+
- Git (for the Dear ImGui submodule)

## Building

```cmd
git submodule update --init --recursive
cmake -S . -B build -G Ninja
cmake --build build --target Mimic
```

The build produces `build/src/gui/Mimic.exe`. Dependencies (Catch2 for the test suite) are fetched automatically via CMake's `FetchContent`; Dear ImGui is a pinned git submodule under `third_party/imgui`.

### Running the tests

```cmd
cmake --build build --target mimic_tests
build/tests/mimic_tests.exe
```

The suite validates the click-timing engine against a frozen reference run of the original Python engine (`tools/python_reference/golden/`) and against the real recordings in `click_data/`, plus closed-form checks on the underlying math.

## Using it

| Key | Action |
|-----|--------|
| `F4` | Toggle clicking on/off (works even when another window has focus) |
| Hold `LEFT CLICK` | Auto-click while enabled |
| `Up` / `Down` | Move between the mode toggle and presets |
| `Enter` | Apply the highlighted setting |

## Project layout

```
src/
  core/   -- headless engine/config logic (no GUI, no Win32 GUI deps)
  app/    -- click thread, physical-hold input hook, global hotkey, orchestration
  gui/    -- Dear ImGui panel and Win32/DirectX11 entry point
tests/    -- Catch2 test suite
tools/python_reference/  -- golden reference data generated from python_legacy/
click_data/               -- real click recordings the engine's constants are fitted to
python_legacy/            -- original Python implementation (reference only)
```

## Disclaimer

This software is for educational and research purposes only. Using automation tools in online games may violate Terms of Service and result in account bans. The authors accept no responsibility for damages resulting from the use of this tool.
