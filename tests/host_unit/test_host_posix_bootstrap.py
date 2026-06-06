import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_posix_package_shape_exists():
    expected_paths = [
        "platforms/host/posix/CMakeLists.txt",
        "platforms/host/posix/startup/main.c",
        "platforms/host/posix/osal_port/ep_host_osal_stub.c",
        "platforms/host/posix/hal_port/ep_host_hal_stub.c",
        "platforms/host/posix/component_port/ep_host_component_stub.c",
        "platforms/host/posix/config/host_posix.cmake",
    ]

    missing = [path for path in expected_paths if not (REPO_ROOT / path).exists()]
    assert not missing, f"Missing host POSIX paths: {missing}"


def test_host_posix_cmake_target_is_named():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_executable(ep_platform_host_posix" in cmake
    assert "target_link_libraries(ep_platform_host_posix" in cmake
    assert "ep_core" in cmake
    assert "ep_app" in cmake


def test_app_lifecycle_uses_framework_services_without_platform_headers():
    app_events = REPO_ROOT / "app/include/app_events.h"
    app_main = REPO_ROOT / "app/main.c"
    app_selftest = REPO_ROOT / "app/selftest/app_selftest.c"
    app_core = REPO_ROOT / "app/app_core.c"
    app_cmake = REPO_ROOT / "app/CMakeLists.txt"

    assert app_events.exists()

    events_header = app_events.read_text(encoding="utf-8")
    source = app_main.read_text(encoding="utf-8")
    selftest_source = app_selftest.read_text(encoding="utf-8")
    core_source = app_core.read_text(encoding="utf-8")
    cmake = app_cmake.read_text(encoding="utf-8")

    assert "APP_EVENT_TIMER_DONE" in events_header
    assert "#define APP_EVENT_TIMER_DONE 1000" in events_header

    assert '#include "app_core.h"' in source
    assert '#include "app_main.h"' in source
    assert '#include "app_selftest.h"' in source
    assert "app_core_start(&app)" in source
    assert "app_selftest_run(&app)" in source
    assert "app_core_run(&app)" in source

    forbidden_headers = [
        "<pthread.h>",
        "<signal.h>",
        "<unistd.h>",
        "\"pthread.h\"",
        "\"signal.h\"",
        "\"unistd.h\"",
    ]
    for header in forbidden_headers:
        assert header not in source
        assert header not in selftest_source
        assert header not in core_source

    assert "APP_TIMER_ID_SELF_TEST" in selftest_source
    assert "APP_TIMER_TIMEOUT_MS" in selftest_source
    assert "APP_WAIT_STEP_MS" in selftest_source
    assert "APP_WAIT_TIMEOUT_MS" in selftest_source
    assert "static volatile int g_app_timer_done;" in selftest_source
    assert "static void app_timer_done_handler(" in selftest_source
    assert "ep_event_subscribe(APP_EVENT_TIMER_DONE, app_timer_done_handler, 0)" in selftest_source
    assert "ep_timer_start(APP_TIMER_ID_SELF_TEST, APP_TIMER_TIMEOUT_MS, APP_EVENT_TIMER_DONE)" in selftest_source
    assert "ep_sleep_ms(APP_WAIT_STEP_MS)" in selftest_source
    assert "return EP_ERR_TIMEOUT;" in selftest_source
    assert "EP_LOGI(\"app\", \"app lifecycle start\")" in core_source
    assert "EP_LOGI(\"app\", \"app lifecycle done\")" in core_source
    assert "EP_LOGE(\"app\", \"app lifecycle timeout\")" in selftest_source

    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/selftest" in cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/services" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/log/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in cmake
    assert "ep_components_log" in cmake
    assert "ep_components_event" in cmake
    assert "ep_components_timer" in cmake


def test_host_posix_executable_runs_successfully(tmp_path):
    build_dir = tmp_path / "host-posix-build"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_platform_host_posix"],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    executable = build_dir / "platforms/host/posix/ep_platform_host_posix"
    run = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run.returncode == 0, (
        f"host executable failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
    assert "app lifecycle start" in run.stdout
    assert "app lifecycle done" in run.stdout
    assert "app lifecycle timeout" not in run.stdout
