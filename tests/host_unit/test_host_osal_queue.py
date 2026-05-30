import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_queue_source():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_queue.c" in cmake


def test_host_osal_queue_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_queue_smoke.c"
    executable = tmp_path / "host_osal_queue_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_queue.h"
            #include "ep_osal_thread.h"
            #include "ep_osal_time.h"

            typedef struct {
                int id;
                int value;
            } message_t;

            typedef struct {
                ep_queue_t *queue;
                message_t message;
            } worker_state_t;

            static void *delayed_sender(void *arg)
            {
                worker_state_t *state = (worker_state_t *)arg;

                ep_sleep_ms(10);

                if (ep_queue_send(state->queue, &state->message, 500) != EP_OK) {
                    return (void *)1;
                }

                return 0;
            }

            static void *delayed_receiver(void *arg)
            {
                worker_state_t *state = (worker_state_t *)arg;
                message_t received;

                ep_sleep_ms(10);

                if (ep_queue_recv(state->queue, &received, 500) != EP_OK) {
                    return (void *)1;
                }

                if (received.id != state->message.id || received.value != state->message.value) {
                    return (void *)2;
                }

                return 0;
            }

            int main(void)
            {
                ep_queue_t *queue = 0;
                ep_thread_t *thread = 0;
                worker_state_t state;
                message_t first = { .id = 1, .value = 100 };
                message_t second = { .id = 2, .value = 200 };
                message_t third = { .id = 3, .value = 300 };
                message_t received = { .id = 0, .value = 0 };
                int scalar = 42;

                if (ep_queue_create(0, sizeof(message_t), 2) == EP_OK) {
                    return 1;
                }

                if (ep_queue_create(&queue, 0, 2) == EP_OK) {
                    return 2;
                }

                if (ep_queue_create(&queue, sizeof(message_t), 0) == EP_OK) {
                    return 3;
                }

                if (ep_queue_send(0, &first, 0) == EP_OK) {
                    return 4;
                }

                if (ep_queue_recv(0, &received, 0) == EP_OK) {
                    return 5;
                }

                if (ep_queue_create(&queue, sizeof(message_t), 1) != EP_OK) {
                    return 6;
                }

                if (ep_queue_send(queue, 0, 0) == EP_OK) {
                    return 7;
                }

                if (ep_queue_recv(queue, 0, 0) == EP_OK) {
                    return 8;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_ERR_TIMEOUT) {
                    return 9;
                }

                if (ep_queue_send(queue, &first, 0) != EP_OK) {
                    return 10;
                }

                if (ep_queue_send(queue, &second, 0) != EP_ERR_TIMEOUT) {
                    return 11;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_OK) {
                    return 12;
                }

                if (received.id != first.id || received.value != first.value) {
                    return 13;
                }

                state.queue = queue;
                state.message = second;
                thread = 0;

                if (ep_thread_create(&thread, "queue-sender", delayed_sender, &state) != EP_OK) {
                    return 14;
                }

                if (ep_queue_recv(queue, &received, 500) != EP_OK) {
                    return 15;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 16;
                }

                if (received.id != second.id || received.value != second.value) {
                    return 17;
                }

                if (ep_queue_send(queue, &third, 0) != EP_OK) {
                    return 18;
                }

                state.message = third;
                thread = 0;

                if (ep_thread_create(&thread, "queue-receiver", delayed_receiver, &state) != EP_OK) {
                    return 19;
                }

                if (ep_queue_send(queue, &second, 500) != EP_OK) {
                    return 20;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 21;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_OK) {
                    return 22;
                }

                if (received.id != second.id || received.value != second.value) {
                    return 23;
                }

                if (ep_queue_create(&queue, sizeof(int), 1) != EP_OK) {
                    return 24;
                }

                if (ep_queue_send(queue, &scalar, 0) != EP_OK) {
                    return 25;
                }

                scalar = 0;
                if (ep_queue_recv(queue, &scalar, 0) != EP_OK) {
                    return 26;
                }

                if (scalar != 42) {
                    return 27;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
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
