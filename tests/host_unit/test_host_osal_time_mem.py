import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_time_and_mem_sources():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_time.c" in cmake
    assert "osal_port/ep_host_osal_mem.c" in cmake


def test_host_osal_time_and_mem_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_time_mem_smoke.c"
    executable = tmp_path / "host_osal_time_mem_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_mem.h"
            #include "ep_osal_time.h"

            int main(void)
            {
                unsigned char *buffer = (unsigned char *)ep_malloc(4);
                uint64_t before = 0;
                uint64_t after = 0;

                if (buffer == 0) {
                    return 1;
                }

                buffer[0] = 0x12;
                buffer[1] = 0x34;
                buffer[2] = 0x56;
                buffer[3] = 0x78;

                before = ep_time_now_ms();
                ep_sleep_ms(1);
                after = ep_time_now_ms();

                ep_free(buffer);
                ep_free(0);

                if (after < before) {
                    return 2;
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
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
