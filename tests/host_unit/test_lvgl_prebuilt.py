import platform
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_lvgl_host_macos_prebuilt_package_shape():
    package_root = REPO_ROOT / "third_party/prebuilt/lvgl/host_macos"
    manifest = package_root / "lvgl_package.txt"

    assert (package_root / "include/lvgl.h").exists()
    assert (package_root / "include/lv_conf.h").exists()
    assert (package_root / "lib/liblvgl.a").exists()
    assert (package_root / "LVGL_LICENCE.txt").exists()
    assert manifest.exists()

    manifest_text = manifest.read_text(encoding="utf-8")
    assert "lvgl.version=9.1.0" in manifest_text
    assert "lvgl.tag=v9.1.0" in manifest_text
    assert "platform=host_macos" in manifest_text
    assert "arch=arm64" in manifest_text
    assert "lv_conf_hash=" in manifest_text
    assert "lib_hash=" in manifest_text


def test_lvgl_host_macos_package_declares_sdl2_backend():
    package_root = REPO_ROOT / "third_party/prebuilt/lvgl/host_macos"
    manifest_text = (package_root / "lvgl_package.txt").read_text(encoding="utf-8")
    lv_conf = (package_root / "include/lv_conf.h").read_text(encoding="utf-8")

    assert "display_backend=sdl2" in manifest_text
    assert "input_backend=sdl2" in manifest_text
    assert "sdl2.version=" in manifest_text
    assert "sdl2.cflags=" in manifest_text
    assert "sdl2.libs=" in manifest_text
    assert "#define LV_USE_SDL 1" in lv_conf
    assert "#define LV_USE_DRAW_SDL 0" in lv_conf
    assert "#define LV_SDL_INCLUDE_PATH <SDL2/SDL.h>" in lv_conf


def test_lvgl_host_macos_static_library_is_tracked_by_git():
    package_library = "third_party/prebuilt/lvgl/host_macos/lib/liblvgl.a"

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


def test_lvgl_prebuilt_cmake_target_is_registered():
    top_level_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    module_path = REPO_ROOT / "cmake/modules/ep_lvgl_prebuilt.cmake"

    assert module_path.exists()

    module = module_path.read_text(encoding="utf-8")
    assert "EP_LVGL_PACKAGE" in module
    assert 'set(EP_LVGL_PACKAGE "host_macos"' in module
    assert "EP_LVGL_ROOT" in module
    assert "third_party/prebuilt/lvgl/${EP_LVGL_PACKAGE}" in module
    assert "add_library(ep_thirdparty_lvgl STATIC IMPORTED GLOBAL)" in module
    assert "IMPORTED_LOCATION" in module
    assert "INTERFACE_INCLUDE_DIRECTORIES" in module
    assert "lvgl_package.txt" in module
    assert "include(ep_lvgl_prebuilt)" in top_level_cmake


def test_lvgl_prebuilt_cmake_wires_sdl2_from_manifest():
    module = (REPO_ROOT / "cmake/modules/ep_lvgl_prebuilt.cmake").read_text(encoding="utf-8")

    assert "display_backend=sdl2" in module
    assert "input_backend=sdl2" in module
    assert "find_program(EP_SDL2_CONFIG_EXECUTABLE sdl2-config REQUIRED)" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --cflags" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --prefix" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --libs" in module
    assert "separate_arguments(EP_SDL2_CFLAGS_LIST NATIVE_COMMAND" in module
    assert "separate_arguments(EP_SDL2_LIBS_LIST NATIVE_COMMAND" in module
    assert 'set(EP_SDL2_INCLUDE_DIR "${EP_SDL2_PREFIX}/include")' in module
    assert "INTERFACE_COMPILE_OPTIONS" in module
    assert "INTERFACE_LINK_OPTIONS" in module
    assert "INTERFACE_INCLUDE_DIRECTORIES" in module


def test_lvgl_prebuilt_cmake_smoke_links_lv_init(tmp_path):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        pytest.skip("host_macos LVGL package can only be linked on macOS arm64")

    project_dir = tmp_path / "lvgl-smoke"
    project_dir.mkdir()

    (project_dir / "CMakeLists.txt").write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(lvgl_smoke C)

            list(APPEND CMAKE_MODULE_PATH "{REPO_ROOT / "cmake/modules"}")
            set(EP_PROJECT_ROOT "{REPO_ROOT}")
            include(ep_lvgl_prebuilt)

            add_executable(lvgl_smoke main.c)
            target_link_libraries(lvgl_smoke PRIVATE ep_thirdparty_lvgl)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project_dir / "main.c").write_text(
        textwrap.dedent(
            """
            #include "lvgl.h"

            int main(void)
            {
                lv_init();
                lv_deinit();
                return 0;
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
        [str(build_dir / "lvgl_smoke")],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        f"run failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
