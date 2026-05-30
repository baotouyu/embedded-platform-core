# EasyLogger Log Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现第一版 `components/log`，通过 `ep_log` 公共接口封装 EasyLogger 同步输出后端，并在 host POSIX 上验证初始化和日志输出。

**Architecture:** 上层只 include `components/log/include/ep_log.h`，不直接依赖 EasyLogger 的 `elog.h`。EasyLogger 源码放在 `third_party/external/EasyLogger`，`components/log/src/ep_log.c` 负责把 `ep_log_*` API 映射到 EasyLogger，host POSIX 通过 `elog_port_*` 输出到 stdout 并使用 OSAL time/mutex。

**Tech Stack:** C11、CMake、EasyLogger、OSAL err/time/mutex、host POSIX、pytest。

---

## 文件结构

- Create: `components/log/include/ep_log.h`
  - `ep_log` 公共头文件，只暴露工程自己的日志级别、初始化和写日志接口。
- Create: `components/log/src/ep_log.c`
  - `ep_log` 到 EasyLogger 的适配层，负责初始化、参数校验、日志级别映射和格式化转发。
- Create: `components/log/CMakeLists.txt`
  - 构建 `ep_components_log` 静态库，并链接 EasyLogger 后端。
- Modify: `CMakeLists.txt`
  - 新增 `add_subdirectory(components/log)`。
- Create: `third_party/external/EasyLogger/LICENSE`
  - 保留 EasyLogger MIT 许可证文本。
- Create: `third_party/external/EasyLogger/easylogger/inc/elog.h`
  - 引入 EasyLogger 公共头文件。
- Create: `third_party/external/EasyLogger/easylogger/inc/elog_cfg.h`
  - 使用本工程第一版同步输出配置。
- Create: `third_party/external/EasyLogger/easylogger/src/elog.c`
  - 引入 EasyLogger 核心实现。
- Create: `third_party/external/EasyLogger/easylogger/src/elog_utils.c`
  - 引入 EasyLogger 工具实现。
- Create: `third_party/external/EasyLogger/easylogger/port/elog_port.c`
  - 第一版 host POSIX port，输出到 stdout，使用 OSAL time 和 mutex。
- Create: `tests/api_contract/test_log_headers.py`
  - 保护 `ep_log.h` 的公共接口和平台无关性。
- Create: `tests/host_unit/test_host_log.py`
  - 验证 CMake 接入、第三方许可证存在、初始化幂等、参数错误和 host 输出。
- Modify: `platforms/host/posix/CMakeLists.txt`
  - host POSIX 可执行文件链接 `ep_components_log`，保证后续 framework 接入前已经有最终链接闭环。

## Task 1: 锁定 `ep_log` 公共接口契约

**Files:**
- Create: `tests/api_contract/test_log_headers.py`
- Create: `components/log/include/ep_log.h`

- [ ] **Step 1: 写失败的公共头文件契约测试**

创建 `tests/api_contract/test_log_headers.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LOG_INCLUDE = REPO_ROOT / "components" / "log" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_log_header_does_not_expose_easylogger_or_platform_headers():
    header = LOG_INCLUDE / "ep_log.h"

    assert header.exists(), "Expected components/log/include/ep_log.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = [
        "elog.h",
        "pthread.h",
        "rtthread.h",
        "unistd.h",
        "sys/",
        "platforms/",
        "third_party/",
    ]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_log.h must hide EasyLogger and stay platform-neutral, found: {found}"


def test_log_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "log_header_smoke.c"
    obj = tmp_path / "log_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_log.h"

            int main(void)
            {
                ep_log_level_e level = EP_LOG_LEVEL_INFO;
                int (*init_fn)(void) = ep_log_init;
                int (*write_fn)(ep_log_level_e, const char *, const char *, ...) = ep_log_write;

                if (EP_LOG_LEVEL_ASSERT != 0) {
                    return 1;
                }

                EP_LOGE("contract", "error %d", 1);
                EP_LOGW("contract", "warn %d", 2);
                EP_LOGI("contract", "info %d", 3);
                EP_LOGD("contract", "debug %d", 4);
                EP_LOGV("contract", "verbose %d", 5);

                return (level == EP_LOG_LEVEL_INFO && init_fn && write_fn) ? 0 : 2;
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
            str(LOG_INCLUDE),
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
pytest tests/api_contract/test_log_headers.py -v
```

