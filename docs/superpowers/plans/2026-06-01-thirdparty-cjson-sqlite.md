# cJSON 和 SQLite 第三方库接入实现计划

> 执行说明：按任务逐步实现，每一步用复选框记录状态。

**目标：** 把 cJSON 和 SQLite 作为第三方源码快照接入主工程，提供可链接的 CMake 静态库目标，并在 host/macOS 上通过 smoke 测试验证。

**架构：** 源码快照放在 `third_party/external/cjson` 和 `third_party/external/sqlite`。根 CMake 进入 `third_party/CMakeLists.txt`，由该文件导出 `ep_thirdparty_cjson` 和 `ep_thirdparty_sqlite` 两个目标；业务组件暂时不封装这两个库。

**技术栈：** C11、CMake、pytest、cJSON v1.7.19、SQLite 3.53.1 amalgamation。

---

## 文件结构

- 新增 `third_party/CMakeLists.txt`：统一管理第三方源码快照目标。
- 新增 `third_party/external/cjson/`：保存 cJSON v1.7.19 的 `cJSON.c`、`cJSON.h`、`LICENSE`、`VERSION.txt`。
- 新增 `third_party/external/sqlite/`：保存 SQLite 3.53.1 amalgamation 的 `sqlite3.c`、`sqlite3.h`、`sqlite3ext.h`、`LICENSE.md`、`VERSION.txt`。
- 修改 `CMakeLists.txt`：增加 `add_subdirectory(third_party)`。
- 新增 `tests/host_unit/test_thirdparty_cjson_sqlite.py`：验证文件、版本、CMake 目标和 smoke 程序。
- 修改 `docs/architecture/repository-layout.md`：说明 cJSON 和 SQLite 属于源码快照。
- 修改 `docs/architecture/project-overview.md`：同步第三方库现状。
- 修改 `docs/development/roadmap.md`：同步后续 JSON/SQLite 方向。

---

### 任务 1：写第三方库接入测试

**文件：**
- 新增：`tests/host_unit/test_thirdparty_cjson_sqlite.py`

- [x] **步骤 1：写失败测试**

写入以下测试代码：

```python
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
    source = tmp_path / "thirdparty_smoke.c"
    build_dir = tmp_path / "build"

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

    cmake_file = tmp_path / "CMakeLists.txt"
    cmake_file.write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(thirdparty_smoke C)

            add_subdirectory({REPO_ROOT.as_posix()} embedded-platform-core)

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
        ["cmake", "-S", str(tmp_path), "-B", str(build_dir)],
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
```

- [x] **步骤 2：运行测试确认失败**

运行：

```bash
pytest tests/host_unit/test_thirdparty_cjson_sqlite.py -v
```

预期：失败，因为源码目录、版本文件和 CMake 目标还不存在。

---

### 任务 2：同步官方源码快照

**文件：**
- 新增：`third_party/external/cjson/cJSON.c`
- 新增：`third_party/external/cjson/cJSON.h`
- 新增：`third_party/external/cjson/LICENSE`
- 新增：`third_party/external/cjson/VERSION.txt`
- 新增：`third_party/external/sqlite/sqlite3.c`
- 新增：`third_party/external/sqlite/sqlite3.h`
- 新增：`third_party/external/sqlite/sqlite3ext.h`
- 新增：`third_party/external/sqlite/LICENSE.md`
- 新增：`third_party/external/sqlite/VERSION.txt`

- [x] **步骤 1：下载 cJSON v1.7.19**

运行：

```bash
mkdir -p /tmp/ep-thirdparty-cjson
curl -L --fail --silent --show-error \
  https://github.com/DaveGamble/cJSON/archive/refs/tags/v1.7.19.tar.gz \
  -o /tmp/ep-thirdparty-cjson/cjson-v1.7.19.tar.gz
tar -xzf /tmp/ep-thirdparty-cjson/cjson-v1.7.19.tar.gz -C /tmp/ep-thirdparty-cjson
```

- [x] **步骤 2：复制 cJSON 源码文件**

运行：

```bash
mkdir -p third_party/external/cjson
cp /tmp/ep-thirdparty-cjson/cJSON-1.7.19/cJSON.c third_party/external/cjson/cJSON.c
cp /tmp/ep-thirdparty-cjson/cJSON-1.7.19/cJSON.h third_party/external/cjson/cJSON.h
cp /tmp/ep-thirdparty-cjson/cJSON-1.7.19/LICENSE third_party/external/cjson/LICENSE
```

- [x] **步骤 3：写 cJSON 版本记录**

创建 `third_party/external/cjson/VERSION.txt`：

```text
cJSON v1.7.19

来源：
https://github.com/DaveGamble/cJSON/releases/tag/v1.7.19
https://github.com/DaveGamble/cJSON/archive/refs/tags/v1.7.19.tar.gz

接入方式：
保留 cJSON.c、cJSON.h 和 LICENSE，作为源码快照由主工程 CMake 编译为 ep_thirdparty_cjson。
```

- [x] **步骤 4：下载 SQLite 3.53.1 amalgamation**

运行：

```bash
mkdir -p /tmp/ep-thirdparty-sqlite
curl -L --fail --silent --show-error \
  https://www.sqlite.org/2026/sqlite-amalgamation-3530100.zip \
  -o /tmp/ep-thirdparty-sqlite/sqlite-amalgamation-3530100.zip
unzip -q -o /tmp/ep-thirdparty-sqlite/sqlite-amalgamation-3530100.zip -d /tmp/ep-thirdparty-sqlite
```

