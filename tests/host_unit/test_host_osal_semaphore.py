import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_semaphore_source_and_threads():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_sem.c" in cmake
    assert "Threads::Threads" in cmake


def test_host_osal_semaphore_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_semaphore_smoke.c"
    executable = tmp_path / "host_osal_semaphore_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_sem.h"
            #include "ep_osal_thread.h"
            #include "ep_osal_time.h"

            static void *poster_entry(void *arg)
            {
                ep_sem_t *sem = (ep_sem_t *)arg;

                ep_sleep_ms(10);

                if (ep_sem_post(sem) != EP_OK) {
                    return (void *)1;
                }

                return 0;
            }

            int main(void)
            {
                ep_sem_t *sem = 0;
                ep_thread_t *thread = 0;
                uint64_t before = 0;
                uint64_t after = 0;

                if (ep_sem_create(0, 1) == EP_OK) {
                    return 1;
                }

                if (ep_sem_wait(0, 0) == EP_OK) {
                    return 2;
                }

                if (ep_sem_post(0) == EP_OK) {
                    return 3;
                }

                if (ep_sem_create(&sem, 1) != EP_OK) {
                    return 4;
                }

                if (ep_sem_wait(sem, 0) != EP_OK) {
                    return 5;
                }

                if (ep_sem_wait(sem, 0) != EP_ERR_TIMEOUT) {
                    return 6;
                }

                before = ep_time_now_ms();
                if (ep_sem_wait(sem, 5) != EP_ERR_TIMEOUT) {
                    return 7;
                }
                after = ep_time_now_ms();

                if (after < before) {
                    return 8;
                }

                if (ep_thread_create(&thread, "sem-poster", poster_entry, sem) != EP_OK) {
                    return 9;
                }

                if (ep_sem_wait(sem, 500) != EP_OK) {
                    return 10;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 11;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_sem.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            "-pthread",
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