Expected:

```text
FAILED tests/api_contract/test_log_headers.py::test_log_header_does_not_expose_easylogger_or_platform_headers
Expected components/log/include/ep_log.h to exist
```

- [ ] **Step 3: 写最小公共头文件**

创建 `components/log/include/ep_log.h`：

```c
#ifndef EP_LOG_H
#define EP_LOG_H

typedef enum {
    EP_LOG_LEVEL_ASSERT = 0,
    EP_LOG_LEVEL_ERROR = 1,
    EP_LOG_LEVEL_WARN = 2,
    EP_LOG_LEVEL_INFO = 3,
    EP_LOG_LEVEL_DEBUG = 4,
    EP_LOG_LEVEL_VERBOSE = 5
} ep_log_level_e;

int ep_log_init(void);
int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...);

#define EP_LOGA(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ASSERT, tag, fmt, ##__VA_ARGS__)
#define EP_LOGE(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ERROR, tag, fmt, ##__VA_ARGS__)
#define EP_LOGW(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_WARN, tag, fmt, ##__VA_ARGS__)
#define EP_LOGI(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_INFO, tag, fmt, ##__VA_ARGS__)
#define EP_LOGD(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_DEBUG, tag, fmt, ##__VA_ARGS__)
#define EP_LOGV(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_VERBOSE, tag, fmt, ##__VA_ARGS__)

#endif
```

- [ ] **Step 4: 运行接口契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_log_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交公共接口契约**

Run:

```bash
git add tests/api_contract/test_log_headers.py components/log/include/ep_log.h
git commit -m "test: 增加 log 公共接口契约"
```

## Task 2: 引入 EasyLogger 同步后端并实现 `ep_log`

**Files:**
- Create: `tests/host_unit/test_host_log.py`
- Create: `components/log/src/ep_log.c`
- Create: `components/log/CMakeLists.txt`
- Modify: `CMakeLists.txt`
- Create: `third_party/external/EasyLogger/LICENSE`
- Create: `third_party/external/EasyLogger/easylogger/inc/elog.h`
- Create: `third_party/external/EasyLogger/easylogger/inc/elog_cfg.h`
- Create: `third_party/external/EasyLogger/easylogger/src/elog.c`
- Create: `third_party/external/EasyLogger/easylogger/src/elog_utils.c`
- Create: `third_party/external/EasyLogger/easylogger/port/elog_port.c`

- [ ] **Step 1: 写失败的 CMake 和第三方来源测试**

创建 `tests/host_unit/test_host_log.py`，先放入 CMake 和第三方来源测试：

```python
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

    assert "add_subdirectory(components/log)" in root_cmake
    assert log_cmake_path.exists()

    log_cmake = log_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_log STATIC" in log_cmake
    assert "src/ep_log.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog_utils.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/port/elog_port.c" in log_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in log_cmake

    license_text = (easylogger_root / "LICENSE").read_text(encoding="utf-8")
    assert "The MIT License" in license_text
    assert "Copyright (c) 2015-2019 Armink" in license_text
```

- [ ] **Step 2: 运行测试，确认因为 log CMake 未接入而失败**

Run:

```bash
pytest tests/host_unit/test_host_log.py::test_log_component_and_easylogger_are_wired_into_cmake -v
```

Expected:

```text
FAILED tests/host_unit/test_host_log.py::test_log_component_and_easylogger_are_wired_into_cmake
assert 'add_subdirectory(components/log)' in root_cmake
```