- [x] **步骤 5：复制 SQLite 源码文件**

运行：

```bash
mkdir -p third_party/external/sqlite
cp /tmp/ep-thirdparty-sqlite/sqlite-amalgamation-3530100/sqlite3.c third_party/external/sqlite/sqlite3.c
cp /tmp/ep-thirdparty-sqlite/sqlite-amalgamation-3530100/sqlite3.h third_party/external/sqlite/sqlite3.h
cp /tmp/ep-thirdparty-sqlite/sqlite-amalgamation-3530100/sqlite3ext.h third_party/external/sqlite/sqlite3ext.h
```

- [x] **步骤 6：写 SQLite 声明和版本记录**

创建 `third_party/external/sqlite/LICENSE.md`：

```text
SQLite is in the public domain.

The SQLite source files in this directory are copied from the official SQLite
amalgamation package. See:
https://www.sqlite.org/copyright.html
```

创建 `third_party/external/sqlite/VERSION.txt`：

```text
SQLite 3.53.1

来源：
https://www.sqlite.org/download.html
https://www.sqlite.org/2026/sqlite-amalgamation-3530100.zip

接入方式：
保留 sqlite3.c、sqlite3.h、sqlite3ext.h 和 LICENSE.md，作为官方 amalgamation 源码快照由主工程 CMake 编译为 ep_thirdparty_sqlite。
```

---

### 任务 3：接入 CMake

**文件：**
- 新增：`third_party/CMakeLists.txt`
- 修改：`CMakeLists.txt`
- 测试：`tests/host_unit/test_thirdparty_cjson_sqlite.py`

- [x] **步骤 1：新增 third_party/CMakeLists.txt**

写入：

```cmake
add_library(ep_thirdparty_cjson STATIC
  external/cjson/cJSON.c
)

target_include_directories(ep_thirdparty_cjson
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/external/cjson
)

add_library(ep_thirdparty_sqlite STATIC
  external/sqlite/sqlite3.c
)

target_include_directories(ep_thirdparty_sqlite
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/external/sqlite
)
```

- [x] **步骤 2：根 CMake 增加 third_party**

在根 `CMakeLists.txt` 中，`add_subdirectory(platforms)` 后增加：

```cmake
add_subdirectory(third_party)
```

- [x] **步骤 3：运行第三方库测试**

运行：

```bash
pytest tests/host_unit/test_thirdparty_cjson_sqlite.py -v
```

预期：通过。

---

### 任务 4：同步中文文档

**文件：**
- 修改：`docs/architecture/repository-layout.md`
- 修改：`docs/architecture/project-overview.md`
- 修改：`docs/development/roadmap.md`
- 测试：`tests/host_unit/test_repository_layout.py`

- [x] **步骤 1：更新仓库目录说明**

在 `docs/architecture/repository-layout.md` 的第三方目录部分补充：

```text
当前源码快照包括 EasyLogger、cJSON 和 SQLite。cJSON 暴露为 `ep_thirdparty_cjson`，SQLite 暴露为 `ep_thirdparty_sqlite`。这两个目标只负责第三方库接入，不代表主工程已经有 JSON 组件或数据库组件。
```

- [x] **步骤 2：更新项目总览**

在 `docs/architecture/project-overview.md` 的第三方库部分补充：

```text
- cJSON v1.7.19 源码快照。
- SQLite 3.53.1 amalgamation 源码快照。
```

并补充说明：

```text
cJSON 和 SQLite 当前只作为第三方库目标接入，后续业务组件可以按需链接。
```

- [x] **步骤 3：更新路线图**

在 `docs/development/roadmap.md` 的业务组件方向补充：

```text
- cJSON 可用于菜谱 JSON、网络 JSON 和配置导入导出。
- SQLite 可用于用户数据、本地收藏、历史记录和状态缓存。
```

- [x] **步骤 4：运行文档测试**

运行：

```bash
pytest tests/host_unit/test_repository_layout.py -v
```

预期：通过。

---

### 任务 5：最终验证和提交

**文件：**
- 全部本次改动文件

- [x] **步骤 1：运行相关测试**

运行：

```bash
pytest tests/host_unit/test_thirdparty_cjson_sqlite.py tests/host_unit/test_repository_layout.py -v
```

预期：全部通过。

- [x] **步骤 2：运行全量 host/API 测试**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：全部通过。

- [x] **步骤 3：运行 CMake 构建**

运行：

```bash
cmake -S . -B build
cmake --build build --target ep_thirdparty_cjson ep_thirdparty_sqlite
```

预期：配置成功，两个第三方库目标构建成功。

- [ ] **步骤 4：提交实现**

运行：

```bash
git add CMakeLists.txt third_party/CMakeLists.txt third_party/external/cjson third_party/external/sqlite tests/host_unit/test_thirdparty_cjson_sqlite.py docs/architecture/repository-layout.md docs/architecture/project-overview.md docs/development/roadmap.md docs/superpowers/plans/2026-06-01-thirdparty-cjson-sqlite.md
git commit -m "feat: 接入cJSON和SQLite第三方库"
```

预期：生成中文提交。
