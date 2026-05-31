# File Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现第一版 `components/file` 文件读写组件，提供平台无关 `ep_file_open/read/write/close` API，并在 Mac/Ubuntu host 上验证写、读、追加、截断和错误路径。

**Architecture:** `components/file` 暴露 `ep_file.h`，公共头文件只包含 `stddef.h` 和不透明 `ep_file_t`。第一版实现内部使用 C 标准库 `fopen/fread/fwrite/fclose`，但不向上层暴露 `FILE *`；后续 Luban-Lite/RT-Thread 可替换内部实现而不改上层 API。

**Tech Stack:** C11、CMake、C 标准库 stdio、`ep_osal_err.h`、pytest、host POSIX 编译运行烟测。

---

## 文件结构

- Create: `tests/api_contract/test_file_headers.py`
  - 验证 `ep_file.h` 平台无关、可独立编译、接口签名稳定。
- Create: `components/file/include/ep_file.h`
  - file 公共 API，只暴露不透明句柄、打开模式和读写函数。
- Create: `tests/host_unit/test_host_file.py`
  - 验证 CMake 接入和 host 文件读写行为。
- Create: `components/file/CMakeLists.txt`
  - 构建 `ep_components_file` 静态库。
- Create: `components/file/src/ep_file.c`
  - 第一版 file 实现，内部使用 stdio。
- Modify: `CMakeLists.txt`
  - 增加 `add_subdirectory(components/file)`，放在 config 后面。

## Task 1: 锁定 file 公共头文件契约

**Files:**
- Create: `tests/api_contract/test_file_headers.py`
- Create: `components/file/include/ep_file.h`

- [ ] **Step 1: 写失败测试**

创建 `tests/api_contract/test_file_headers.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
FILE_INCLUDE = REPO_ROOT / "components" / "file" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_file_header_is_platform_neutral():
    header = FILE_INCLUDE / "ep_file.h"

    assert header.exists(), "Expected components/file/include/ep_file.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "FILE *",
        "FILE*",
        "typedef FILE",
        "stdio.h",
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "fcntl.h",
        "sys/",
        "platforms/",
        "third_party/",
        "flash",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_file.h must stay platform-neutral, found: {found}"


def test_file_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "file_header_smoke.c"
    obj = tmp_path / "file_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_file.h"
            #include "ep_file.h"

            int main(void)
            {
                ep_file_t *file = 0;
                int mode = EP_FILE_MODE_READ | EP_FILE_MODE_WRITE |
                           EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE |
                           EP_FILE_MODE_APPEND;
                int (*open_fn)(ep_file_t **, const char *, int) = ep_file_open;
                int (*read_fn)(ep_file_t *, void *, size_t, size_t *) = ep_file_read;
                int (*write_fn)(ep_file_t *, const void *, size_t, size_t *) = ep_file_write;
                int (*close_fn)(ep_file_t *) = ep_file_close;

                return (file == 0 && mode != 0 && open_fn && read_fn && write_fn && close_fn) ? 0 : 1;
            }
            """
        ).strip()
        + "\n"
    )

    result = subprocess.run(
        [
            COMPILER,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-I",
            str(FILE_INCLUDE),
            "-c",
            str(source),
            "-o",
            str(obj),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )

    assert result.returncode == 0, result.stderr
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/api_contract/test_file_headers.py -v
```

Expected:

```text
FAILED tests/api_contract/test_file_headers.py::test_file_header_is_platform_neutral
Expected components/file/include/ep_file.h to exist
```

- [ ] **Step 3: 创建公共头文件**

创建目录：

```bash
mkdir -p components/file/include
```

创建 `components/file/include/ep_file.h`：

```c
#ifndef EP_FILE_H
#define EP_FILE_H

#include <stddef.h>

#define EP_FILE_MODE_READ (1 << 0)
#define EP_FILE_MODE_WRITE (1 << 1)
#define EP_FILE_MODE_CREATE (1 << 2)
#define EP_FILE_MODE_TRUNCATE (1 << 3)
#define EP_FILE_MODE_APPEND (1 << 4)

typedef struct ep_file ep_file_t;

int ep_file_open(ep_file_t **file, const char *path, int mode);
int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read);
int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written);
int ep_file_close(ep_file_t *file);

#endif
```