- [ ] **Step 3: 引入 EasyLogger 核心源码**

从上游仓库复制以下文件，保持版权头不删除：

```bash
mkdir -p third_party/external/EasyLogger/easylogger/inc
mkdir -p third_party/external/EasyLogger/easylogger/src
mkdir -p third_party/external/EasyLogger/easylogger/port
cp /tmp/easylogger-analysis/LICENSE third_party/external/EasyLogger/LICENSE
cp /tmp/easylogger-analysis/easylogger/inc/elog.h third_party/external/EasyLogger/easylogger/inc/elog.h
cp /tmp/easylogger-analysis/easylogger/src/elog.c third_party/external/EasyLogger/easylogger/src/elog.c
cp /tmp/easylogger-analysis/easylogger/src/elog_utils.c third_party/external/EasyLogger/easylogger/src/elog_utils.c
```

如果 `/tmp/easylogger-analysis` 不存在，先执行：

```bash
rm -rf /tmp/easylogger-analysis
git clone --depth 1 https://github.com/armink/EasyLogger.git /tmp/easylogger-analysis
```

- [ ] **Step 4: 写本工程 EasyLogger 配置**

创建 `third_party/external/EasyLogger/easylogger/inc/elog_cfg.h`：

```c
#ifndef _ELOG_CFG_H_
#define _ELOG_CFG_H_

#define ELOG_OUTPUT_ENABLE
#define ELOG_OUTPUT_LVL ELOG_LVL_VERBOSE
#define ELOG_LINE_BUF_SIZE 256
#define ELOG_LINE_NUM_MAX_LEN 5
#define ELOG_FILTER_TAG_MAX_LEN 24
#define ELOG_FILTER_KW_MAX_LEN 16
#define ELOG_FILTER_TAG_LVL_MAX_NUM 5
#define ELOG_NEWLINE_SIGN "\n"

#define ELOG_FMT_USING_FUNC
#define ELOG_FMT_USING_DIR
#define ELOG_FMT_USING_LINE

#endif
```

- [ ] **Step 5: 写 host POSIX EasyLogger port**

创建 `third_party/external/EasyLogger/easylogger/port/elog_port.c`：

```c
#include "elog.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_time.h"

#include <stdio.h>

static ep_mutex_t *g_elog_output_lock;
static char g_elog_time[24];

ElogErrCode elog_port_init(void)
{
    if (g_elog_output_lock != 0) {
        return ELOG_NO_ERR;
    }

    if (ep_mutex_create(&g_elog_output_lock) != EP_OK) {
        return ELOG_NO_ERR;
    }

    return ELOG_NO_ERR;
}

void elog_port_deinit(void)
{
}

void elog_port_output(const char *log, size_t size)
{
    (void)fwrite(log, 1u, size, stdout);
    (void)fflush(stdout);
}

void elog_port_output_lock(void)
{
    if (g_elog_output_lock != 0) {
        (void)ep_mutex_lock(g_elog_output_lock);
    }
}

void elog_port_output_unlock(void)
{
    if (g_elog_output_lock != 0) {
        (void)ep_mutex_unlock(g_elog_output_lock);
    }
}

const char *elog_port_get_time(void)
{
    (void)snprintf(g_elog_time, sizeof(g_elog_time), "ms:%010llu", (unsigned long long)ep_time_now_ms());
    return g_elog_time;
}

const char *elog_port_get_p_info(void)
{
    return "";
}

const char *elog_port_get_t_info(void)
{
    return "";
}
```

说明：`ep_mutex_create()` 失败时仍返回 `ELOG_NO_ERR`，日志会退化为无锁输出。原因是 EasyLogger 当前错误码只有
`ELOG_NO_ERR`，无法向上精确表达 port 初始化失败。

- [ ] **Step 6: 写 `ep_log` 最小实现**

创建 `components/log/src/ep_log.c`：

