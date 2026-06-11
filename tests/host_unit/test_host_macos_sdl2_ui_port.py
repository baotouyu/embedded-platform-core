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
    assert '#include "src/misc/cache/lv_image_cache.h"' in source_text
    assert '#include "src/misc/lv_timer.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_window.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_mouse.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_keyboard.h"' in source_text
    assert "#define EP_HOST_UI_HOR_RES 800" in source_text
    assert "#define EP_HOST_UI_VER_RES 480" in source_text
    assert "#define EP_HOST_UI_REFR_PERIOD_MS 16u" in source_text
    assert "#define EP_HOST_UI_IMAGE_CACHE_SIZE (12u * 1024u * 1024u)" in source_text
    assert "#define EP_HOST_UI_IMAGE_HEADER_CACHE_COUNT 64u" in source_text
    assert "lv_sdl_window_create(EP_HOST_UI_HOR_RES, EP_HOST_UI_VER_RES)" in source_text
    assert "lv_display_get_refr_timer(g_host_ui_display)" in source_text
    assert "lv_timer_set_period(refresh_timer, EP_HOST_UI_REFR_PERIOD_MS)" in source_text
    assert "lv_image_cache_resize(EP_HOST_UI_IMAGE_CACHE_SIZE, true)" in source_text
    assert "lv_image_header_cache_resize(EP_HOST_UI_IMAGE_HEADER_CACHE_COUNT, true)" in source_text
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
    assert "ep_components_ui" in host_cmake
    assert "ep_thirdparty_lvgl" in host_cmake


def test_app_cmake_stays_platform_neutral():
    app_cmake = (REPO_ROOT / "app/CMakeLists.txt").read_text(encoding="utf-8")

    assert "ui/app_ui.c" in app_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/ui" in app_cmake
    assert "${EP_LVGL_INCLUDE_DIR}" in app_cmake
    assert "EP_HAS_HOST_SDL2_UI" not in app_cmake
    assert "ep_host_ui_port" not in app_cmake


def test_host_startup_runs_sdl2_demo_behind_compile_flag():
    startup = (REPO_ROOT / "platforms/host/posix/startup/main.c").read_text(encoding="utf-8")

    assert "#if defined(EP_HAS_HOST_SDL2_UI)" in startup
    assert '#include "app_ui.h"' in startup
    assert '#include "ep_ui.h"' in startup
    assert '#include "ep_host_ui_port.h"' in startup
    assert '#include "lvgl.h"' not in startup
    assert "ep_framework_start()" in startup
    assert "ep_ui_init()" in startup
    assert "ep_host_ui_port_init()" in startup
    assert "app_ui_create()" in startup
    assert "lv_label_create" not in startup
    assert "lv_label_set_text" not in startup
    assert "ep_ui_process()" in startup
    assert "#define EP_HOST_UI_FRAME_DELAY_MS 16u" in startup
    assert "frame_start_ms = ep_time_now_ms()" in startup
    assert "frame_elapsed_ms = ep_time_now_ms() - frame_start_ms" in startup
    assert "if (frame_elapsed_ms < EP_HOST_UI_FRAME_DELAY_MS)" in startup
    assert "ep_sleep_ms((unsigned int)(EP_HOST_UI_FRAME_DELAY_MS - frame_elapsed_ms))" in startup
    assert "ep_host_ui_port_deinit()" in startup
    assert "ep_ui_deinit()" in startup


def test_app_main_remains_platform_neutral():
    app_main = (REPO_ROOT / "app/main.c").read_text(encoding="utf-8")

    assert "EP_HAS_HOST_SDL2_UI" not in app_main
    assert "ep_host_ui_port" not in app_main
    assert "lvgl.h" not in app_main


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
