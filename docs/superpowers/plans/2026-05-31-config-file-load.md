# Config 文件加载 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 `components/config` 增加 `ep_config_load_file(const char *path)`，让 Mac/Ubuntu host 可以从简单文本文件加载 int/bool/string 配置。

**Architecture:** `ep_config_load_file()` 作为 config 的公共 API 暴露，但 `ep_config.h` 不包含 `ep_file.h`。config 的 `.c` 实现私有依赖 `components/file`，读取整个小配置文件到固定缓冲区，再逐行解析并复用现有 `ep_config_set_int/bool/string` 写入内存表。第一版不做事务回滚、不保存文件、不接 framework 自动初始化。

**Tech Stack:** C11、CMake、pytest、host 编译 smoke test、现有 `ep_osal_err.h` 错误码、现有 `ep_file_*` 文件接口。

---

## 参考文档

- 设计文档：`docs/superpowers/specs/2026-05-31-config-file-load-design.md`
- 现有 config 设计：`docs/superpowers/specs/2026-05-30-config-component-design.md`
- file 设计：`docs/superpowers/specs/2026-05-31-file-component-design.md`

## 文件结构

- Modify: `components/config/include/ep_config.h`
  - 新增 `int ep_config_load_file(const char *path);`
  - 仍然不包含 `ep_file.h`

- Modify: `components/config/src/ep_config.c`
  - 私有包含 `ep_file.h`
  - 新增固定缓冲区读取逻辑
  - 新增按行解析逻辑
  - 新增 int/bool/string value 解析逻辑
  - 复用现有 `ep_config_set_int()`、`ep_config_set_bool()`、`ep_config_set_string()`

- Modify: `components/config/CMakeLists.txt`
  - 私有包含 `components/file/include`
  - 私有链接 `ep_components_file`

- Modify: `CMakeLists.txt`
  - 将 `add_subdirectory(components/file)` 放到 `add_subdirectory(components/config)` 前面，阅读顺序和依赖方向一致

- Modify: `tests/api_contract/test_config_headers.py`
  - 头文件 smoke test 增加 `ep_config_load_file` 函数指针检查

- Modify: `tests/host_unit/test_host_config.py`
  - CMake wiring test 增加 file include 和 link 断言
  - 新增 host smoke test 验证正常加载、覆盖、多次加载和错误路径

---

## Task 1: 公共 API 契约

**Files:**
- Modify: `tests/api_contract/test_config_headers.py`
- Modify: `components/config/include/ep_config.h`

- [ ] **Step 1: 写失败测试，要求 `ep_config.h` 暴露 `ep_config_load_file`**

修改 `tests/api_contract/test_config_headers.py` 里 `test_config_header_compiles_standalone()` 生成的 C 代码，把函数指针检查改成：

```c
#include "ep_config.h"
#include "ep_config.h"

int main(void)
{
    int (*init_fn)(void) = ep_config_init;
    int (*load_file_fn)(const char *) = ep_config_load_file;
    int (*set_int_fn)(const char *, int) = ep_config_set_int;
    int (*get_int_fn)(const char *, int) = ep_config_get_int;
    int (*set_bool_fn)(const char *, int) = ep_config_set_bool;
    int (*get_bool_fn)(const char *, int) = ep_config_get_bool;
    int (*set_string_fn)(const char *, const char *) = ep_config_set_string;
    const char *(*get_string_fn)(const char *, const char *) = ep_config_get_string;

    return (init_fn && load_file_fn && set_int_fn && get_int_fn &&
            set_bool_fn && get_bool_fn && set_string_fn && get_string_fn) ? 0 : 1;
}
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/api_contract/test_config_headers.py::test_config_header_compiles_standalone -v
```

Expected:

```text
FAILED ... use of undeclared identifier 'ep_config_load_file'
```

- [ ] **Step 3: 在公共头文件增加 API 声明**

修改 `components/config/include/ep_config.h`，在 `ep_config_init()` 后新增：

```c
int ep_config_load_file(const char *path);
```

