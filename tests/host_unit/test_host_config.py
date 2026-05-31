import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_config_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    config_cmake_path = REPO_ROOT / "components/config/CMakeLists.txt"

    assert "add_subdirectory(components/config)" in root_cmake
    assert config_cmake_path.exists()

    config_cmake = config_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_config STATIC" in config_cmake
    assert "src/ep_config.c" in config_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in config_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in config_cmake


def test_host_config_memory_store_validation_and_defaults(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_config_smoke.c"
    executable = tmp_path / "host_config_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_config.h"
            #include "ep_osal_err.h"

            #include <stdio.h>
            #include <string.h>

            int main(void)
            {
                const char *server;
                const char *fallback;
                char long_key[64];
                char long_value[128];
                char key[32];
                int i;

                if (ep_config_set_int("before.init", 1) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_config_get_int("before.init", 42) != 42) {
                    return 2;
                }

                if (ep_config_get_bool("before.init", 1) != 1) {
                    return 3;
                }

                fallback = ep_config_get_string("before.init", "fallback");
                if (fallback == 0 || strcmp(fallback, "fallback") != 0) {
                    return 4;
                }

                if (ep_config_init() != EP_OK) {
                    return 5;
                }

                if (ep_config_set_int("log.level", 3) != EP_OK) {
                    return 6;
                }

                if (ep_config_get_int("log.level", 0) != 3) {
                    return 7;
                }

                if (ep_config_set_bool("feature.enabled", 99) != EP_OK) {
                    return 8;
                }

                if (ep_config_get_bool("feature.enabled", 0) != 1) {
                    return 9;
                }

                if (ep_config_set_bool("feature.disabled", 0) != EP_OK) {
                    return 10;
                }

                if (ep_config_get_bool("feature.disabled", 1) != 0) {
                    return 11;
                }

                if (ep_config_set_string("network.server", "127.0.0.1") != EP_OK) {
                    return 12;
                }

                server = ep_config_get_string("network.server", "missing");
                if (server == 0 || strcmp(server, "127.0.0.1") != 0) {
                    return 13;
                }

                if (ep_config_get_int("missing.int", 55) != 55) {
                    return 14;
                }

                if (ep_config_get_bool("missing.bool", 0) != 0) {
                    return 15;
                }

                fallback = ep_config_get_string("missing.string", "default");
                if (fallback == 0 || strcmp(fallback, "default") != 0) {
                    return 16;
                }

                if (ep_config_get_bool("log.level", 0) != 0) {
                    return 17;
                }

                if (ep_config_get_int("network.server", 77) != 77) {
                    return 18;
                }

                if (ep_config_set_int("", 1) != EP_ERR_INVAL) {
                    return 19;
                }

                if (ep_config_set_int(0, 1) != EP_ERR_INVAL) {
                    return 20;
                }

                if (ep_config_set_string("bad.null", 0) != EP_ERR_INVAL) {
                    return 21;
                }

                memset(long_key, 'k', sizeof(long_key));
                long_key[sizeof(long_key) - 1u] = '\\0';
                if (ep_config_set_int(long_key, 1) != EP_ERR_INVAL) {
                    return 22;
                }

                memset(long_value, 'v', sizeof(long_value));
                long_value[sizeof(long_value) - 1u] = '\\0';
                if (ep_config_set_string("bad.long.value", long_value) != EP_ERR_INVAL) {
                    return 23;
                }

                if (ep_config_init() != EP_OK) {
                    return 24;
                }

                if (ep_config_get_int("log.level", 0) != 3) {
                    return 25;
                }

                for (i = 0; i < 28; ++i) {
                    (void)snprintf(key, sizeof(key), "capacity.%02d", i);
                    if (ep_config_set_int(key, i) != EP_OK) {
                        return 30 + i;
                    }
                }

                if (ep_config_set_int("capacity.extra", 100) != EP_ERR_BUSY) {
                    return 80;
                }

                if (ep_config_set_int("log.level", 4) != EP_OK) {
                    return 81;
                }

                if (ep_config_get_int("log.level", 0) != 4) {
                    return 82;
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
            str(REPO_ROOT / "components/config/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/config/src/ep_config.c"),
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

    assert run_result.returncode == 0, (
        f"config smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
