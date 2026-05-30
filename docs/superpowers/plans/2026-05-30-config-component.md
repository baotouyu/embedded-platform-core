# Config Component Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `components/config` 内存 key/value 配置组件，提供平台无关的 int、bool、string 配置读写接口。

**Architecture:** `components/config` 暴露 `ep_config.h`，内部使用固定容量内存表保存 key/value。第一版不落盘、不读取文件、不接 flash、不接 Luban-Lite/RT-Thread，也不接入 `ep_framework_init()`。

**Tech Stack:** C、CMake、pytest、host 编译 smoke test、现有 `ep_osal_err.h` 错误码。

---

## 文件结构

- `tests/api_contract/test_config_headers.py`
  - 约束 `ep_config.h` 存在、平台无关、可独立编译。
- `components/config/include/ep_config.h`
  - 定义 config 公共 API，只暴露平台无关接口。
- `tests/host_unit/test_host_config.py`
  - 约束 CMake 接入和 host 行为。
- `components/config/CMakeLists.txt`
  - 定义 `ep_components_config` 静态库。
- `components/config/src/ep_config.c`
  - 实现内存 key/value 配置表。
- `CMakeLists.txt`
  - 增加 `add_subdirectory(components/config)`。

## Task 1: 增加 config 公共头文件契约

**Files:**
- Create: `tests/api_contract/test_config_headers.py`
- Create: `components/config/include/ep_config.h`

- [ ] **Step 1: 写失败测试**

创建 `tests/api_contract/test_config_headers.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_INCLUDE = REPO_ROOT / "components" / "config" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_config_header_is_platform_neutral():
    header = CONFIG_INCLUDE / "ep_config.h"

    assert header.exists(), "Expected components/config/include/ep_config.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "sys/",
        "platforms/",
        "third_party/",
        "elog.h",
        "EasyLogger",
        "ep_file",
        "flash",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_config.h must stay platform-neutral, found: {found}"


def test_config_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "config_header_smoke.c"
    obj = tmp_path / "config_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_config.h"
            #include "ep_config.h"

            int main(void)
            {
                int (*init_fn)(void) = ep_config_init;
                int (*set_int_fn)(const char *, int) = ep_config_set_int;
                int (*get_int_fn)(const char *, int) = ep_config_get_int;
                int (*set_bool_fn)(const char *, int) = ep_config_set_bool;
                int (*get_bool_fn)(const char *, int) = ep_config_get_bool;
                int (*set_string_fn)(const char *, const char *) = ep_config_set_string;
                const char *(*get_string_fn)(const char *, const char *) = ep_config_get_string;

                return (init_fn && set_int_fn && get_int_fn && set_bool_fn &&
                        get_bool_fn && set_string_fn && get_string_fn) ? 0 : 1;
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
            str(CONFIG_INCLUDE),
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

- [ ] **Step 2: 运行测试，确认因为头文件不存在而失败**

Run:

```bash
pytest tests/api_contract/test_config_headers.py -v
```

Expected: FAIL，失败点包含：

```text
Expected components/config/include/ep_config.h to exist
```

- [ ] **Step 3: 写最小公共头文件**

创建 `components/config/include/ep_config.h`：

```c
#ifndef EP_CONFIG_H
#define EP_CONFIG_H

int ep_config_init(void);

int ep_config_set_int(const char *key, int value);
int ep_config_get_int(const char *key, int default_value);

int ep_config_set_bool(const char *key, int value);
int ep_config_get_bool(const char *key, int default_value);

int ep_config_set_string(const char *key, const char *value);
const char *ep_config_get_string(const char *key, const char *default_value);

#endif
```

- [ ] **Step 4: 运行头文件契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_config_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交公共头文件契约**

Run:

```bash
git add tests/api_contract/test_config_headers.py components/config/include/ep_config.h
git commit -m "test: 增加 config 公共接口契约"
```

## Task 2: 接入 config 组件 CMake 骨架

**Files:**
- Create: `tests/host_unit/test_host_config.py`
- Create: `components/config/CMakeLists.txt`
- Create: `components/config/src/ep_config.c`
- Modify: `CMakeLists.txt`

- [ ] **Step 1: 写失败测试**

创建 `tests/host_unit/test_host_config.py`，先只放入 CMake 接入测试：

```python
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
```

- [ ] **Step 2: 运行 CMake 接入测试，确认失败**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_config_component_is_wired_into_cmake -v
```

Expected: FAIL，失败点包含：

```text
assert 'add_subdirectory(components/config)' in root_cmake
```

- [ ] **Step 3: 接入根 CMake**

修改根 `CMakeLists.txt`，在 `components/log` 后增加 `components/config`：