- [ ] **Step 4: 运行测试确认通过**

Run:

```bash
pytest tests/api_contract/test_file_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交公共接口契约**

```bash
git add tests/api_contract/test_file_headers.py components/file/include/ep_file.h
git commit -m "test: 增加 file 公共接口契约"
```

## Task 2: 建立 file 组件 CMake 骨架

**Files:**
- Create: `tests/host_unit/test_host_file.py`
- Create: `components/file/CMakeLists.txt`
- Create: `components/file/src/ep_file.c`
- Modify: `CMakeLists.txt`

- [ ] **Step 1: 写失败测试**

创建 `tests/host_unit/test_host_file.py`：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_host_file.py::test_file_component_is_wired_into_cmake -v
```

Expected:

```text
FAILED ... assert 'add_subdirectory(components/file)' in root_cmake
```

- [ ] **Step 3: 新增组件 CMake 和临时实现**

创建目录：

```bash
mkdir -p components/file/src
```

创建 `components/file/CMakeLists.txt`：

```cmake
add_library(ep_components_file STATIC
  src/ep_file.c
)

target_include_directories(ep_components_file
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
```

创建 `components/file/src/ep_file.c`：

```c
#include "ep_file.h"
#include "ep_osal_err.h"

int ep_file_open(ep_file_t **file, const char *path, int mode)
{
    (void)file;
    (void)path;
    (void)mode;
    return EP_ERR_UNSUPPORTED;
}

int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read)
{
    (void)file;
    (void)buffer;
    (void)buffer_size;
    if (bytes_read != 0) {
        *bytes_read = 0u;
    }
    return EP_ERR_UNSUPPORTED;
}

int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written)
{
    (void)file;
    (void)buffer;
    (void)buffer_size;
    if (bytes_written != 0) {
        *bytes_written = 0u;
    }
    return EP_ERR_UNSUPPORTED;
}

int ep_file_close(ep_file_t *file)
{
    (void)file;
    return EP_ERR_UNSUPPORTED;
}
```

- [ ] **Step 4: 修改根 CMake**

修改根 `CMakeLists.txt`，在 config 后面加入 file：

```cmake
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(components/config)
add_subdirectory(components/file)
add_subdirectory(platforms/rtos/demo_family)
add_subdirectory(platforms/linux/demo_family)
add_subdirectory(platforms/host/posix)
```

- [ ] **Step 5: 运行测试确认通过**

Run:

```bash
pytest tests/host_unit/test_host_file.py::test_file_component_is_wired_into_cmake -v
```

Expected:

```text
PASSED
```

- [ ] **Step 6: 运行 CMake configure 确认骨架有效**

Run:

```bash
cmake -S . -B build
```

Expected:

```text
Configuring done
Generating done
```

- [ ] **Step 7: 提交 CMake 骨架**

```bash
git add CMakeLists.txt components/file/CMakeLists.txt components/file/src/ep_file.c tests/host_unit/test_host_file.py
git commit -m "build: 接入 file 组件骨架"
```

## Task 3: 实现 host 文件读写行为

**Files:**
- Modify: `tests/host_unit/test_host_file.py`
- Modify: `components/file/src/ep_file.c`

- [ ] **Step 1: 写失败行为测试**

在 `tests/host_unit/test_host_file.py` 追加：

