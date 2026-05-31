# 配置驱动日志等级 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `config/profiles/host.cfg` 中的 `log.level` 在 framework 启动后真正控制 `ep_log` 的输出等级。

**Architecture:** `components/log` 新增 `ep_log_set_level()` 和 `ep_log_get_level()`，并在 `ep_log_write()` 内做全局等级过滤；`components/log` 不依赖 `components/config`。`core/src/ep_framework.c` 在默认配置加载后读取 `log.level`，再调用 `ep_log_set_level()`，作为 config 到 log 的唯一桥接点。

**Tech Stack:** C11、CMake、pytest、EasyLogger、现有 `ep_config_get_int()`、现有 `EP_OK/EP_ERR_*` 错误码。

---

## 参考文档

- 设计文档：`docs/superpowers/specs/2026-05-31-log-level-config-design.md`
- EasyLogger 后端设计：`docs/superpowers/specs/2026-05-30-easylogger-log-backend-design.md`
- framework 启动加载配置设计：`docs/superpowers/specs/2026-05-31-framework-config-load-design.md`

## 文件结构

- Modify: `components/log/include/ep_log.h`
  - 新增日志等级设置和读取公共 API。

- Modify: `components/log/src/ep_log.c`
  - 保存当前全局日志等级。
  - 校验日志等级。
  - 在输出前过滤高于当前等级的日志。

- Modify: `tests/api_contract/test_log_headers.py`
  - 确认公共头新增 API，且仍然平台无关、不暴露 EasyLogger。

- Modify: `tests/host_unit/test_host_log.py`
  - 增加 host smoke 测试覆盖默认等级、过滤行为、非法等级。

- Modify: `core/src/ep_framework.c`
  - 增加 `EP_FRAMEWORK_LOG_LEVEL_KEY` 和 `ep_framework_apply_log_config()`。
  - 默认配置加载后应用 `log.level`。

- Modify: `tests/host_unit/test_framework_bootstrap.py`
  - 检查 framework 源码包含日志配置应用调用。
  - 增加 framework smoke 测试覆盖 `host.cfg` 的 `log.level=3` 过滤 DEBUG。
  - 增加非法 `log.level` 会让 `ep_framework_init()` 失败的测试。

---

## Task 1: ep_log 公共等级 API 和过滤行为

**Files:**
- Modify: `tests/api_contract/test_log_headers.py`
- Modify: `tests/host_unit/test_host_log.py`
- Modify: `components/log/include/ep_log.h`
- Modify: `components/log/src/ep_log.c`

- [ ] **Step 1: 写 API contract 失败测试**

修改 `tests/api_contract/test_log_headers.py` 的 `test_log_header_compiles_standalone()`，将 C 源码片段替换为：

```python
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_log.h"

            int main(void)
            {
                ep_log_level_e level = EP_LOG_LEVEL_INFO;
                int (*init_fn)(void) = ep_log_init;
                int (*set_level_fn)(ep_log_level_e) = ep_log_set_level;
                ep_log_level_e (*get_level_fn)(void) = ep_log_get_level;
                int (*write_fn)(ep_log_level_e, const char *, const char *, ...) = ep_log_write;

                if (EP_LOG_LEVEL_ASSERT != 0) {
                    return 1;
                }

                EP_LOGE("contract", "error %d", 1);
                EP_LOGW("contract", "warn %d", 2);
                EP_LOGI("contract", "info %d", 3);
                EP_LOGD("contract", "debug %d", 4);
                EP_LOGV("contract", "verbose %d", 5);

                return (level == EP_LOG_LEVEL_INFO &&
                        init_fn &&
                        set_level_fn &&
                        get_level_fn &&
                        write_fn) ? 0 : 2;
            }
            """
        ).strip()
        + "\n"
    )
```

- [ ] **Step 2: 运行 API contract 测试确认失败**

Run:

```bash
pytest tests/api_contract/test_log_headers.py::test_log_header_compiles_standalone -v
```

Expected:

```text
FAILED ... undeclared identifier 'ep_log_set_level'
```

- [ ] **Step 3: 写 log 组件行为失败测试**

在 `tests/host_unit/test_host_log.py` 的 `test_host_log_init_validation_and_output()` 后新增：

