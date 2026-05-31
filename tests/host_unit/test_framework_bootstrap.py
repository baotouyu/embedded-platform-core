import shutil
import subprocess
from pathlib import Path


COMPILER = shutil.which("clang") or shutil.which("cc")


def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    cmake = Path("core/CMakeLists.txt").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int ep_framework_start(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
    assert "int ep_framework_start(void)" in source
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PUBLIC\n    ${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PRIVATE\n    ${CMAKE_SOURCE_DIR}/app/include" in cmake
    assert "PUBLIC\n    ${CMAKE_SOURCE_DIR}/app/include" not in cmake
    assert '#include "ep_log.h"' in source
    assert '#include "elog.h"' not in source
    assert '#include "ep_config.h"' in source
    assert '#include "ep_event.h"' in source
    assert '#include "ep_timer.h"' in source
    assert '#include "ep_osal_err.h"' in source
    assert "EP_FRAMEWORK_DEFAULT_CONFIG_PATH" in source
    assert '"config/profiles/host.cfg"' in source
    assert "static int ep_framework_load_default_config(void)" in source
    assert "ep_config_load_file(EP_FRAMEWORK_DEFAULT_CONFIG_PATH)" in source
    assert "int rc = ep_log_init();" in source
    assert "rc = ep_config_init();" in source
    assert "rc = ep_framework_load_default_config();" in source
    assert "if (rc == EP_ERR_UNSUPPORTED)" in source
    assert "rc = ep_event_init();" in source
    assert "return ep_event_init();" not in source
    assert "return ep_timer_init();" in source
    assert "EP_LOGI(" not in source
    assert "EP_LOGE(" not in source
    assert source.index("ep_log_init()") < source.index("ep_config_init()")
    assert source.index("ep_config_init()") < source.index("ep_framework_load_default_config()")
    assert source.index("ep_framework_load_default_config()") < source.index("ep_event_init()")
    assert source.index("ep_event_init()") < source.index("ep_timer_init()")
    assert "${CMAKE_SOURCE_DIR}/osal/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/log/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/config/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake


def test_framework_bootstrap_cmake_smoke(tmp_path):
    repo_root = Path(__file__).resolve().parents[2]
    build_dir = tmp_path / "build"

    configure = subprocess.run(
        ["cmake", "-S", str(repo_root), "-B", str(build_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert configure.returncode == 0, (
        f"cmake configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_core", "ep_app"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build.returncode == 0, (
        f"cmake build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )


def test_framework_init_loads_default_host_config(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_config_load_smoke.c"
    executable = tmp_path / "framework_config_load_smoke"

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_config.h"
        #include "ep_osal_err.h"

        #include <string.h>

        int app_main(void)
        {
            return 0;
        }

        int ep_platform_boot(void)
        {
            return 0;
        }

        int main(void)
        {
            const char *device_name;

            if (ep_framework_init() != EP_OK) {
                return 1;
            }

            if (ep_config_get_int("log.level", 0) != 3) {
                return 2;
            }

            if (ep_config_get_bool("feature.enabled", 0) != 1) {
                return 3;
            }

            device_name = ep_config_get_string("device.name", "missing");
            if (device_name == 0 || strcmp(device_name, "host") != 0) {
                return 4;
            }

            return 0;
        }
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    compile_result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(repo_root / "core/include"),
            "-I",
            str(repo_root / "app/include"),
            "-I",
            str(repo_root / "osal/include"),
            "-I",
            str(repo_root / "components/log/include"),
            "-I",
            str(repo_root / "components/config/include"),
            "-I",
            str(repo_root / "components/event/include"),
            "-I",
            str(repo_root / "components/timer/include"),
            "-I",
            str(repo_root / "components/file/include"),
            "-I",
            str(repo_root / "third_party/external/EasyLogger/easylogger/inc"),
            str(source),
            str(repo_root / "core/src/ep_framework.c"),
            str(repo_root / "components/log/src/ep_log.c"),
            str(repo_root / "components/config/src/ep_config.c"),
            str(repo_root / "components/event/src/ep_event.c"),
            str(repo_root / "components/timer/src/ep_timer.c"),
            str(repo_root / "components/file/src/ep_file.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/src/elog_utils.c"),
            str(repo_root / "third_party/external/EasyLogger/easylogger/port/elog_port.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(repo_root / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert compile_result.returncode == 0, compile_result.stderr

    run_result = subprocess.run(
        [str(executable)],
        capture_output=True,
        text=True,
        cwd=repo_root,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework config load smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
