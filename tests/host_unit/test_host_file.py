import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_file_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    file_cmake_path = REPO_ROOT / "components/file/CMakeLists.txt"

    assert "add_subdirectory(components/file)" in root_cmake
    assert file_cmake_path.exists()

    file_cmake = file_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_file STATIC" in file_cmake
    assert "src/ep_file.c" in file_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in file_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in file_cmake


def test_host_file_read_write_append_truncate_and_errors(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    data_path = tmp_path / "ep_file_smoke.txt"
    missing_path = tmp_path / "missing.txt"
    source = tmp_path / "host_file_smoke.c"
    executable = tmp_path / "host_file_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_file.h"
            #include "ep_osal_err.h"

            #include <string.h>

            int main(int argc, char **argv)
            {
                ep_file_t *file = 0;
                ep_file_t *missing = 0;
                char buffer[32];
                size_t count = 99u;
                const char *path;
                const char *missing_path;

                if (argc != 3) {
                    return 1;
                }

                path = argv[1];
                missing_path = argv[2];

                if (ep_file_open(0, path, EP_FILE_MODE_READ) != EP_ERR_INVAL) {
                    return 2;
                }

                if (ep_file_open(&file, 0, EP_FILE_MODE_READ) != EP_ERR_INVAL) {
                    return 3;
                }

                if (ep_file_open(&file, "", EP_FILE_MODE_READ) != EP_ERR_INVAL) {
                    return 4;
                }

                if (ep_file_open(&file, path, 0) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_CREATE) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_READ | EP_FILE_MODE_APPEND) != EP_ERR_INVAL) {
                    return 7;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_APPEND | EP_FILE_MODE_TRUNCATE) != EP_ERR_INVAL) {
                    return 8;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_READ | (1 << 9)) != EP_ERR_INVAL) {
                    return 9;
                }

                if (ep_file_open(&missing, missing_path, EP_FILE_MODE_READ) != EP_ERR_UNSUPPORTED) {
                    return 10;
                }

                if (missing != 0) {
                    return 11;
                }

                if (ep_file_read(0, buffer, sizeof(buffer), &count) != EP_ERR_INVAL) {
                    return 12;
                }

                count = 99u;
                if (ep_file_read(file, 0, 1u, &count) != EP_ERR_INVAL) {
                    return 13;
                }

                if (count != 0u) {
                    return 14;
                }

                count = 99u;
                if (ep_file_write(0, "x", 1u, &count) != EP_ERR_INVAL) {
                    return 15;
                }

                count = 99u;
                if (ep_file_write(file, 0, 1u, &count) != EP_ERR_INVAL) {
                    return 16;
                }

                if (count != 0u) {
                    return 17;
                }

                if (ep_file_close(0) != EP_ERR_INVAL) {
                    return 18;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE) != EP_OK) {
                    return 19;
                }

                if (file == 0) {
                    return 20;
                }

                count = 99u;
                if (ep_file_write(file, "hello", 5u, &count) != EP_OK) {
                    return 21;
                }

                if (count != 5u) {
                    return 22;
                }

                if (ep_file_write(file, "", 0u, &count) != EP_OK) {
                    return 23;
                }

                if (count != 0u) {
                    return 24;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 25;
                }

                file = 0;
                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_APPEND) != EP_OK) {
                    return 26;
                }

                if (ep_file_write(file, " world", 6u, 0) != EP_OK) {
                    return 27;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 28;
                }

                file = 0;
                memset(buffer, 0, sizeof(buffer));
                if (ep_file_open(&file, path, EP_FILE_MODE_READ) != EP_OK) {
                    return 29;
                }

                count = 99u;
                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 30;
                }

                if (count != 11u || strcmp(buffer, "hello world") != 0) {
                    return 31;
                }

                count = 99u;
                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 32;
                }

                if (count != 0u) {
                    return 33;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 34;
                }

                file = 0;
                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE) != EP_OK) {
                    return 35;
                }

                if (ep_file_write(file, "new", 3u, &count) != EP_OK) {
                    return 36;
                }

                if (count != 3u) {
                    return 37;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 38;
                }

                file = 0;
                memset(buffer, 0, sizeof(buffer));
                if (ep_file_open(&file, path, EP_FILE_MODE_READ) != EP_OK) {
                    return 39;
                }

                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 40;
                }

                if (count != 3u || strcmp(buffer, "new") != 0) {
                    return 41;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 42;
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
            str(REPO_ROOT / "components/file/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
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
        [str(executable), str(data_path), str(missing_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"file smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