```python
def test_host_log_level_filtering_and_validation(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_log_level_smoke.c"
    executable = tmp_path / "host_log_level_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_log.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                if (ep_log_get_level() != EP_LOG_LEVEL_INFO) {
                    return 1;
                }

                if (ep_log_set_level(EP_LOG_LEVEL_WARN) != EP_OK) {
                    return 2;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 3;
                }

                if (ep_log_set_level((ep_log_level_e)-1) != EP_ERR_INVAL) {
                    return 4;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 5;
                }

                if (ep_log_set_level((ep_log_level_e)6) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                    return 7;
                }

                if (ep_log_init() != EP_OK) {
                    return 8;
                }

                if (ep_log_write(EP_LOG_LEVEL_INFO, "level-filter", "info hidden") != EP_OK) {
                    return 9;
                }

                if (ep_log_write(EP_LOG_LEVEL_ERROR, "level-filter", "error visible") != EP_OK) {
                    return 10;
                }

                if (ep_log_set_level(EP_LOG_LEVEL_VERBOSE) != EP_OK) {
                    return 11;
                }

                if (ep_log_write(EP_LOG_LEVEL_DEBUG, "level-filter", "debug visible") != EP_OK) {
                    return 12;
                }

                if (ep_log_write((ep_log_level_e)99, "level-filter", "bad level") != EP_ERR_INVAL) {
                    return 13;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
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
    assert "info hidden" not in run_result.stdout
    assert "error visible" in run_result.stdout
    assert "debug visible" in run_result.stdout
```

- [ ] **Step 4: 运行 log 行为测试确认失败**

Run:

```bash
pytest tests/host_unit/test_host_log.py::test_host_log_level_filtering_and_validation -v
```

Expected:

```text
FAILED ... implicit declaration of function 'ep_log_get_level'
```

- [ ] **Step 5: 修改 `ep_log.h` 增加公共 API**

修改 `components/log/include/ep_log.h`，在 `ep_log_init()` 后增加：

```c
int ep_log_set_level(ep_log_level_e level);
ep_log_level_e ep_log_get_level(void);
```

期望完整头文件为：

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
int ep_log_set_level(ep_log_level_e level);
ep_log_level_e ep_log_get_level(void);
int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...);

#define EP_LOGA(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ASSERT, tag, fmt, ##__VA_ARGS__)
#define EP_LOGE(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ERROR, tag, fmt, ##__VA_ARGS__)
#define EP_LOGW(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_WARN, tag, fmt, ##__VA_ARGS__)
#define EP_LOGI(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_INFO, tag, fmt, ##__VA_ARGS__)
#define EP_LOGD(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_DEBUG, tag, fmt, ##__VA_ARGS__)
#define EP_LOGV(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_VERBOSE, tag, fmt, ##__VA_ARGS__)

#endif
```

- [ ] **Step 6: 修改 `ep_log.c` 实现等级状态和过滤**

修改 `components/log/src/ep_log.c`：

```c
#include "ep_log.h"
#include "ep_osal_err.h"
#include "elog.h"

#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>

#define EP_LOG_LINE_BUF_SIZE 256u

static int g_ep_log_initialized;
static ep_log_level_e g_ep_log_level = EP_LOG_LEVEL_INFO;

static int ep_log_level_is_valid(ep_log_level_e level)
{
    return level >= EP_LOG_LEVEL_ASSERT && level <= EP_LOG_LEVEL_VERBOSE;
}

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

int ep_log_set_level(ep_log_level_e level)
{
    if (!ep_log_level_is_valid(level)) {
        return EP_ERR_INVAL;
    }

    g_ep_log_level = level;
    return EP_OK;
}

ep_log_level_e ep_log_get_level(void)
{
    return g_ep_log_level;
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

    if (level > g_ep_log_level) {
        return EP_OK;
    }

    va_start(args, fmt);
    (void)vsnprintf(line, sizeof(line), fmt, args);
    va_end(args);

    elog_output(elog_level, tag, 0, 0, 0, "%s", line);
    return EP_OK;
}
```

- [ ] **Step 7: 运行 log 相关测试确认通过**

Run:

```bash
pytest tests/api_contract/test_log_headers.py tests/host_unit/test_host_log.py -v
```

Expected:

```text
6 passed
```

- [ ] **Step 8: 提交 ep_log 等级 API 和过滤行为**

```bash
git add tests/api_contract/test_log_headers.py tests/host_unit/test_host_log.py components/log/include/ep_log.h components/log/src/ep_log.c
git commit -m "feat: 增加日志等级过滤"
```

---

## Task 2: framework 应用 `log.level`

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`
- Modify: `core/src/ep_framework.c`

