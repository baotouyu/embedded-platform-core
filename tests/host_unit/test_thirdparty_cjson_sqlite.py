import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_thirdparty_cjson_and_sqlite_files_are_present():
    required_files = [
        "third_party/external/cjson/cJSON.c",
        "third_party/external/cjson/cJSON.h",
        "third_party/external/cjson/LICENSE",
        "third_party/external/cjson/VERSION.txt",
        "third_party/external/sqlite/sqlite3.c",
        "third_party/external/sqlite/sqlite3.h",
        "third_party/external/sqlite/sqlite3ext.h",
        "third_party/external/sqlite/LICENSE.md",
        "third_party/external/sqlite/VERSION.txt",
    ]

    missing_files = [
        path for path in required_files if not (REPO_ROOT / path).is_file()
    ]

    assert not missing_files, "Missing third-party files: " + ", ".join(missing_files)


def test_thirdparty_versions_are_documented():
    cjson_version = (REPO_ROOT / "third_party/external/cjson/VERSION.txt").read_text(
        encoding="utf-8"
    )
    sqlite_version = (REPO_ROOT / "third_party/external/sqlite/VERSION.txt").read_text(
        encoding="utf-8"
    )

    assert "cJSON v1.7.19" in cjson_version
    assert "https://github.com/DaveGamble/cJSON/releases/tag/v1.7.19" in cjson_version
    assert "SQLite 3.53.1" in sqlite_version
    assert "sqlite-amalgamation-3530100.zip" in sqlite_version
    assert "https://www.sqlite.org/2026/sqlite-amalgamation-3530100.zip" in sqlite_version


def test_thirdparty_cmake_targets_are_declared():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    third_party_cmake = (REPO_ROOT / "third_party/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(third_party)" in root_cmake
    assert "add_library(ep_thirdparty_cjson STATIC" in third_party_cmake
    assert "external/cjson/cJSON.c" in third_party_cmake
    assert "add_library(ep_thirdparty_sqlite STATIC" in third_party_cmake
    assert "external/sqlite/sqlite3.c" in third_party_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/external/cjson" in third_party_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/external/sqlite" in third_party_cmake


def test_thirdparty_cjson_and_sqlite_can_link_and_run(tmp_path):
    smoke_dir = REPO_ROOT / "build/thirdparty_smoke"
    source = smoke_dir / "thirdparty_smoke.c"
    build_dir = smoke_dir / "build"
    smoke_dir.mkdir(parents=True, exist_ok=True)

    source.write_text(
        textwrap.dedent(
            """
            #include "cJSON.h"
            #include "sqlite3.h"

            #include <string.h>

            int main(void)
            {
                cJSON *root = cJSON_Parse("{\\"name\\":\\"host\\"}");
                cJSON *name = 0;
                sqlite3 *db = 0;
                char *errmsg = 0;
                int rc;

                if (root == 0) {
                    return 1;
                }

                name = cJSON_GetObjectItemCaseSensitive(root, "name");
                if (!cJSON_IsString(name) || strcmp(name->valuestring, "host") != 0) {
                    cJSON_Delete(root);
                    return 2;
                }

                cJSON_Delete(root);

                rc = sqlite3_open(":memory:", &db);
                if (rc != SQLITE_OK) {
                    return 3;
                }

                rc = sqlite3_exec(db, "create table t(id integer);", 0, 0, &errmsg);
                if (rc != SQLITE_OK) {
                    sqlite3_free(errmsg);
                    sqlite3_close(db);
                    return 4;
                }

                sqlite3_close(db);
                return 0;
            }
            """
        ).strip()
        + "\n"
    )

    cmake_file = smoke_dir / "CMakeLists.txt"
    cmake_file.write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(thirdparty_smoke C)

            add_subdirectory({(REPO_ROOT / "third_party").as_posix()} third_party)

            add_executable(thirdparty_smoke {source.as_posix()})
            target_link_libraries(thirdparty_smoke
              PRIVATE
                ep_thirdparty_cjson
                ep_thirdparty_sqlite
            )
            """
        ).strip()
        + "\n"
    )

    configure_result = subprocess.run(
        ["cmake", "-S", str(smoke_dir), "-B", str(build_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert configure_result.returncode == 0, (
        f"stdout:\n{configure_result.stdout}\nstderr:\n{configure_result.stderr}"
    )

    build_result = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "thirdparty_smoke"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert build_result.returncode == 0, (
        f"stdout:\n{build_result.stdout}\nstderr:\n{build_result.stderr}"
    )

    run_result = subprocess.run(
        [str(build_dir / "thirdparty_smoke")],
        capture_output=True,
        text=True,
        check=False,
    )
    assert run_result.returncode == 0, (
        f"stdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