```cmake
add_subdirectory(core)
add_subdirectory(app)
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(components/config)
add_subdirectory(platforms/rtos/demo_family)
add_subdirectory(platforms/linux/demo_family)
add_subdirectory(platforms/host/posix)
```

- [ ] **Step 4: 创建 config 组件 CMake**

创建 `components/config/CMakeLists.txt`：

```cmake
add_library(ep_components_config STATIC
  src/ep_config.c
)

target_include_directories(ep_components_config
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
```

- [ ] **Step 5: 创建可编译的最小 stub 实现**

创建 `components/config/src/ep_config.c`：

```c
#include "ep_config.h"
#include "ep_osal_err.h"

int ep_config_init(void)
{
    return EP_OK;
}

int ep_config_set_int(const char *key, int value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

int ep_config_get_int(const char *key, int default_value)
{
    (void)key;
    return default_value;
}

int ep_config_set_bool(const char *key, int value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

int ep_config_get_bool(const char *key, int default_value)
{
    (void)key;
    return default_value;
}

int ep_config_set_string(const char *key, const char *value)
{
    (void)key;
    (void)value;
    return EP_ERR_UNSUPPORTED;
}

const char *ep_config_get_string(const char *key, const char *default_value)
{
    (void)key;
    return default_value;
}
```

- [ ] **Step 6: 运行 CMake 接入测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_config_component_is_wired_into_cmake -v
```

Expected:

```text
1 passed
```

- [ ] **Step 7: 运行 CMake 配置 smoke，确认新组件可被 CMake 读取**

Run:

```bash
cmake -S . -B build
```

Expected: exit code 0，输出包含：

```text
Build files have been written to:
```

- [ ] **Step 8: 提交 CMake 骨架**

Run:

```bash
git add CMakeLists.txt components/config/CMakeLists.txt components/config/src/ep_config.c tests/host_unit/test_host_config.py
git commit -m "build: 接入 config 组件骨架"
```

## Task 3: 增加 host 行为测试并实现内存配置表

**Files:**
- Modify: `tests/host_unit/test_host_config.py`
- Modify: `components/config/src/ep_config.c`

- [ ] **Step 1: 写失败行为测试**

在 `tests/host_unit/test_host_config.py` 末尾追加：

```python
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
        f"config smoke failed with {run_result.returncode}\\n"
        f"stdout:\\n{run_result.stdout}\\n"
        f"stderr:\\n{run_result.stderr}"
    )
```

- [ ] **Step 2: 运行行为测试，确认 stub 实现失败**

Run:

```bash
pytest tests/host_unit/test_host_config.py::test_host_config_memory_store_validation_and_defaults -v
```

Expected: FAIL，失败信息包含：

```text
config smoke failed with 6
```

失败码 6 表示 `ep_config_set_int("log.level", 3)` 仍返回 `EP_ERR_UNSUPPORTED`。

- [ ] **Step 3: 写内存配置表实现**

将 `components/config/src/ep_config.c` 替换为：

```c
#include "ep_config.h"
#include "ep_osal_err.h"

#include <stddef.h>
#include <string.h>

#define EP_CONFIG_MAX_ITEMS 32u
#define EP_CONFIG_KEY_MAX_LEN 48u
#define EP_CONFIG_STRING_MAX_LEN 96u

typedef enum {
    EP_CONFIG_VALUE_INT = 0,
    EP_CONFIG_VALUE_BOOL = 1,
    EP_CONFIG_VALUE_STRING = 2
} ep_config_value_type_e;

typedef struct {
    int used;
    char key[EP_CONFIG_KEY_MAX_LEN];
    ep_config_value_type_e type;
    union {
        int int_value;
        int bool_value;
        char string_value[EP_CONFIG_STRING_MAX_LEN];
    } value;
} ep_config_entry_t;

static int g_ep_config_initialized;
static ep_config_entry_t g_ep_config_entries[EP_CONFIG_MAX_ITEMS];

static int ep_config_key_is_valid(const char *key)
{
    if (key == 0 || key[0] == '\0') {
        return 0;
    }

    return strlen(key) < EP_CONFIG_KEY_MAX_LEN;
}

static ep_config_entry_t *ep_config_find_entry(const char *key)
{
    size_t i;

    for (i = 0u; i < EP_CONFIG_MAX_ITEMS; ++i) {
        if (g_ep_config_entries[i].used != 0 && strcmp(g_ep_config_entries[i].key, key) == 0) {
            return &g_ep_config_entries[i];
        }
    }

    return 0;
}

static ep_config_entry_t *ep_config_alloc_entry(void)
{
    size_t i;

    for (i = 0u; i < EP_CONFIG_MAX_ITEMS; ++i) {
        if (g_ep_config_entries[i].used == 0) {
            return &g_ep_config_entries[i];
        }
    }

    return 0;
}

