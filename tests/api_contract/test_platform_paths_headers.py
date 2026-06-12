import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PLATFORM_INCLUDE = REPO_ROOT / "platforms" / "include"


def _require_compiler() -> str:
    compiler = shutil.which("clang") or shutil.which("cc")
    assert compiler, "Expected clang or cc to be available for compile smoke test"
    return compiler


def test_platform_paths_header_exists():
    assert (PLATFORM_INCLUDE / "ep_platform_paths.h").is_file()


def test_platform_paths_header_compiles_standalone(tmp_path):
    compiler = _require_compiler()
    source = tmp_path / "platform_paths_header_smoke.c"
    obj = tmp_path / "platform_paths_header_smoke.o"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_platform_paths.h"
            #include "ep_platform_paths.h"

            int main(void)
            {
                const char *(*config_fn)(void) = ep_platform_config_profile_path;
                const char *(*resource_fn)(void) = ep_platform_resource_root_path;
                int (*asset_fn)(const char *, char *, size_t) = ep_platform_asset_path;
                int (*image_fn)(const char *, char *, size_t) = ep_platform_image_path;
                int (*lvgl_image_fn)(const char *, char *, size_t) = ep_platform_lvgl_image_src;
                int (*font_fn)(const char *, char *, size_t) = ep_platform_font_path;
                int (*lvgl_font_fn)(const char *, char *, size_t) = ep_platform_lvgl_font_src;
                int (*theme_fn)(const char *, char *, size_t) = ep_platform_theme_path;

                return (
                    config_fn &&
                    resource_fn &&
                    asset_fn &&
                    image_fn &&
                    lvgl_image_fn &&
                    font_fn &&
                    lvgl_font_fn &&
                    theme_fn
                ) ? 0 : 1;
            }
            """
        ).strip()
        + "\n"
    )

    result = subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(PLATFORM_INCLUDE),
            "-c",
            str(source),
            "-o",
            str(obj),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, (
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