- [ ] **Step 1: 写 framework 源码结构失败测试**

修改 `tests/host_unit/test_framework_bootstrap.py` 的 `test_framework_bootstrap_symbols_exist()`，在默认配置加载断言附近新增：

```python
    assert "EP_FRAMEWORK_LOG_LEVEL_KEY" in source
    assert '"log.level"' in source
    assert "static int ep_framework_apply_log_config(void)" in source
    assert "ep_config_get_int(EP_FRAMEWORK_LOG_LEVEL_KEY, EP_LOG_LEVEL_INFO)" in source
    assert "ep_log_set_level((ep_log_level_e)level)" in source
    assert "rc = ep_framework_apply_log_config();" in source
```

同时补顺序断言：

```python
    assert source.index("ep_framework_load_default_config()") < source.index("ep_framework_apply_log_config()")
    assert source.index("ep_framework_apply_log_config()") < source.index("ep_event_init()")
```

- [ ] **Step 2: 写 framework 行为失败测试**

在 `tests/host_unit/test_framework_bootstrap.py` 末尾新增：

```python
def test_framework_init_applies_log_level_from_config_file(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_log_level_smoke.c"
    executable = tmp_path / "framework_log_level_smoke"
    config_dir = tmp_path / "config/profiles"

    config_dir.mkdir(parents=True)
    (config_dir / "host.cfg").write_text("int log.level=2\n", encoding="utf-8")

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_log.h"
        #include "ep_osal_err.h"

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
            if (ep_framework_init() != EP_OK) {
                return 1;
            }

            if (ep_log_get_level() != EP_LOG_LEVEL_WARN) {
                return 2;
            }

            if (ep_log_write(EP_LOG_LEVEL_INFO, "framework-log-level", "info hidden") != EP_OK) {
                return 3;
            }

            if (ep_log_write(EP_LOG_LEVEL_ERROR, "framework-log-level", "error visible") != EP_OK) {
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
        cwd=tmp_path,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework log level smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
    assert "info hidden" not in run_result.stdout
    assert "error visible" in run_result.stdout
```

继续新增非法 `log.level` 测试：

```python
def test_framework_init_fails_on_invalid_log_level_config(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    repo_root = Path(__file__).resolve().parents[2]
    source = tmp_path / "framework_bad_log_level_smoke.c"
    executable = tmp_path / "framework_bad_log_level_smoke"
    config_dir = tmp_path / "config/profiles"

    config_dir.mkdir(parents=True)
    (config_dir / "host.cfg").write_text("int log.level=99\n", encoding="utf-8")

    source.write_text(
        """
        #include "ep_framework.h"
        #include "ep_osal_err.h"

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
            return ep_framework_init() == EP_ERR_INVAL ? 0 : 1;
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
        cwd=tmp_path,
        check=False,
    )

    assert run_result.returncode == 0, (
        f"framework bad log level smoke failed with {run_result.returncode}\n"
        f"stdout:\n{run_result.stdout}\n"
        f"stderr:\n{run_result.stderr}"
    )
```

- [ ] **Step 3: 运行 framework 新测试确认失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist tests/host_unit/test_framework_bootstrap.py::test_framework_init_applies_log_level_from_config_file tests/host_unit/test_framework_bootstrap.py::test_framework_init_fails_on_invalid_log_level_config -v
```

Expected:

```text
FAILED ... AssertionError
FAILED ... framework log level smoke failed with 2
FAILED ... framework bad log level smoke failed with 1
```

`test_framework_init_applies_log_level_from_config_file` 使用临时 `config/profiles/host.cfg` 写入 `int log.level=2`，所以实现前必须因为当前日志等级仍是默认 INFO 而失败。

- [ ] **Step 4: 修改 framework 源码应用日志配置**

修改 `core/src/ep_framework.c`：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_log.h"
#include "ep_config.h"
#include "ep_event.h"
#include "ep_timer.h"
#include "ep_osal_err.h"

#define EP_FRAMEWORK_DEFAULT_CONFIG_PATH "config/profiles/host.cfg"
#define EP_FRAMEWORK_LOG_LEVEL_KEY "log.level"

static int ep_framework_load_default_config(void)
{
    int rc = ep_config_load_file(EP_FRAMEWORK_DEFAULT_CONFIG_PATH);

    if (rc == EP_ERR_UNSUPPORTED) {
        return EP_OK;
    }

    return rc;
}

static int ep_framework_apply_log_config(void)
{
    int level = ep_config_get_int(EP_FRAMEWORK_LOG_LEVEL_KEY, EP_LOG_LEVEL_INFO);

    if (level < EP_LOG_LEVEL_ASSERT || level > EP_LOG_LEVEL_VERBOSE) {
        return EP_ERR_INVAL;
    }

    return ep_log_set_level((ep_log_level_e)level);
}

int ep_framework_init(void)
{
    int rc = ep_log_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_config_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_load_default_config();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_apply_log_config();
    if (rc != 0) {
        return rc;
    }

    rc = ep_event_init();
    if (rc != 0) {
        return rc;
    }

    return ep_timer_init();
}

int ep_framework_start(void)
{
    int rc = ep_platform_boot();
    if (rc != 0) {
        return rc;
    }

    rc = ep_framework_init();
    if (rc != 0) {
        return rc;
    }

    return app_main();
}
```

