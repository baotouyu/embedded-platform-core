import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_event_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    event_cmake_path = REPO_ROOT / "components/event/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/event)" in root_cmake
    assert event_cmake_path.exists()

    event_cmake = event_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_event STATIC" in event_cmake
    assert "src/ep_event.c" in event_cmake
    assert "components/event/include" not in event_cmake
    assert "ep_components_event" in host_cmake


def test_host_event_bus_init_and_invalid_arguments(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_invalid_smoke.c"
    executable = tmp_path / "host_event_invalid_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"

            static void handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                unsigned char payload[65] = {0};

                if (ep_event_subscribe(1, handler, 0) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_event_publish(1, 0, 0, 0) != EP_ERR_UNSUPPORTED) {
                    return 2;
                }

                if (ep_event_init() != EP_OK) {
                    return 3;
                }

                if (ep_event_init() != EP_OK) {
                    return 4;
                }

                if (ep_event_subscribe(1, 0, 0) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_event_publish(1, 0, 1, 0) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_event_publish(1, payload, sizeof(payload), 0) != EP_ERR_INVAL) {
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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


def test_host_event_bus_subscription_capacity(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_capacity_smoke.c"
    executable = tmp_path / "host_event_capacity_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"

            static void handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                int i;

                if (ep_event_init() != EP_OK) {
                    return 1;
                }

                for (i = 0; i < 16; ++i) {
                    if (ep_event_subscribe(100 + i, handler, 0) != EP_OK) {
                        return 2;
                    }
                }

                if (ep_event_subscribe(200, handler, 0) != EP_ERR_BUSY) {
                    return 3;
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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


def test_host_event_bus_dispatches_published_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_dispatch_smoke.c"
    executable = tmp_path / "host_event_dispatch_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"

            #include <string.h>

            struct payload {
                int value;
                char label[8];
            };

            struct observed_state {
                volatile int call_count;
                volatile int second_call_count;
                ep_event_id_t event_id;
                size_t payload_size;
                int value;
                char label[8];
                int user_value;
            };

            static void first_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;
                const struct payload *body = (const struct payload *)payload;

                state->event_id = event_id;
                state->payload_size = payload_size;
                state->value = body->value;
                (void)memcpy(state->label, body->label, sizeof(state->label));
                state->user_value = 1234;
                state->call_count += 1;
            }

            static void second_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->second_call_count += 1;
            }

            static int wait_for_count(volatile int *value, int expected)
            {
                int i;

                for (i = 0; i < 100; ++i) {
                    if (*value == expected) {
                        return 0;
                    }
                    ep_sleep_ms(5);
                }

                return 1;
            }

            int main(void)
            {
                struct observed_state state;
                struct payload body;

                (void)memset(&state, 0, sizeof(state));
                body.value = 77;
                (void)memcpy(body.label, "kitchen", 8);

                if (ep_event_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(10, first_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_event_subscribe(10, second_handler, &state) != EP_OK) {
                    return 3;
                }

                if (ep_event_publish(99, &body, sizeof(body), 0) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(20);
                if (state.call_count != 0 || state.second_call_count != 0) {
                    return 5;
                }

                if (ep_event_publish(10, &body, sizeof(body), 100) != EP_OK) {
                    return 6;
                }

                if (wait_for_count(&state.call_count, 1) != 0) {
                    return 7;
                }

                if (wait_for_count(&state.second_call_count, 1) != 0) {
                    return 8;
                }

                if (state.event_id != 10) {
                    return 9;
                }

                if (state.payload_size != sizeof(body)) {
                    return 10;
                }

                if (state.value != 77) {
                    return 11;
                }

                if (memcmp(state.label, "kitchen", 8) != 0) {
                    return 12;
                }

                if (state.user_value != 1234) {
                    return 13;
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
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