```c
#include "ep_log.h"
#include "ep_osal_err.h"
#include "elog.h"

#include <stdarg.h>
#include <stdio.h>

#define EP_LOG_LINE_BUF_SIZE 256u

static int g_ep_log_initialized;

static int ep_log_to_easylogger_level(ep_log_level_e level, uint8_t *elog_level)
{
    if (elog_level == 0) {
        return EP_ERR_INVAL;
    }

    switch (level) {
    case EP_LOG_LEVEL_ASSERT:
        *elog_level = ELOG_LVL_ASSERT;
        return EP_OK;
    case EP_LOG_LEVEL_ERROR:
        *elog_level = ELOG_LVL_ERROR;
        return EP_OK;
    case EP_LOG_LEVEL_WARN:
        *elog_level = ELOG_LVL_WARN;
        return EP_OK;
    case EP_LOG_LEVEL_INFO:
        *elog_level = ELOG_LVL_INFO;
        return EP_OK;
    case EP_LOG_LEVEL_DEBUG:
        *elog_level = ELOG_LVL_DEBUG;
        return EP_OK;
    case EP_LOG_LEVEL_VERBOSE:
        *elog_level = ELOG_LVL_VERBOSE;
        return EP_OK;
    default:
        return EP_ERR_INVAL;
    }
}

int ep_log_init(void)
{
    ElogErrCode rc;

    if (g_ep_log_initialized != 0) {
        return EP_OK;
    }

    rc = elog_init();
    if (rc != ELOG_NO_ERR) {
        return EP_ERR_UNSUPPORTED;
    }

    elog_set_fmt(ELOG_LVL_ASSERT, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
    elog_set_fmt(ELOG_LVL_ERROR, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_WARN, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_INFO, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_set_fmt(ELOG_LVL_DEBUG, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
    elog_set_fmt(ELOG_LVL_VERBOSE, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
    elog_start();

    g_ep_log_initialized = 1;
    return EP_OK;
}

int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...)
{
    char line[EP_LOG_LINE_BUF_SIZE];
    uint8_t elog_level;
    va_list args;
    int rc;

    if (g_ep_log_initialized == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    if (tag == 0 || fmt == 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_log_to_easylogger_level(level, &elog_level);
    if (rc != EP_OK) {
        return rc;
    }

    va_start(args, fmt);
    (void)vsnprintf(line, sizeof(line), fmt, args);
    va_end(args);

    elog_output(elog_level, tag, 0, 0, 0, "%s", line);
    return EP_OK;
}
```

- [ ] **Step 7: 写 log 组件 CMake**

创建 `components/log/CMakeLists.txt`：

```cmake
add_library(ep_components_log STATIC
  src/ep_log.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog_utils.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/port/elog_port.c
)

target_include_directories(ep_components_log
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc
)
```

- [ ] **Step 8: 修改顶层 CMake**

在顶层 `CMakeLists.txt` 的 components 区域加入：

```cmake
add_subdirectory(components/log)
```

修改后的相关片段应为：

```cmake
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(platforms/rtos/demo_family)
```

- [ ] **Step 9: 运行 CMake 和第三方来源测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_log.py::test_log_component_and_easylogger_are_wired_into_cmake -v
```

Expected:

```text
1 passed
```

- [ ] **Step 10: 提交 EasyLogger 后端骨架**

Run:

```bash
git add CMakeLists.txt components/log/CMakeLists.txt components/log/src/ep_log.c tests/host_unit/test_host_log.py third_party/external/EasyLogger
git commit -m "feat: 引入 EasyLogger log 后端"
```

## Task 3: 验证 host 日志行为和平台链接闭环

**Files:**
- Modify: `tests/host_unit/test_host_log.py`
- Modify: `platforms/host/posix/CMakeLists.txt`

- [ ] **Step 1: 写失败的 host 日志行为测试**

在 `tests/host_unit/test_host_log.py` 追加：

```python
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
```

同时追加 host 平台链接测试：

```python
def test_host_posix_links_log_component():
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "ep_components_log" in host_cmake
```

- [ ] **Step 2: 运行 host 日志测试，确认平台链接断言失败**

Run:

```bash
pytest tests/host_unit/test_host_log.py -v
```

Expected:

```text
FAILED tests/host_unit/test_host_log.py::test_host_posix_links_log_component
assert 'ep_components_log' in host_cmake
```

如果行为测试因为 EasyLogger 源码的编译警告失败，先记录具体 warning，再只做必须的配置调整；不要改 EasyLogger 核心源码。

- [ ] **Step 3: 修改 host POSIX 链接 log 组件**

在 `platforms/host/posix/CMakeLists.txt` 的 `target_link_libraries(ep_platform_host_posix ...)` 中加入：

```cmake
    ep_components_log
