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


def test_host_platform_capability_source_is_wired_into_cmake():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "capability/ep_host_platform_capability.c" in cmake
    assert "ep_platform_api" in cmake


def test_host_platform_capabilities_are_queryable(tmp_path):
    compiler = _require_compiler()
    source = tmp_path / "host_platform_capability_smoke.c"
    executable = tmp_path / "host_platform_capability_smoke"

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_platform_capability.h"

            #include <string.h>

            int main(void)
            {
                if (!ep_platform_has_capability(EP_PLATFORM_CAPABILITY_FILESYSTEM)) {
                    return 1;
                }

                if (!ep_platform_has_capability(EP_PLATFORM_CAPABILITY_LOG)) {
                    return 2;
                }

                if (!ep_platform_has_capability(EP_PLATFORM_CAPABILITY_CONFIG_PERSISTENCE)) {
                    return 3;
                }

                if (!ep_platform_has_capability(EP_PLATFORM_CAPABILITY_THREAD)) {
                    return 4;
                }

                if (ep_platform_has_capability(EP_PLATFORM_CAPABILITY_GPIO)) {
                    return 5;
                }

                if (ep_platform_has_capability(EP_PLATFORM_CAPABILITY_NETWORK)) {
                    return 6;
                }

                if (ep_platform_has_capability(EP_PLATFORM_CAPABILITY_COUNT)) {
                    return 7;
                }

                if (strcmp(ep_platform_capability_name(EP_PLATFORM_CAPABILITY_FILESYSTEM), "filesystem") != 0) {
                    return 8;
                }

                if (strcmp(ep_platform_capability_name(EP_PLATFORM_CAPABILITY_GPIO), "gpio") != 0) {
                    return 9;
                }

                if (strcmp(ep_platform_capability_name(EP_PLATFORM_CAPABILITY_COUNT), "unknown") != 0) {
                    return 10;
                }

                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    compile_result = subprocess.run(
        [
            compiler,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            "-I",
            str(PLATFORM_INCLUDE),
            str(source),
            str(
                REPO_ROOT
                / "platforms/host/posix/capability/ep_host_platform_capability.c"
            ),
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