static int ep_config_prepare_entry(const char *key, ep_config_entry_t **entry)
{
    ep_config_entry_t *found;

    if (entry == 0) {
        return EP_ERR_INVAL;
    }

    *entry = 0;

    if (g_ep_config_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (!ep_config_key_is_valid(key)) {
        return EP_ERR_INVAL;
    }

    found = ep_config_find_entry(key);
    if (found != 0) {
        *entry = found;
        return EP_OK;
    }

    found = ep_config_alloc_entry();
    if (found == 0) {
        return EP_ERR_BUSY;
    }

    found->used = 1;
    (void)strcpy(found->key, key);
    *entry = found;
    return EP_OK;
}

int ep_config_init(void)
{
    if (g_ep_config_initialized != 0) {
        return EP_OK;
    }

    (void)memset(g_ep_config_entries, 0, sizeof(g_ep_config_entries));
    g_ep_config_initialized = 1;
    return EP_OK;
}

int ep_config_set_int(const char *key, int value)
{
    ep_config_entry_t *entry;
    int rc = ep_config_prepare_entry(key, &entry);

    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_INT;
    entry->value.int_value = value;
    return EP_OK;
}

int ep_config_get_int(const char *key, int default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_INT) {
        return default_value;
    }

    return entry->value.int_value;
}

int ep_config_set_bool(const char *key, int value)
{
    ep_config_entry_t *entry;
    int rc = ep_config_prepare_entry(key, &entry);

    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_BOOL;
    entry->value.bool_value = (value != 0) ? 1 : 0;
    return EP_OK;
}

int ep_config_get_bool(const char *key, int default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_BOOL) {
        return default_value;
    }

    return entry->value.bool_value;
}

int ep_config_set_string(const char *key, const char *value)
{
    ep_config_entry_t *entry;
    int rc;

    if (value == 0 || strlen(value) >= EP_CONFIG_STRING_MAX_LEN) {
        return EP_ERR_INVAL;
    }

    rc = ep_config_prepare_entry(key, &entry);
    if (rc != EP_OK) {
        return rc;
    }

    entry->type = EP_CONFIG_VALUE_STRING;
    (void)strcpy(entry->value.string_value, value);
    return EP_OK;
}

const char *ep_config_get_string(const char *key, const char *default_value)
{
    ep_config_entry_t *entry;

    if (g_ep_config_initialized == 0 || !ep_config_key_is_valid(key)) {
        return default_value;
    }

    entry = ep_config_find_entry(key);
    if (entry == 0 || entry->type != EP_CONFIG_VALUE_STRING) {
        return default_value;
    }

    return entry->value.string_value;
}
```

- [ ] **Step 4: 运行 host config 测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_config.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 运行 config 头文件契约测试，确认仍通过**

Run:

```bash
pytest tests/api_contract/test_config_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交 config 内存后端实现**

Run:

```bash
git add tests/host_unit/test_host_config.py components/config/src/ep_config.c
git commit -m "feat: 实现 config 内存配置表"
```

## Task 4: 全量验证并收尾

**Files:**
- No code changes expected.

- [ ] **Step 1: 运行 host_unit 和 api_contract 测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected: 全部测试通过，输出包含：

```text
passed
```

- [ ] **Step 2: 重新配置 CMake**

Run:

```bash
cmake -S . -B build
```

Expected: exit code 0，输出包含：

```text
Build files have been written to:
```

- [ ] **Step 3: 构建全部目标**

Run:

```bash
cmake --build build
```

Expected: exit code 0，输出包含：

```text
Built target ep_components_config
```

- [ ] **Step 4: 检查 diff 空白问题**

Run:

```bash
git diff --check
```

Expected: exit code 0，无输出。

- [ ] **Step 5: 检查最近提交和工作区状态**

Run:

```bash
git status --short --branch
git log --oneline --decorate -6
```

Expected:

```text
## feature/config-component
```

最近提交包含：

```text
feat: 实现 config 内存配置表
build: 接入 config 组件骨架
test: 增加 config 公共接口契约
```

## PR 内容建议

标题：

```text
feat: 实现 config 内存配置组件
```

正文：

```markdown
## Summary
- 新增 `components/config` 公共接口和 CMake 组件
- 实现内存 key/value 配置表，支持 int、bool、string
- 补充 config 头文件契约测试和 host 行为测试

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `git diff --check`

## Notes
- 本 PR 不落盘、不读取配置文件
- 本 PR 不接 file、flash、Luban-Lite 或 RT-Thread
- 本 PR 不把 config 接入 `ep_framework_init()`
```