完整头文件应为：

```c
#ifndef EP_CONFIG_H
#define EP_CONFIG_H

int ep_config_init(void);
int ep_config_load_file(const char *path);

int ep_config_set_int(const char *key, int value);
int ep_config_get_int(const char *key, int default_value);

int ep_config_set_bool(const char *key, int value);
int ep_config_get_bool(const char *key, int default_value);

int ep_config_set_string(const char *key, const char *value);
const char *ep_config_get_string(const char *key, const char *default_value);

#endif
```

- [ ] **Step 4: 运行 API 契约测试确认通过**

Run:

```bash
pytest tests/api_contract/test_config_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交 API 契约**

```bash
git add tests/api_contract/test_config_headers.py components/config/include/ep_config.h
git commit -m "test: 增加 config 文件加载接口契约"
```

---

## Task 2: CMake 依赖接入

**Files:**
- Modify: `tests/host_unit/test_host_config.py`
- Modify: `components/config/CMakeLists.txt`
- Modify: `CMakeLists.txt`

- [ ] **Step 1: 写失败测试，要求 config 私有依赖 file**

修改 `tests/host_unit/test_host_config.py` 的 `test_config_component_is_wired_into_cmake()`，新增断言：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_config_component_is_wired_into_cmake -v
```

Expected:

```text
FAILED ... AssertionError
```

失败原因应是 root CMake 中 file 还在 config 后面，且 `components/config/CMakeLists.txt` 还没有 file include/link。

- [ ] **Step 3: 调整根 CMake 顺序**

修改 `CMakeLists.txt` 中组件顺序为：

```cmake
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(components/file)
add_subdirectory(components/config)
```

- [ ] **Step 4: 调整 config CMake 私有依赖**

修改 `components/config/CMakeLists.txt` 为：

```cmake
add_library(ep_components_config STATIC
  src/ep_config.c
)

target_include_directories(ep_components_config
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/components/file/include
)

target_link_libraries(ep_components_config
  PRIVATE
    ep_components_file
)
```

- [ ] **Step 5: 运行 CMake wiring 测试和配置**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_config_component_is_wired_into_cmake -v
cmake -S . -B build
```

Expected:

```text
1 passed
-- Configuring done
-- Generating done
```

- [ ] **Step 6: 提交 CMake 依赖接入**

```bash
git add CMakeLists.txt components/config/CMakeLists.txt tests/host_unit/test_host_config.py
git commit -m "build: 接入 config 文件依赖"
```

---

## Task 3: 正常文件加载行为

**Files:**
- Modify: `tests/host_unit/test_host_config.py`
- Modify: `components/config/src/ep_config.c`

- [ ] **Step 1: 写失败测试，验证 int/bool/string、覆盖和多次加载**

在 `tests/host_unit/test_host_config.py` 末尾新增：

```python
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
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_host_config_load_file_success_and_overrides -v
```

Expected:

```text
FAILED ... undefined symbol: _ep_config_load_file
```

如果编译器直接报 `implicit declaration` 或 `undeclared identifier`，说明 Task 1 没执行到当前分支，需要先完成 Task 1。

- [ ] **Step 3: 在 `ep_config.c` 增加 include 和固定上限**

在 `components/config/src/ep_config.c` 顶部改为：

```c
#include "ep_config.h"
#include "ep_file.h"
#include "ep_osal_err.h"

