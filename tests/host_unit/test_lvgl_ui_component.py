import platform
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ui_component_layout_and_public_header_are_platform_neutral():
    component_root = REPO_ROOT / "components/ui"
    header = component_root / "include/ep_ui.h"

    assert (component_root / "CMakeLists.txt").exists()
    assert header.exists()
    assert (component_root / "src/ep_ui.c").exists()

    header_text = header.read_text(encoding="utf-8")
    assert "int ep_ui_init(void);" in header_text
    assert "int ep_ui_tick_inc(unsigned int elapsed_ms);" in header_text
    assert "int ep_ui_process(void);" in header_text
    assert "int ep_ui_deinit(void);" in header_text

    forbidden_headers = [
        "lvgl.h",
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
    ]
    for forbidden in forbidden_headers:
        assert forbidden not in header_text


def test_ui_component_calls_lvgl_lifecycle_apis_without_platform_headers():
    source = (REPO_ROOT / "components/ui/src/ep_ui.c").read_text(encoding="utf-8")

    assert '#include "ep_ui.h"' in source
    assert '#include "ep_osal_err.h"' in source
    assert '#include "lvgl.h"' in source
    assert "lv_init();" in source
    assert "lv_tick_inc(elapsed_ms);" in source
    assert "lv_timer_handler();" in source
    assert "lv_deinit();" in source

    forbidden_headers = [
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
        "SDL2/SDL.h",
        "lv_sdl_window.h",
        "ep_host_ui_port.h",
    ]
    for forbidden in forbidden_headers:
        assert forbidden not in source


def test_ui_component_is_wired_into_cmake():
    top_level = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    component_cmake = (REPO_ROOT / "components/ui/CMakeLists.txt").read_text(encoding="utf-8")
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(encoding="utf-8")

    assert "add_subdirectory(components/ui)" in top_level
    assert "add_library(ep_components_ui STATIC" in component_cmake
    assert "src/ep_ui.c" in component_cmake
    assert "target_include_directories(ep_components_ui" in component_cmake
    assert "../../osal/include" in component_cmake
    assert "ep_thirdparty_lvgl" in component_cmake
    assert "ep_components_ui" in host_cmake
    assert "APPLE" in host_cmake
    assert "CMAKE_SYSTEM_PROCESSOR" in host_cmake


def test_ui_component_cmake_smoke_links_lvgl_lifecycle(tmp_path):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        pytest.skip("host_macos LVGL package can only be linked on macOS arm64")

    project_dir = tmp_path / "ui-smoke"
    project_dir.mkdir()

    (project_dir / "CMakeLists.txt").write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(ui_smoke C)

            list(APPEND CMAKE_MODULE_PATH "{REPO_ROOT / "cmake/modules"}")
            set(EP_PROJECT_ROOT "{REPO_ROOT}")
            include(ep_lvgl_prebuilt)

            add_subdirectory("{REPO_ROOT / "components/ui"}" ui-build)

            add_executable(ui_smoke main.c)
            target_link_libraries(ui_smoke PRIVATE ep_components_ui)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project_dir / "main.c").write_text(
        textwrap.dedent(
            """
            #include "ep_ui.h"

            int main(void)
            {
                int rc = ep_ui_init();
                if (rc != 0) {
                    return rc;
                }

                rc = ep_ui_tick_inc(1u);
                if (rc != 0) {
                    return rc;
                }

                rc = ep_ui_process();
                if (rc != 0) {
                    return rc;
                }

                return ep_ui_deinit();
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    build_dir = project_dir / "build"
    configure = subprocess.run(
        ["cmake", "-S", str(project_dir), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    run = subprocess.run(
        [str(build_dir / "ui_smoke")],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        f"run failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
