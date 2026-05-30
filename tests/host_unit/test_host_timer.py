import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_timer_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    timer_cmake_path = REPO_ROOT / "components/timer/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/timer)" in root_cmake
    assert timer_cmake_path.exists()

    timer_cmake = timer_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_timer STATIC" in timer_cmake
    assert "src/ep_timer.c" in timer_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
    assert "ep_components_timer" in host_cmake


def test_host_timer_init_and_invalid_arguments(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_invalid_smoke.c"
    executable = tmp_path / "host_timer_invalid_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_timer.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                if (ep_timer_start(1, 10, 100) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_timer_stop(1) != EP_ERR_UNSUPPORTED) {
                    return 2;
                }

                if (ep_timer_init() != EP_OK) {
                    return 3;
                }

                if (ep_timer_init() != EP_OK) {
                    return 4;
                }

                if (ep_timer_start(-1, 10, 100) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_timer_stop(-1) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_timer_stop(999) != EP_ERR_INVAL) {
                    return 7;
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
            "-I",
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, run_result.stderr
