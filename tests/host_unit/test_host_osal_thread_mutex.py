import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_thread_and_mutex_sources():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_thread.c" in cmake
    assert "osal_port/ep_host_osal_mutex.c" in cmake


def test_host_osal_thread_and_mutex_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_thread_mutex_smoke.c"
    executable = tmp_path / "host_osal_thread_mutex_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_mutex.h"
            #include "ep_osal_thread.h"

            typedef struct {
                ep_mutex_t *mutex;
                int value;
            } shared_state_t;

            static void *worker_entry(void *arg)
            {
                shared_state_t *state = (shared_state_t *)arg;

                if (ep_mutex_lock(state->mutex) != EP_OK) {
                    return (void *)1;
                }

                state->value += 1;

                if (ep_mutex_unlock(state->mutex) != EP_OK) {
                    return (void *)2;
                }

                return 0;
            }

            int main(void)
            {
                ep_thread_t *thread = 0;
                shared_state_t state;

                state.mutex = 0;
                state.value = 0;

                if (ep_mutex_create(0) == EP_OK) {
                    return 1;
                }

                if (ep_mutex_lock(0) == EP_OK) {
                    return 2;
                }

                if (ep_mutex_unlock(0) == EP_OK) {
                    return 3;
                }

                if (ep_thread_create(0, "invalid", worker_entry, &state) == EP_OK) {
                    return 4;
                }

                if (ep_thread_create(&thread, "invalid", 0, &state) == EP_OK) {
                    return 5;
                }

                if (ep_thread_join(0) == EP_OK) {
                    return 6;
                }

                if (ep_mutex_create(&state.mutex) != EP_OK) {
                    return 7;
                }

                if (ep_mutex_lock(state.mutex) != EP_OK) {
                    return 8;
                }

                if (ep_mutex_unlock(state.mutex) != EP_OK) {
                    return 9;
                }

                if (ep_thread_create(&thread, "host-worker", worker_entry, &state) != EP_OK) {
                    return 10;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 11;
                }

                if (state.value != 1) {
                    return 12;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
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
