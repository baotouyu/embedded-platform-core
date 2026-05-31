import platform
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_macos_sdl2_ui_port_files_and_api_are_present():
    header = REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.h"
    source = REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.c"

    assert header.exists()
    assert source.exists()

    header_text = header.read_text(encoding="utf-8")
    assert "int ep_host_ui_port_init(void);" in header_text
    assert "int ep_host_ui_port_deinit(void);" in header_text
    assert "lvgl.h" not in header_text
    assert "SDL2/SDL.h" not in header_text

    source_text = source.read_text(encoding="utf-8")
    assert '#include "ep_host_ui_port.h"' in source_text
    assert '#include "ep_osal_err.h"' in source_text
    assert '#include "lvgl.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_window.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_mouse.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_keyboard.h"' in source_text
    assert "lv_sdl_window_create(480, 320)" in source_text
    assert "lv_sdl_window_set_title" in source_text
    assert "lv_sdl_mouse_create()" in source_text
    assert "lv_sdl_keyboard_create()" in source_text
    assert "lv_deinit" not in source_text


def test_host_cmake_wires_sdl2_ui_port_only_for_host_macos():
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(encoding="utf-8")

    assert "ui_port/ep_host_ui_port.c" in host_cmake
    assert "EP_HAS_HOST_SDL2_UI=1" in host_cmake
    assert "APPLE" in host_cmake
    assert "CMAKE_SYSTEM_PROCESSOR" in host_cmake
    assert "ui_port" in host_cmake


def test_app_cmake_wires_host_sdl2_demo_dependencies():
    app_cmake = (REPO_ROOT / "app/CMakeLists.txt").read_text(encoding="utf-8")

    assert "EP_HAS_HOST_SDL2_UI" in app_cmake
    assert "ep_components_ui" in app_cmake
    assert "ep_thirdparty_lvgl" in app_cmake


def test_app_runs_host_sdl2_demo_behind_compile_flag():
    app_main = (REPO_ROOT / "app/main.c").read_text(encoding="utf-8")

    assert "#if defined(EP_HAS_HOST_SDL2_UI)" in app_main
    assert '#include "ep_ui.h"' in app_main
    assert '#include "ep_host_ui_port.h"' in app_main
    assert '#include "lvgl.h"' in app_main
    assert "ep_ui_init()" in app_main
    assert "ep_host_ui_port_init()" in app_main
    assert "lv_label_create(lv_screen_active())" in app_main
    assert 'lv_label_set_text(label, "embedded-platform-core host SDL2")' in app_main
    assert "ep_ui_process()" in app_main
    assert "#define APP_HOST_UI_FRAME_DELAY_MS 16u" in app_main
    assert "ep_sleep_ms(APP_HOST_UI_FRAME_DELAY_MS)" in app_main
    assert "ep_host_ui_port_deinit()" in app_main
    assert "ep_ui_deinit()" in app_main


def test_host_macos_binary_builds_and_runs_sdl2_demo():
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        pytest.skip("host macOS SDL2 UI smoke only runs on macOS arm64")

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(REPO_ROOT / "build")],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(REPO_ROOT / "build")],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    run = subprocess.run(
        [str(REPO_ROOT / "build/platforms/host/posix/ep_platform_host_posix")],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        f"run failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
