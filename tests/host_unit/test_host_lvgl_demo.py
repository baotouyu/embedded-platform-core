import platform
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_lvgl_demo_source_and_behavior_are_declared():
    demo = REPO_ROOT / "platforms/host/posix/demos/lvgl_demo_main.c"

    assert demo.exists()

    text = demo.read_text()
    assert "ep_ui_init()" in text
    assert "ep_host_ui_port_init()" in text
    assert "ep_ui_tick_inc(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS)" in text
    assert "ep_ui_process()" in text
    assert "frame_start_ms = ep_time_now_ms()" in text
    assert "frame_elapsed_ms = ep_time_now_ms() - frame_start_ms" in text
    assert "if (frame_elapsed_ms < EP_HOST_LVGL_DEMO_FRAME_DELAY_MS)" in text
    assert "ep_sleep_ms((unsigned int)(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS - frame_elapsed_ms))" in text
    assert "#define EP_HOST_LVGL_DEMO_FRAME_DELAY_MS 16u" in text
    assert "ep_host_ui_port_should_quit()" in text
    assert "lv_label_create" in text
    assert "lv_button_create" in text
    assert "lv_obj_add_event_cb" in text
    assert "EP_HOST_LVGL_DEMO_EXIT_TEXT" in text


def test_host_ui_port_exposes_quit_query_without_polluting_public_ui():
    header = (REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.h").read_text()
    source = (REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.c").read_text()
    public_ui = (REPO_ROOT / "components/ui/include/ep_ui.h").read_text()

    assert "int ep_host_ui_port_should_quit(void);" in header
    assert "SDL_PollEvent" in source
    assert "SDL_PushEvent" in source
    assert "SDL_AddEventWatch" in source
    assert "SDL_DelEventWatch" in source
    assert "SDL_QUIT" in source
    assert "SDL_WINDOWEVENT_CLOSE" in source
    assert "exit(0)" in source
    assert "ep_host_ui_port_should_quit" in source

    assert "ep_host_ui_port" not in public_ui
    assert "SDL" not in public_ui


def test_host_cmake_builds_lvgl_demo_only_for_host_macos():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    app_cmake = (REPO_ROOT / "app/CMakeLists.txt").read_text()

    assert "add_executable(ep_host_lvgl_demo" in cmake
    assert "demos/lvgl_demo_main.c" in cmake
    assert "${CMAKE_SOURCE_DIR}/app/ui/page_manager.c" in cmake
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages/home_page.c" in cmake
    assert "${CMAKE_SOURCE_DIR}/app/ui/pages/settings_page.c" in cmake
    assert "ui_port/ep_host_ui_port.c" in cmake
    assert "osal_port/ep_host_osal_mem.c" in cmake
    assert "osal_port/ep_host_osal_mutex.c" in cmake
    assert "ep_components_ui" in cmake
    assert "ep_thirdparty_lvgl" in cmake
    assert "EP_HAS_HOST_SDL2_UI=1" in cmake
    assert "EP_HOME_CAROUSEL_DISABLE_LIVE_SCALE" not in cmake
    assert 'if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")' in cmake

    assert "ep_host_lvgl_demo" not in app_cmake
    assert "lvgl_demo_main.c" not in app_cmake


def test_host_lvgl_demo_builds_on_macos_arm64():
    if platform.system() != "Darwin" or platform.machine() not in {"arm64", "aarch64"}:
        pytest.skip("host LVGL demo only builds on macOS arm64")

    build_dir = REPO_ROOT / "build"
    subprocess.run(["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)], check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "ep_host_lvgl_demo"], check=True)
    assert (build_dir / "platforms/host/posix/ep_host_lvgl_demo").exists()
