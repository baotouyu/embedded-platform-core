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


def test_host_timer_publishes_event_when_expired(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_expire_smoke.c"
    executable = tmp_path / "host_timer_expire_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int call_count;
                ep_event_id_t event_id;
                size_t payload_size;
            };

            static void timer_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)payload;
                state->event_id = event_id;
                state->payload_size = payload_size;
                state->call_count += 1;
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

                state.call_count = 0;
                state.event_id = 0;
                state.payload_size = 99;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(500, timer_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_timer_start(1, 20, 500) != EP_OK) {
                    return 3;
                }

                if (wait_for_count(&state.call_count, 1) != 0) {
                    return 4;
                }

                if (state.event_id != 500) {
                    return 5;
                }

                if (state.payload_size != 0) {
                    return 6;
                }

                ep_sleep_ms(60);
                if (state.call_count != 1) {
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


def test_host_timer_stop_prevents_pending_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_stop_smoke.c"
    executable = tmp_path / "host_timer_stop_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int call_count;
            };

            static void timer_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->call_count += 1;
            }

            int main(void)
            {
                struct observed_state state;

                state.call_count = 0;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(510, timer_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_timer_start(2, 80, 510) != EP_OK) {
                    return 3;
                }

                if (ep_timer_stop(2) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(140);
                if (state.call_count != 0) {
                    return 5;
                }

                if (ep_timer_stop(2) != EP_ERR_INVAL) {
                    return 6;
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


def test_host_timer_restart_same_id_updates_deadline_and_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_restart_smoke.c"
    executable = tmp_path / "host_timer_restart_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int first_count;
                volatile int second_count;
            };

            static void first_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->first_count += 1;
            }

            static void second_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->second_count += 1;
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

                state.first_count = 0;
                state.second_count = 0;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(520, first_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_event_subscribe(521, second_handler, &state) != EP_OK) {
                    return 3;
                }

                if (ep_timer_start(3, 120, 520) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(20);

                if (ep_timer_start(3, 20, 521) != EP_OK) {
                    return 5;
                }

                if (wait_for_count(&state.second_count, 1) != 0) {
                    return 6;
                }

                ep_sleep_ms(140);
                if (state.first_count != 0) {
                    return 7;
                }

                if (state.second_count != 1) {
                    return 8;
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


def test_host_timer_capacity_limit(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_capacity_smoke.c"
    executable = tmp_path / "host_timer_capacity_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_timer.h"

            int main(void)
            {
                int i;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                for (i = 0; i < 16; ++i) {
                    if (ep_timer_start(i, 10000, 600 + i) != EP_OK) {
                        return 2;
                    }
                }

                if (ep_timer_start(99, 10000, 700) != EP_ERR_BUSY) {
                    return 3;
                }

                if (ep_timer_start(0, 10000, 800) != EP_OK) {
                    return 4;
                }

                if (ep_timer_stop(0) != EP_OK) {
                    return 5;
                }

                if (ep_timer_start(99, 10000, 700) != EP_OK) {
                    return 6;
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
