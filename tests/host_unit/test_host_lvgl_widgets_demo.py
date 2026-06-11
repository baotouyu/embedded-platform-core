import platform
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_lvgl_package_exports_widgets_demo_library_and_headers():
    package = REPO_ROOT / "third_party/prebuilt/lvgl/host_macos"
    manifest = (package / "lvgl_package.txt").read_text()
    lv_conf = (package / "include/lv_conf.h").read_text()

    assert (package / "lib/liblvgl_demos.a").exists()
    assert (package / "include/demos/lv_demos.h").exists()
    assert (package / "include/demos/widgets/lv_demo_widgets.h").exists()
    assert "#define LV_USE_DEMO_WIDGETS 1" in lv_conf
    assert "demo_widgets=enabled" in manifest
    assert "demo_lib_hash=" in manifest


def test_lvgl_widgets_demo_static_library_is_tracked_by_git():
    package_library = "third_party/prebuilt/lvgl/host_macos/lib/liblvgl_demos.a"

    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", package_library],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )

    assert tracked.returncode == 0, (
        f"{package_library} must be tracked by git\n"
        f"stdout:\n{tracked.stdout}\nstderr:\n{tracked.stderr}"
    )


def test_lvgl_prebuilt_cmake_registers_demo_library_target():
    cmake = (REPO_ROOT / "cmake/modules/ep_lvgl_prebuilt.cmake").read_text()

    assert "EP_LVGL_DEMOS_LIBRARY" in cmake
    assert "lib/liblvgl_demos.a" in cmake
    assert "ep_thirdparty_lvgl_demos" in cmake
    assert "IMPORTED_LOCATION \"${EP_LVGL_DEMOS_LIBRARY}\"" in cmake
    assert "INTERFACE_LINK_LIBRARIES ep_thirdparty_lvgl" in cmake


def test_host_widgets_demo_source_calls_official_lvgl_demo():
    demo = REPO_ROOT / "platforms/host/posix/demos/lvgl_widgets_demo_main.c"

    assert demo.exists()

    text = demo.read_text()
    assert '#include "demos/widgets/lv_demo_widgets.h"' in text
    assert "ep_ui_init()" in text
    assert "ep_host_ui_port_init()" in text
    assert "lv_demo_widgets();" in text
    assert "ep_ui_tick_inc(EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS)" in text
    assert "ep_ui_process()" in text
    assert "ep_host_ui_port_should_quit()" in text
    assert "frame_start_ms = ep_time_now_ms()" in text
    assert "frame_elapsed_ms = ep_time_now_ms() - frame_start_ms" in text
    assert "if (frame_elapsed_ms < EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS)" in text
    assert "ep_sleep_ms((unsigned int)(EP_HOST_LVGL_WIDGETS_DEMO_FRAME_DELAY_MS - frame_elapsed_ms))" in text


def test_host_cmake_builds_widgets_demo_only_for_macos():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()

    assert "add_executable(ep_host_lvgl_widgets_demo" in cmake
    assert "demos/lvgl_widgets_demo_main.c" in cmake
    assert "ep_thirdparty_lvgl_demos" in cmake
    assert "EP_HAS_HOST_SDL2_UI=1" in cmake
    assert 'if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")' in cmake


def test_host_widgets_demo_builds_on_macos_arm64():
    if platform.system() != "Darwin" or platform.machine() not in {"arm64", "aarch64"}:
        pytest.skip("host LVGL widgets demo only builds on macOS arm64")

    build_dir = REPO_ROOT / "build"
    subprocess.run(["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)], check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "ep_host_lvgl_widgets_demo"], check=True)
    assert (build_dir / "platforms/host/posix/ep_host_lvgl_widgets_demo").exists()