```python
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

                if (ep_file_open(&missing, missing_path, EP_FILE_MODE_READ) != EP_ERR_UNSUPPORTED) {
                    return 9;
                }

                if (missing != 0) {
                    return 10;
                }

                if (ep_file_read(0, buffer, sizeof(buffer), &count) != EP_ERR_INVAL) {
                    return 11;
                }

                count = 99u;
                if (ep_file_read(file, 0, 1u, &count) != EP_ERR_INVAL) {
                    return 12;
                }

                if (count != 0u) {
                    return 13;
                }

                count = 99u;
                if (ep_file_write(0, "x", 1u, &count) != EP_ERR_INVAL) {
                    return 14;
                }

                count = 99u;
                if (ep_file_write(file, 0, 1u, &count) != EP_ERR_INVAL) {
                    return 15;
                }

                if (count != 0u) {
                    return 16;
                }

                if (ep_file_close(0) != EP_ERR_INVAL) {
                    return 17;
                }

                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE) != EP_OK) {
                    return 18;
                }

                if (file == 0) {
                    return 19;
                }

                count = 99u;
                if (ep_file_write(file, "hello", 5u, &count) != EP_OK) {
                    return 20;
                }

                if (count != 5u) {
                    return 21;
                }

                if (ep_file_write(file, "", 0u, &count) != EP_OK) {
                    return 22;
                }

                if (count != 0u) {
                    return 23;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 24;
                }

                file = 0;
                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_APPEND) != EP_OK) {
                    return 25;
                }

                if (ep_file_write(file, " world", 6u, 0) != EP_OK) {
                    return 26;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 27;
                }

                file = 0;
                memset(buffer, 0, sizeof(buffer));
                if (ep_file_open(&file, path, EP_FILE_MODE_READ) != EP_OK) {
                    return 28;
                }

                count = 99u;
                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 29;
                }

                if (count != 11u || strcmp(buffer, "hello world") != 0) {
                    return 30;
                }

                count = 99u;
                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 31;
                }

                if (count != 0u) {
                    return 32;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 33;
                }

                file = 0;
                if (ep_file_open(&file, path, EP_FILE_MODE_WRITE | EP_FILE_MODE_CREATE | EP_FILE_MODE_TRUNCATE) != EP_OK) {
                    return 34;
                }

                if (ep_file_write(file, "new", 3u, &count) != EP_OK) {
                    return 35;
                }

                if (count != 3u) {
                    return 36;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 37;
                }

                file = 0;
                memset(buffer, 0, sizeof(buffer));
                if (ep_file_open(&file, path, EP_FILE_MODE_READ) != EP_OK) {
                    return 38;
                }

                if (ep_file_read(file, buffer, sizeof(buffer), &count) != EP_OK) {
                    return 39;
                }

                if (count != 3u || strcmp(buffer, "new") != 0) {
                    return 40;
                }

                if (ep_file_close(file) != EP_OK) {
                    return 41;
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_host_file.py::test_host_file_read_write_append_truncate_and_errors -v
```

Expected:

```text
FAILED ... file smoke failed with 2
```

- [ ] **Step 3: 替换为 stdio 实现**

将 `components/file/src/ep_file.c` 替换为：

```c
#include "ep_file.h"
#include "ep_osal_err.h"

#include <stdio.h>
#include <stdlib.h>

struct ep_file {
    FILE *handle;
};

static int ep_file_mode_has(int mode, int flag)
{
    return (mode & flag) != 0;
}

static const char *ep_file_mode_to_stdio(int mode)
{
    int read = ep_file_mode_has(mode, EP_FILE_MODE_READ);
    int write = ep_file_mode_has(mode, EP_FILE_MODE_WRITE);
    int create = ep_file_mode_has(mode, EP_FILE_MODE_CREATE);
    int truncate = ep_file_mode_has(mode, EP_FILE_MODE_TRUNCATE);
    int append = ep_file_mode_has(mode, EP_FILE_MODE_APPEND);

    if (mode == 0) {
        return 0;
    }

    if (!read && !write) {
        return 0;
    }

    if (append && truncate) {
        return 0;
    }

    if (append && !write) {
        return 0;
    }

    if (create && !write) {
        return 0;
    }

    if (truncate && !write) {
        return 0;
    }

    if (read && write && create && truncate) {
        return "wb+";
    }

    if (read && write && create) {
        return "ab+";
    }

    if (read && write) {
        return "rb+";
    }

    if (read) {
        return "rb";
    }

    if (write && create && truncate) {
        return "wb";
    }

    if (write && create && append) {
        return "ab";
    }

    if (write && create) {
        return "ab+";
    }

    return 0;
}

int ep_file_open(ep_file_t **file, const char *path, int mode)
{
    const char *stdio_mode;
    ep_file_t *new_file;
    FILE *handle;

    if (file == 0 || path == 0 || path[0] == '\0') {
        return EP_ERR_INVAL;
    }

    *file = 0;

    stdio_mode = ep_file_mode_to_stdio(mode);
    if (stdio_mode == 0) {
        return EP_ERR_INVAL;
    }

    handle = fopen(path, stdio_mode);
    if (handle == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    new_file = (ep_file_t *)malloc(sizeof(*new_file));
    if (new_file == 0) {
        (void)fclose(handle);
        return EP_ERR_BUSY;
    }

    new_file->handle = handle;
    *file = new_file;
    return EP_OK;
}

int ep_file_read(ep_file_t *file, void *buffer, size_t buffer_size, size_t *bytes_read)
{
    size_t count;

    if (bytes_read != 0) {
        *bytes_read = 0u;
    }

    if (file == 0 || (buffer == 0 && buffer_size > 0u)) {
        return EP_ERR_INVAL;
    }

    if (buffer_size == 0u) {
        return EP_OK;
    }

    count = fread(buffer, 1u, buffer_size, file->handle);
    if (bytes_read != 0) {
        *bytes_read = count;
    }

    if (count < buffer_size && ferror(file->handle) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

int ep_file_write(ep_file_t *file, const void *buffer, size_t buffer_size, size_t *bytes_written)
{
    size_t count;

    if (bytes_written != 0) {
        *bytes_written = 0u;
    }

    if (file == 0 || (buffer == 0 && buffer_size > 0u)) {
        return EP_ERR_INVAL;
    }

    if (buffer_size == 0u) {
        return EP_OK;
    }

    count = fwrite(buffer, 1u, buffer_size, file->handle);
    if (bytes_written != 0) {
        *bytes_written = count;
    }

    if (count != buffer_size) {
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

int ep_file_close(ep_file_t *file)
{
    int rc;

    if (file == 0) {
        return EP_ERR_INVAL;
    }

    rc = fclose(file->handle);
    free(file);

    return (rc == 0) ? EP_OK : EP_ERR_UNSUPPORTED;
}
```

