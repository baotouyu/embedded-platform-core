import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_platform_paths_source_is_wired_into_cmake():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "paths/ep_host_platform_paths.c" in cmake
    assert "ep_platform_api" in cmake


def test_rtos_platform_paths_split_static_images_and_recipe_data():
    source_path = REPO_ROOT / "platforms/rtos/demo_family/paths/ep_rtos_platform_paths.c"
    cmake = (REPO_ROOT / "platforms/rtos/demo_family/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert source_path.is_file()
    assert "paths/ep_rtos_platform_paths.c" in cmake


def test_rtos_platform_paths_are_queryable(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtos_platform_paths_smoke.c"
    executable = tmp_path / "rtos_platform_paths_smoke"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_platform_paths.h"

            #include <string.h>

            int main(void)
            {
                char path[128];
                char small[8];

                if (strcmp(ep_platform_config_profile_path(), "/data/ep/config/profile.cfg") != 0) {
                    return 1;
                }

                if (strcmp(ep_platform_resource_root_path(), "/data/ep/resources") != 0) {
                    return 2;
                }

                if (ep_platform_asset_path("recipe/recipelib.db", path, sizeof(path)) != EP_OK) {
                    return 3;
                }

                if (strcmp(path, "/data/ep/resources/recipe/recipelib.db") != 0) {
                    return 4;
                }

                if (ep_platform_image_path("home_bg.png", path, sizeof(path)) != EP_OK) {
                    return 5;
                }

                if (strcmp(path, "/rodata/ep/resources/images/home_bg.png") != 0) {
                    return 6;
                }

                if (ep_platform_lvgl_image_src("home_bg.png", path, sizeof(path)) != EP_OK) {
                    return 7;
                }

                if (strcmp(path, "L:/rodata/ep/resources/images/home_bg.png") != 0) {
                    return 8;
                }

                if (ep_platform_recipe_path("recipelib.db", path, sizeof(path)) != EP_OK) {
                    return 9;
                }

                if (strcmp(path, "/data/ep/resources/recipe/recipelib.db") != 0) {
                    return 10;
                }

                if (ep_platform_lvgl_recipe_src("latte.png", path, sizeof(path)) != EP_OK) {
                    return 11;
                }

                if (strcmp(path, "L:/data/ep/resources/recipe/latte.png") != 0) {
                    return 12;
                }

                if (ep_platform_font_path("main.ttf", path, sizeof(path)) != EP_OK) {
                    return 13;
                }

                if (strcmp(path, "/rodata/ep/resources/fonts/main.ttf") != 0) {
                    return 14;
                }

                if (ep_platform_theme_path("default.bin", path, sizeof(path)) != EP_OK) {
                    return 15;
                }

                if (strcmp(path, "/rodata/ep/resources/themes/default.bin") != 0) {
                    return 16;
                }

                if (ep_platform_recipe_path("../bad.db", path, sizeof(path)) != EP_ERR_INVAL) {
                    return 17;
                }

                if (ep_platform_lvgl_recipe_src("latte.png", small, sizeof(small)) != EP_ERR_INVAL) {
                    return 18;
                }

                if (small[0] != '\\0') {
                    return 19;
                }

                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "platforms/rtos/demo_family/paths/ep_rtos_platform_paths.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert compile_result.returncode == 0, (
        f"stdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )


def test_host_platform_paths_are_queryable(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_platform_paths_smoke.c"
    executable = tmp_path / "host_platform_paths_smoke"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_platform_paths.h"

            #include <string.h>

            int main(void)
            {
                char path[96];
                char small[8];

                if (strcmp(ep_platform_config_profile_path(), "config/profiles/host.cfg") != 0) {
                    return 1;
                }

                if (strcmp(ep_platform_resource_root_path(), "resources/host") != 0) {
                    return 2;
                }

                if (ep_platform_asset_path("images/logo.png", path, sizeof(path)) != EP_OK) {
                    return 3;
                }

            if (strcmp(path, "resources/host/images/logo.png") != 0) {
                return 4;
            }

            if (ep_platform_asset_path("images/logo..backup.png", path, sizeof(path)) != EP_OK) {
                return 18;
            }

            if (strcmp(path, "resources/host/images/logo..backup.png") != 0) {
                return 19;
            }

            if (ep_platform_image_path("logo.png", path, sizeof(path)) != EP_OK) {
                return 5;
            }

                if (strcmp(path, "resources/host/images/logo.png") != 0) {
                    return 6;
                }

                if (ep_platform_lvgl_image_src("logo.png", path, sizeof(path)) != EP_OK) {
                    return 20;
                }

                if (strcmp(path, "A:resources/host/images/logo.png") != 0) {
                    return 21;
                }

                if (ep_platform_lvgl_image_src("drinks/latte.png", path, sizeof(path)) != EP_OK) {
                    return 22;
                }

                if (strcmp(path, "A:resources/host/images/drinks/latte.png") != 0) {
                    return 23;
                }

                if (ep_platform_font_path("main.ttf", path, sizeof(path)) != EP_OK) {
                    return 7;
                }

                if (strcmp(path, "resources/host/fonts/main.ttf") != 0) {
                    return 8;
                }

                if (ep_platform_recipe_path("latte.png", path, sizeof(path)) != EP_OK) {
                    return 26;
                }

                if (strcmp(path, "resources/host/recipe/latte.png") != 0) {
                    return 27;
                }

                if (ep_platform_lvgl_recipe_src("latte.png", path, sizeof(path)) != EP_OK) {
                    return 28;
                }

                if (strcmp(path, "A:resources/host/recipe/latte.png") != 0) {
                    return 29;
                }

                if (ep_platform_theme_path("default.bin", path, sizeof(path)) != EP_OK) {
                    return 9;
                }

                if (strcmp(path, "resources/host/themes/default.bin") != 0) {
                    return 10;
                }

                if (ep_platform_asset_path(0, path, sizeof(path)) != EP_ERR_INVAL) {
                    return 11;
                }

                if (ep_platform_asset_path("", path, sizeof(path)) != EP_ERR_INVAL) {
                    return 12;
                }

                if (ep_platform_asset_path("/bad", path, sizeof(path)) != EP_ERR_INVAL) {
                    return 13;
                }

                if (ep_platform_asset_path("bad/../x", path, sizeof(path)) != EP_ERR_INVAL) {
                    return 14;
                }

                if (ep_platform_asset_path("images/logo.png", 0, sizeof(path)) != EP_ERR_INVAL) {
                    return 15;
                }

                if (ep_platform_asset_path("images/logo.png", path, 0) != EP_ERR_INVAL) {
                    return 16;
                }

                if (ep_platform_image_path("logo.png", small, sizeof(small)) != EP_ERR_INVAL) {
                    return 17;
                }

                if (ep_platform_lvgl_image_src("logo.png", small, sizeof(small)) != EP_ERR_INVAL) {
                    return 24;
                }

                if (small[0] != '\\0') {
                    return 25;
                }

                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(REPO_ROOT / "platforms/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "platforms/host/posix/paths/ep_host_platform_paths.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert compile_result.returncode == 0, (
        f"stdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
