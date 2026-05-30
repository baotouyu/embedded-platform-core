import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_log_component_and_easylogger_are_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    log_cmake_path = REPO_ROOT / "components/log/CMakeLists.txt"
    easylogger_root = REPO_ROOT / "third_party/external/EasyLogger"

    assert "add_subdirectory(components/log)" in root_cmake
    assert log_cmake_path.exists()

    log_cmake = log_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_log STATIC" in log_cmake
    assert "src/ep_log.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog_utils.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/port/elog_port.c" in log_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in log_cmake

    license_text = (easylogger_root / "LICENSE").read_text(encoding="utf-8")
    assert "The MIT License" in license_text
    assert "Copyright (c) 2015-2019 Armink" in license_text


def test_host_log_init_validation_and_output(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_log_smoke.c"
    executable = tmp_path / "host_log_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                if (ep_log_write(EP_LOG_LEVEL_INFO, "log", "before init") != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_log_init() != EP_OK) {
                    return 2;
                }

                if (ep_log_init() != EP_OK) {
                    return 3;
                }

                if (ep_log_write(EP_LOG_LEVEL_INFO, 0, "missing tag") != EP_ERR_INVAL) {
                    return 4;
                }

                if (ep_log_write(EP_LOG_LEVEL_INFO, "log", 0) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_log_write((ep_log_level_e)99, "log", "bad level") != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_log_write(EP_LOG_LEVEL_INFO, "host-log", "hello %s", "EasyLogger") != EP_OK) {
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
            str(REPO_ROOT / "components/log/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            "-I",
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(REPO_ROOT / "components/log/src/ep_log.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
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
    assert "host-log" in run_result.stdout
    assert "hello EasyLogger" in run_result.stdout


def test_host_posix_links_log_component():
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "ep_components_log" in host_cmake
