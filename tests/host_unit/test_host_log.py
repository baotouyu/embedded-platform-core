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
    easylogger_cfg = easylogger_root / "easylogger/inc/elog_cfg.h"

    assert "add_subdirectory(components/log)" in root_cmake
    assert log_cmake_path.exists()

    log_cmake = log_cmake_path.read_text(encoding="utf-8")
    elog_cfg = easylogger_cfg.read_text(encoding="utf-8")
    assert "add_library(ep_components_log STATIC" in log_cmake
    assert "src/ep_log.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog_utils.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/port/elog_port.c" in log_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in log_cmake
    assert "#define ELOG_COLOR_ENABLE" in elog_cfg

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


def test_host_log_level_filtering_and_validation(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_log_level_smoke.c"
    executable = tmp_path / "host_log_level_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                if (ep_log_get_level() != EP_LOG_LEVEL_INFO) {
                    return 1;
                }

                if (ep_log_set_level(EP_LOG_LEVEL_WARN) != EP_OK) {
                    return 2;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 3;
                }

                if (ep_log_set_level((ep_log_level_e)-1) != EP_ERR_INVAL) {
                    return 4;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 5;
                }

                if (ep_log_set_level((ep_log_level_e)6) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 7;
                }

                if (ep_log_init() != EP_OK) {
                    return 8;
                }

                if (ep_log_write(EP_LOG_LEVEL_INFO, "level-filter", "info hidden") != EP_OK) {
                    return 9;
                }

                if (ep_log_write(EP_LOG_LEVEL_ERROR, "level-filter", "error visible") != EP_OK) {
                    return 10;
                }

                if (ep_log_set_level(EP_LOG_LEVEL_VERBOSE) != EP_OK) {
                    return 11;
                }

                if (ep_log_write(EP_LOG_LEVEL_DEBUG, "level-filter", "debug visible") != EP_OK) {
                    return 12;
                }

                if (ep_log_write((ep_log_level_e)99, "level-filter", "bad level") != EP_ERR_INVAL) {
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
    assert "info hidden" not in run_result.stdout
    assert "error visible" in run_result.stdout
    assert "debug visible" in run_result.stdout


def test_easylogger_port_uses_rtthread_console_for_luban_lite(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "rtthread_elog_port_smoke.c"
    executable = tmp_path / "rtthread_elog_port_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include <stddef.h>
            #include <stdint.h>
            #include <stdarg.h>

            typedef struct ep_mutex ep_mutex_t;

            int ep_mutex_create(ep_mutex_t **mutex)
            {
                *mutex = 0;
                return 0;
            }

            int ep_mutex_lock(ep_mutex_t *mutex)
            {
                (void)mutex;
                return 0;
            }

            int ep_mutex_unlock(ep_mutex_t *mutex)
            {
                (void)mutex;
                return 0;
            }

            uint64_t ep_time_now_ms(void)
            {
                return 1234u;
            }

            static char g_console[128];
            static unsigned int g_console_len;

            int rt_kprintf(const char *fmt, ...)
            {
                va_list args;
                const char *src = fmt;

                va_start(args, fmt);
                if (fmt[0] == '%' && fmt[1] == 's' && fmt[2] == '\\0') {
                    src = va_arg(args, const char *);
                }

                while (*src != '\\0' && g_console_len < sizeof(g_console) - 1u) {
                    g_console[g_console_len++] = *src++;
                }
                g_console[g_console_len] = '\\0';
                va_end(args);
                return (int)g_console_len;
            }

            void elog_port_output(const char *log, size_t size);

            int main(void)
            {
                elog_port_output("ep rtthread log\\n", 16u);
                return (g_console[0] == 'e' && g_console[15] == '\\n') ? 0 : 1;
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    rtthread_include = tmp_path / "rtthread.h"
    rtthread_include.write_text(
        "int rt_kprintf(const char *fmt, ...);\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-DRT_USING_CONSOLE",
            "-I",
            str(tmp_path),
            "-I",
            str(REPO_ROOT / "osal/include"),
            "-I",
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(REPO_ROOT / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
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


def test_host_posix_links_log_component():
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "ep_components_log" in host_cmake