#include <errno.h>
#include <limits.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
```

在现有上限宏后新增：

```c
#define EP_CONFIG_FILE_MAX_SIZE 1024u
#define EP_CONFIG_LINE_MAX_LEN 128u
```

- [ ] **Step 4: 增加文件读取辅助函数**

在 `ep_config_prepare_entry()` 后、`ep_config_init()` 前新增：

```c
static int ep_config_read_file(const char *path, char *buffer, size_t buffer_size, size_t *content_size)
{
    ep_file_t *file = 0;
    size_t total = 0u;
    int rc;

    if (content_size == 0 || buffer == 0 || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    *content_size = 0u;

    rc = ep_file_open(&file, path, EP_FILE_MODE_READ);
    if (rc != EP_OK) {
        return rc;
    }

    while (total < buffer_size - 1u) {
        size_t bytes_read = 0u;

        rc = ep_file_read(file, buffer + total, (buffer_size - 1u) - total, &bytes_read);
        if (rc != EP_OK) {
            (void)ep_file_close(file);
            return rc;
        }

        if (bytes_read == 0u) {
            break;
        }

        total += bytes_read;
    }

    rc = ep_file_close(file);
    if (rc != EP_OK) {
        return rc;
    }

    buffer[total] = '\0';
    *content_size = total;
    return EP_OK;
}
```

- [ ] **Step 5: 增加 int 解析辅助函数**

在 `ep_config_read_file()` 后新增：

```c
static int ep_config_parse_int_value(const char *value, int *out_value)
{
    char *end = 0;
    long parsed;

    if (value == 0 || value[0] == '\0' || out_value == 0) {
        return EP_ERR_INVAL;
    }

    errno = 0;
    parsed = strtol(value, &end, 10);
    if (errno != 0 || end == value || end == 0 || end[0] != '\0') {
        return EP_ERR_INVAL;
    }

    if (parsed < INT_MIN || parsed > INT_MAX) {
        return EP_ERR_INVAL;
    }

    *out_value = (int)parsed;
    return EP_OK;
}
```

- [ ] **Step 6: 增加单行解析函数**

在 `ep_config_parse_int_value()` 后新增：

```c
static int ep_config_parse_line(char *line)
{
    char *key;
    char *value;
    char *separator;
    int parsed_int;

    if (line == 0 || line[0] == '\0') {
        return EP_ERR_INVAL;
    }

    separator = strchr(line, '=');
    if (separator == 0) {
        return EP_ERR_INVAL;
    }

    *separator = '\0';
    value = separator + 1;
    if (value[0] == '\0') {
        return EP_ERR_INVAL;
    }

    if (strncmp(line, "int ", 4u) == 0) {
        key = line + 4;
        if (ep_config_parse_int_value(value, &parsed_int) != EP_OK) {
            return EP_ERR_INVAL;
        }
        return ep_config_set_int(key, parsed_int);
    }

    if (strncmp(line, "bool ", 5u) == 0) {
        key = line + 5;
        if (strcmp(value, "true") == 0) {
            return ep_config_set_bool(key, 1);
        }
        if (strcmp(value, "false") == 0) {
            return ep_config_set_bool(key, 0);
        }
        return EP_ERR_INVAL;
    }

    if (strncmp(line, "string ", 7u) == 0) {
        key = line + 7;
        return ep_config_set_string(key, value);
    }

    return EP_ERR_INVAL;
}
```

- [ ] **Step 7: 增加内容解析函数**

在 `ep_config_parse_line()` 后新增：

```c
static int ep_config_parse_content(char *content)
{
    char *line = content;

    while (line != 0 && line[0] != '\0') {
        char *next = strchr(line, '\n');
        size_t line_len;
        int rc;

        if (next != 0) {
            *next = '\0';
        }

        line_len = strlen(line);
        if (line_len > 0u && line[line_len - 1u] == '\r') {
            line[line_len - 1u] = '\0';
            --line_len;
        }

        rc = ep_config_parse_line(line);
        if (rc != EP_OK) {
            return rc;
        }

        if (next == 0) {
            break;
        }

        line = next + 1;
    }

    return EP_OK;
}
```

- [ ] **Step 8: 增加 `ep_config_load_file()` 最小实现**

在 `ep_config_init()` 后新增：

```c
int ep_config_load_file(const char *path)
{
    char content[EP_CONFIG_FILE_MAX_SIZE];
    size_t content_size = 0u;
    int rc;

    if (g_ep_config_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (path == 0 || path[0] == '\0') {
        return EP_ERR_INVAL;
    }

    rc = ep_config_read_file(path, content, sizeof(content), &content_size);
    if (rc != EP_OK) {
        return rc;
    }

    return ep_config_parse_content(content);
}
```

- [ ] **Step 9: 运行正常加载测试确认通过**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_host_config_load_file_success_and_overrides -v
```

Expected:

```text
1 passed
```

- [ ] **Step 10: 运行 config 相关测试**

Run:

```bash
pytest tests/api_contract/test_config_headers.py tests/host_unit/test_host_config.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 11: 提交正常加载行为**

```bash
git add tests/host_unit/test_host_config.py components/config/src/ep_config.c
git commit -m "feat: 实现 config 文件加载"
```

---

## Task 4: 错误路径和格式边界

**Files:**
- Modify: `tests/host_unit/test_host_config.py`
- Modify: `components/config/src/ep_config.c`

- [ ] **Step 1: 写失败测试，覆盖错误路径**

在 `tests/host_unit/test_host_config.py` 末尾新增：

```python
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
```

- [ ] **Step 2: 运行错误路径测试确认失败或通过**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_host_config_load_file_errors -v
```

Expected:

```text
FAILED ... config file error smoke failed with 非 0 返回码
```

预期会失败，因为 Task 3 的最小实现还没有处理空文件和超大文件。

- [ ] **Step 3: 修正实现中的错误路径**

把 `components/config/src/ep_config.c` 中的 `ep_config_read_file()` 替换为：

```c
static int ep_config_read_file(const char *path, char *buffer, size_t buffer_size, size_t *content_size)
{
    ep_file_t *file = 0;
    size_t total = 0u;
    int rc;

    if (content_size == 0 || buffer == 0 || buffer_size == 0u) {
        return EP_ERR_INVAL;
    }

    *content_size = 0u;

    rc = ep_file_open(&file, path, EP_FILE_MODE_READ);
    if (rc != EP_OK) {
        return rc;
    }

    while (total < buffer_size - 1u) {
        size_t bytes_read = 0u;

        rc = ep_file_read(file, buffer + total, (buffer_size - 1u) - total, &bytes_read);
        if (rc != EP_OK) {
            (void)ep_file_close(file);
            return rc;
        }

        if (bytes_read == 0u) {
            break;
        }

        total += bytes_read;
    }

    if (total == buffer_size - 1u) {
        size_t extra = 0u;

        rc = ep_file_read(file, buffer + total, 1u, &extra);
        if (rc != EP_OK) {
            (void)ep_file_close(file);
            return rc;
        }

        if (extra != 0u) {
            (void)ep_file_close(file);
            return EP_ERR_BUSY;
        }
    }

    rc = ep_file_close(file);
    if (rc != EP_OK) {
        return rc;
    }

    buffer[total] = '\0';
    *content_size = total;
    return EP_OK;
}
```

把 `ep_config_parse_content()` 替换为：

```c
static int ep_config_parse_content(char *content)
{
    char *line = content;

    while (line != 0 && line[0] != '\0') {
        char *next = strchr(line, '\n');
        size_t line_len;
        int rc;

        if (next != 0) {
            *next = '\0';
        }

        line_len = strlen(line);
        if (line_len > 0u && line[line_len - 1u] == '\r') {
            line[line_len - 1u] = '\0';
            --line_len;
        }

        if (line_len >= EP_CONFIG_LINE_MAX_LEN) {
            return EP_ERR_INVAL;
        }

        rc = ep_config_parse_line(line);
        if (rc != EP_OK) {
            return rc;
        }

        if (next == 0) {
            break;
        }

        line = next + 1;
    }

    return EP_OK;
}
```

把 `ep_config_load_file()` 替换为：

```c
int ep_config_load_file(const char *path)
{
    char content[EP_CONFIG_FILE_MAX_SIZE];
    size_t content_size = 0u;
    int rc;

    if (g_ep_config_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (path == 0 || path[0] == '\0') {
        return EP_ERR_INVAL;
    }

    rc = ep_config_read_file(path, content, sizeof(content), &content_size);
    if (rc != EP_OK) {
        return rc;
    }

    if (content_size == 0u) {
        return EP_ERR_INVAL;
    }

    return ep_config_parse_content(content);
}
```

- [ ] **Step 4: 运行错误路径测试确认通过**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_host_config_load_file_errors -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 运行 config/file 相关测试**

Run:

```bash
pytest tests/api_contract/test_config_headers.py tests/host_unit/test_host_config.py tests/api_contract/test_file_headers.py tests/host_unit/test_host_file.py -v
```

Expected:

```text
10 passed
```

- [ ] **Step 6: 提交错误路径测试**

```bash
git add tests/host_unit/test_host_config.py components/config/src/ep_config.c
git commit -m "test: 覆盖 config 文件加载错误路径"
```

---

## Task 5: 全量验证、PR、合并和清理

**Files:**
- No source changes expected

- [ ] **Step 1: 运行全量测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
58 passed
```

实际数量可能随新增测试数量变动，要求是全部通过、0 failures。

- [ ] **Step 2: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
-- Configuring done
-- Generating done
Built target ep_components_config
Built target ep_components_file
Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 diff 空白检查**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 4: 检查工作区和提交**

Run:

```bash
git status --short --branch
git log --oneline --decorate --graph --max-count=8
git diff --stat origin/main..HEAD
```

Expected:

```text
## feature/config-file-load
```

并且 diff 只包含 config、CMake 和测试文件。

- [ ] **Step 5: 推送实现分支**

```bash
git push -u origin feature/config-file-load
```

- [ ] **Step 6: 创建 PR**

```bash
gh pr create --base main --head feature/config-file-load --title "feat: 实现 config 文件加载" --body "$(cat <<'EOF'
## Summary
- 新增 `ep_config_load_file(const char *path)` 公共接口
- config 内部通过 `components/file` 读取文本配置文件并加载 int/bool/string
- 补充 config 文件加载正常路径、覆盖行为和错误路径测试

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `git diff --check`

## Notes
- 本 PR 不实现配置保存、热加载、JSON/INI 或 framework 自动初始化
- 本 PR 不接 Luban-Lite、RT-Thread 或真实 flash/NVRAM
EOF
)"
```

- [ ] **Step 7: 等待 GitHub 检查通过**

Run:

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr checks "$PR_NUMBER" --watch --interval 5
```

Expected:

```text
host-tests pass
```

- [ ] **Step 8: squash merge**

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr merge "$PR_NUMBER" --squash --delete-branch --subject "feat: 实现 config 文件加载" --body $'实现 config 文件加载：\n\n- 新增 ep_config_load_file 公共接口\n- 通过 components/file 读取并解析 int/bool/string 文本配置\n- 补充正常路径、覆盖行为和错误路径测试'
```

如果出现：

```text
failed to run git: fatal: 'main' is already used by worktree
```

先确认远程 PR 是否已经合并：

```bash
gh pr view "$PR_NUMBER" --json number,state,mergedAt,mergeCommit,url
```

如果 `state` 是 `MERGED`，继续执行本地清理。

- [ ] **Step 9: 同步 main 并清理本地分支**

在主工作区 `/Users/yuwei/Documents/KitchenIdea/项目/C08/embedded-platform-core` 执行：

```bash
git pull --ff-only
git worktree remove .worktrees/feature-config-file-load
git branch -d feature/config-file-load
git push origin --delete feature/config-file-load
```

如果远程分支已经被 GitHub 删除，`git push origin --delete` 可能提示 remote ref 不存在；这种情况下确认远程只剩 `origin/main` 即可。

- [ ] **Step 10: 最终状态确认**

Run:

```bash
git status --short --branch
git branch -vv
git branch -r
git worktree list
gh pr view "$PR_NUMBER" --json number,state,mergedAt,mergeCommit,url,title
```

Expected:

```text
## main...origin/main
* main ... [origin/main] feat: 实现 config 文件加载
origin/HEAD -> origin/main
origin/main
```

并且没有 `feature/config-file-load` 本地或远程分支。
