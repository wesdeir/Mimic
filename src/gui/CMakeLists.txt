set(IMGUI_DIR ${CMAKE_SOURCE_DIR}/third_party/imgui)

add_executable(Mimic WIN32
    main.cpp
    AppTheme.cpp
    ${IMGUI_DIR}/imgui.cpp
    ${IMGUI_DIR}/imgui_draw.cpp
    ${IMGUI_DIR}/imgui_tables.cpp
    ${IMGUI_DIR}/imgui_widgets.cpp
    ${IMGUI_DIR}/backends/imgui_impl_win32.cpp
    ${IMGUI_DIR}/backends/imgui_impl_dx11.cpp
)

target_include_directories(Mimic PRIVATE
    ${IMGUI_DIR}
    ${IMGUI_DIR}/backends
    ${CMAKE_CURRENT_SOURCE_DIR}
)

target_link_libraries(Mimic PRIVATE
    mimic_app
    d3d11
    dxgi
    d3dcompiler
    User32
    Gdi32
)

mimic_set_warnings(Mimic)