```

修改后的链接片段应为：

```cmake
target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    Threads::Threads
)
```

- [ ] **Step 4: 运行 host 日志测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_log.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 5: 运行 log 头文件契约测试，确认仍通过**

Run:

```bash
pytest tests/api_contract/test_log_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交 host 日志行为和平台链接**

Run:

```bash
git add tests/host_unit/test_host_log.py platforms/host/posix/CMakeLists.txt
git commit -m "test: 验证 host log 输出"
```

## Task 4: 完整验证和 PR 前收尾

**Files:**
- Verify only.

- [ ] **Step 1: 运行完整 host 和契约测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
所有测试通过，0 failed
```

- [ ] **Step 2: 运行 CMake 配置**

Run:

```bash
cmake -S . -B build
```

Expected:

```text
配置成功，退出码为 0
```

- [ ] **Step 3: 运行 CMake 构建**

Run:

```bash
cmake --build build
```

Expected:

```text
构建成功，输出包含 Built target ep_components_log 和 Built target ep_platform_host_posix
```

- [ ] **Step 4: 运行 host POSIX 程序**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
命令退出码为 0
```

- [ ] **Step 5: 检查 diff 空白问题**

Run:

```bash
git diff --check
```

Expected:

```text
无输出，退出码为 0
```

- [ ] **Step 6: 检查工作区和提交记录**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected:

```text
工作区干净，最近提交包含 log 公共接口契约、EasyLogger 后端和 host log 输出验证提交
```

- [ ] **Step 7: PR 标题和正文使用中文**

PR 标题：

```text
feat: 实现 EasyLogger log 后端
```

PR 正文：

```markdown
## 变更内容

- 新增 `components/log` 和 `ep_log` 公共接口
- 引入 EasyLogger 核心同步输出源码并保留 MIT 许可证
- 使用 `ep_log` 封装 EasyLogger，避免上层直接依赖 `elog.h`
- 增加 host POSIX EasyLogger port，输出到 stdout
- 补充 log 公共头文件契约测试和 host 输出测试
- 让 host POSIX 可执行文件链接 `ep_components_log`

## 测试

- [ ] `pytest tests/host_unit tests/api_contract -v`
- [ ] `cmake -S . -B build`
- [ ] `cmake --build build`
- [ ] `./build/platforms/host/posix/ep_platform_host_posix`
- [ ] `git diff --check`
```

## 自检结果

- 设计文档要求均有对应任务：
  - `components/log` 和 `ep_log.h`：Task 1、Task 2。
  - EasyLogger 作为内部后端且不暴露 `elog.h`：Task 1 契约测试、Task 2 实现。
  - 第三方源码保留 MIT 许可证：Task 2。
  - host POSIX 输出到 stdout：Task 2、Task 3。
  - 不启用异步、文件、Flash 插件：Task 2 的 `elog_cfg.h`。
  - 本阶段不接入 framework、Luban-Lite、RT-Thread 或真实 SDK：本计划没有修改 core 初始化或新增真实 RTOS port。
- 任务按 TDD 顺序拆分：先写失败测试，再写实现，再运行测试。
- 每个代码修改步骤都给出完整代码片段或明确复制来源。
