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
    assert root_cmake.index("add_subdirectory(components/file)") < root_cmake.index(
        "add_subdirectory(components/config)"
    )
    assert config_cmake_path.exists()

    config_cmake = config_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_config STATIC" in config_cmake
    assert "src/ep_config.c" in config_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in config_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in config_cmake
    assert "${CMAKE_SOURCE_DIR}/components/file/include" in config_cmake
    assert "target_link_libraries(ep_components_config" in config_cmake
    assert "ep_components_file" in config_cmake


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
            str(REPO_ROOT / "components/file/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/config/src/ep_config.c"),
            str(REPO_ROOT / "components/file/src/ep_file.c"),
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


def test_host_config_load_file_success_and_overrides(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    config_path = tmp_path / "default.cfg"
    override_path = tmp_path / "override.cfg"
    source = tmp_path / "host_config_file_success.c"
    executable = tmp_path / "host_config_file_success"

    config_path.write_text(
        "\n".join(
            [
                "int log.level=3",
                "bool feature.enabled=true",
                "bool feature.disabled=false",
                "string network.server=127.0.0.1",
                "int duplicate.value=1",
                "int duplicate.value=2",
            ]
        ),
        encoding="utf-8",
    )
    override_path.write_text(
        "\n".join(
            [
                "int log.level=5",
                "string device.name=demo_board",
            ]
        ),
        encoding="utf-8",
    )

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_config.h"
            #include "ep_osal_err.h"

            #include <string.h>

            int main(int argc, char **argv)
            {
                const char *server;
                const char *device_name;

                if (argc != 3) {
                    return 1;
                }

                if (ep_config_init() != EP_OK) {
                    return 2;
                }

                if (ep_config_load_file(argv[1]) != EP_OK) {
                    return 3;
                }

                if (ep_config_get_int("log.level", 0) != 3) {
                    return 4;
                }

                if (ep_config_get_bool("feature.enabled", 0) != 1) {
                    return 5;
                }

                if (ep_config_get_bool("feature.disabled", 1) != 0) {
                    return 6;
                }

                server = ep_config_get_string("network.server", "missing");
                if (server == 0 || strcmp(server, "127.0.0.1") != 0) {
                    return 7;
                }

                if (ep_config_get_int("duplicate.value", 0) != 2) {
                    return 8;
                }

                if (ep_config_load_file(argv[2]) != EP_OK) {
                    return 9;
                }

                if (ep_config_get_int("log.level", 0) != 5) {
                    return 10;
                }

                if (ep_config_get_bool("feature.enabled", 0) != 1) {
                    return 11;
                }

                device_name = ep_config_get_string("device.name", "missing");
                if (device_name == 0 || strcmp(device_name, "demo_board") != 0) {
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
            str(REPO_ROOT / "components/config/include"),
            "-I",
            str(REPO_ROOT / "components/file/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/config/src/ep_config.c"),
            str(REPO_ROOT / "components/file/src/ep_file.c"),
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
        [str(executable), str(config_path), str(override_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"config file success smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )


def test_host_config_load_file_errors(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    missing_path = tmp_path / "missing.cfg"
    bad_format_path = tmp_path / "bad_format.cfg"
    unknown_type_path = tmp_path / "unknown_type.cfg"
    bad_bool_path = tmp_path / "bad_bool.cfg"
    bad_int_path = tmp_path / "bad_int.cfg"
    empty_value_path = tmp_path / "empty_value.cfg"
    empty_file_path = tmp_path / "empty.cfg"
    long_line_path = tmp_path / "long_line.cfg"
    oversized_file_path = tmp_path / "oversized.cfg"
    partial_path = tmp_path / "partial.cfg"
    source = tmp_path / "host_config_file_errors.c"
    executable = tmp_path / "host_config_file_errors"

    bad_format_path.write_text("int log.level\n", encoding="utf-8")
    unknown_type_path.write_text("float ratio=1\n", encoding="utf-8")
    bad_bool_path.write_text("bool feature.enabled=1\n", encoding="utf-8")
    bad_int_path.write_text("int log.level=3x\n", encoding="utf-8")
    empty_value_path.write_text("string device.name=\n", encoding="utf-8")
    empty_file_path.write_text("", encoding="utf-8")
    long_line_path.write_text("string long.value=" + ("x" * 128) + "\n", encoding="utf-8")
    oversized_file_path.write_text("string item=value\n" * 80, encoding="utf-8")
    partial_path.write_text("int partial.good=7\nbadline\n", encoding="utf-8")

    source.write_text(
        textwrap.dedent(
            """
            #include "ep_config.h"
            #include "ep_osal_err.h"

            int main(int argc, char **argv)
            {
                if (argc != 11) {
                    return 1;
                }

                if (ep_config_load_file(argv[1]) != EP_ERR_UNSUPPORTED) {
                    return 2;
                }

                if (ep_config_init() != EP_OK) {
                    return 3;
                }

                if (ep_config_load_file(0) != EP_ERR_INVAL) {
                    return 4;
                }

                if (ep_config_load_file("") != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_config_load_file(argv[1]) != EP_ERR_UNSUPPORTED) {
                    return 6;
                }

                if (ep_config_load_file(argv[2]) != EP_ERR_INVAL) {
                    return 7;
                }

                if (ep_config_load_file(argv[3]) != EP_ERR_INVAL) {
                    return 8;
                }

                if (ep_config_load_file(argv[4]) != EP_ERR_INVAL) {
                    return 9;
                }

                if (ep_config_load_file(argv[5]) != EP_ERR_INVAL) {
                    return 10;
                }

                if (ep_config_load_file(argv[6]) != EP_ERR_INVAL) {
                    return 11;
                }

                if (ep_config_load_file(argv[7]) != EP_ERR_INVAL) {
                    return 12;
                }

                if (ep_config_load_file(argv[8]) != EP_ERR_INVAL) {
                    return 13;
                }

                if (ep_config_load_file(argv[9]) != EP_ERR_BUSY) {
                    return 14;
                }

                if (ep_config_load_file(argv[10]) != EP_ERR_INVAL) {
                    return 15;
                }

                if (ep_config_get_int("partial.good", 0) != 7) {
                    return 16;
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
            str(REPO_ROOT / "components/file/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/config/src/ep_config.c"),
            str(REPO_ROOT / "components/file/src/ep_file.c"),
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
        [
            str(executable),
            str(missing_path),
            str(bad_format_path),
            str(unknown_type_path),
            str(bad_bool_path),
            str(bad_int_path),
            str(empty_value_path),
            str(empty_file_path),
            str(long_line_path),
            str(oversized_file_path),
            str(partial_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"config file error smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