- [ ] **Step 5: 运行 framework 相关测试确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py -v
```

Expected:

```text
9 passed
```

本文件在 Task 2 前已有 7 个测试，Task 2 新增 2 个测试后应为 9 个。实际数量如果随测试变化略有不同，要求是全部通过、0 failures。

- [ ] **Step 6: 提交 framework 应用 log.level**

```bash
git add tests/host_unit/test_framework_bootstrap.py core/src/ep_framework.c
git commit -m "feat: framework 应用日志等级配置"
```

---

## Task 3: 全量验证、PR、合并和清理

**Files:**
- No source changes expected

- [ ] **Step 1: 运行全量测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
65 passed
```

实际数量可能随测试变化略有不同，要求是全部通过、0 failures。

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
Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 host 可执行文件**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected: exit code 0.

- [ ] **Step 4: 运行 diff 空白检查**

Run:

```bash
git diff --check
```

Expected: no output, exit code 0.

- [ ] **Step 5: 检查工作区和提交范围**

Run:

```bash
git status --short --branch
git log --oneline --decorate --graph --max-count=8
git diff --stat origin/main..HEAD
```

Expected:

```text
## feature/log-level-config
```

Diff 应只包含：

```text
components/log/include/ep_log.h
components/log/src/ep_log.c
core/src/ep_framework.c
tests/api_contract/test_log_headers.py
tests/host_unit/test_framework_bootstrap.py
tests/host_unit/test_host_log.py
```

- [ ] **Step 6: 推送实现分支**

```bash
git push -u origin feature/log-level-config
```

- [ ] **Step 7: 创建 PR**

```bash
gh pr create --base main --head feature/log-level-config --title "feat: 接入日志等级配置" --body "$(cat <<'EOF'
## Summary
- 新增 `ep_log_set_level()` 和 `ep_log_get_level()` 公共 API
- `ep_log_write()` 根据当前日志等级过滤输出
- framework 加载默认配置后读取 `log.level` 并应用到日志组件

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- `components/log` 仍然不依赖 `components/config`
- 本 PR 不做 tag 过滤、颜色配置、输出目的地配置
- 本 PR 不接 Luban-Lite、RT-Thread 或真实串口输出
EOF
)"
```

- [ ] **Step 8: 等待 GitHub 检查通过**

Run:

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr checks "$PR_NUMBER" --watch --interval 5
```

Expected:

```text
host-tests pass
```

- [ ] **Step 9: squash merge**

```bash
PR_NUMBER=$(gh pr view --json number --jq '.number')
gh pr merge "$PR_NUMBER" --squash --delete-branch --subject "feat: 接入日志等级配置" --body $'接入日志等级配置：\n\n- 新增日志等级设置和读取 API\n- ep_log_write 按当前等级过滤输出\n- framework 读取 log.level 并应用到日志组件'
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

- [ ] **Step 10: 同步 main 并清理本地分支**

在主工作区 `/Users/yuwei/Documents/KitchenIdea/项目/C08/embedded-platform-core` 执行：

```bash
git pull --ff-only
git worktree remove .worktrees/feature-log-level-config
git branch -d feature/log-level-config
git push origin --delete feature/log-level-config
```

如果远程分支已经被 GitHub 删除，`git push origin --delete` 可能提示 remote ref 不存在；这种情况下确认远程只剩 `origin/main` 即可。

- [ ] **Step 11: 最终状态确认**

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
* main ... [origin/main] feat: 接入日志等级配置
origin/HEAD -> origin/main
origin/main
```

并且没有 `feature/log-level-config` 本地或远程分支。
