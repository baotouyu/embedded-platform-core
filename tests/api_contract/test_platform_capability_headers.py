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


def test_platform_capability_header_exists():
    assert (PLATFORM_INCLUDE / "ep_platform_capability.h").is_file()


def test_platform_capability_header_compiles_standalone(tmp_path):
    compiler = _require_compiler()
    source = tmp_path / "platform_capability_header_smoke.c"
    obj = tmp_path / "platform_capability_header_smoke.o"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_platform_capability.h"
            #include "ep_platform_capability.h"

            int main(void)
            {
                ep_platform_capability_e cap = EP_PLATFORM_CAPABILITY_FILESYSTEM;
                int (*has_fn)(ep_platform_capability_e) = ep_platform_has_capability;
                const char *(*name_fn)(ep_platform_capability_e) = ep_platform_capability_name;

                return (cap == EP_PLATFORM_CAPABILITY_FILESYSTEM && has_fn && name_fn) ? 0 : 1;
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
