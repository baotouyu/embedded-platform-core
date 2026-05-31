import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
UI_INCLUDE = REPO_ROOT / "components" / "ui" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_ui_header_is_platform_neutral():
    header = UI_INCLUDE / "ep_ui.h"
    text = header.read_text(encoding="utf-8")

    forbidden_tokens = [
        "lvgl.h",
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
        "platforms/",
    ]

    for token in forbidden_tokens:
        assert token not in text


def test_ui_header_compiles_standalone():
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = Path("ui_header_smoke.c")
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_ui.h"
            #include "ep_ui.h"

            int main(void)
            {
                int (*init_fn)(void) = ep_ui_init;
                int (*tick_fn)(unsigned int) = ep_ui_tick_inc;
                int (*process_fn)(void) = ep_ui_process;
                int (*deinit_fn)(void) = ep_ui_deinit;

                return (init_fn && tick_fn && process_fn && deinit_fn) ? 0 : 1;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    obj = Path("ui_header_smoke.o")
    try:
        result = subprocess.run(
            [
                COMPILER,
                "-std=c11",
                "-Wall",
                "-Wextra",
                "-I",
                str(UI_INCLUDE),
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
    finally:
        source.unlink(missing_ok=True)
        obj.unlink(missing_ok=True)

    assert result.returncode == 0, result.stderr