- [ ] **Step 4: 运行行为测试确认通过**

Run:

```bash
pytest tests/host_unit/test_host_file.py::test_host_file_read_write_append_truncate_and_errors -v
```

Expected:

```text
PASSED
```

- [ ] **Step 5: 运行 file 相关测试确认通过**

Run:

```bash
pytest tests/api_contract/test_file_headers.py tests/host_unit/test_host_file.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 6: 提交 file 行为实现**

```bash
git add tests/host_unit/test_host_file.py components/file/src/ep_file.c
git commit -m "feat: 实现 file host 文件读写"
```

## Task 4: 全量验证并创建 PR

**Files:**
- No code changes.

- [ ] **Step 1: 运行完整 host/api 测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
passed
```

- [ ] **Step 2: 运行 CMake configure**

Run:

```bash
cmake -S . -B build
```

Expected:

```text
Configuring done
Generating done
```

- [ ] **Step 3: 运行 CMake build**

Run:

```bash
cmake --build build
```

Expected:

```text
Built target ep_components_file
```

- [ ] **Step 4: 运行空白检查**

Run:

```bash
git diff --check
```

Expected:

```text
无输出，返回码为 0
```

- [ ] **Step 5: 推送并创建 PR**

```bash
git status --short --branch
git log --oneline --decorate --max-count=8
git push -u origin feature/file-component
gh pr create --base main --head feature/file-component --title "feat: 实现 file 文件组件" --body "$(cat <<'EOF'
## Summary
- 新增 `components/file` 公共接口和 CMake 组件
- 实现 host stdio 文件打开、读取、写入、追加、截断和关闭
- 补充 file 头文件契约测试和 host 行为测试

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `git diff --check`

## Notes
- 本 PR 不修改 config、log 或 framework 初始化链路
- 本 PR 不接 flash、Luban-Lite 或 RT-Thread
- 本 PR 不实现目录、seek、stat、rename 或异步文件 IO
EOF
)"
```

## 覆盖检查

- 设计要求 `components/file/include/ep_file.h` 平台无关：Task 1。
- 设计要求 `ep_file_open/read/write/close`：Task 1、Task 3。
- 设计要求打开模式：Task 1、Task 3。
- 设计要求 CMake 构建 `ep_components_file`：Task 2。
- 设计要求 host 上验证写、读、追加、截断、EOF、错误路径：Task 3。
- 设计非目标包括不改 config/log/framework、不接 flash/Luban-Lite/RT-Thread、不做目录/seek/stat/rename/异步 IO：本计划不触碰这些模块和能力。
