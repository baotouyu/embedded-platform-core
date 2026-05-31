# Framework Config Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ep_framework_init()` 自动初始化 config，使 framework 启动链路固定为 `log -> config -> event -> timer`。

**Architecture:** core 层继续用显式顺序编排基础组件初始化。`ep_framework_init()` include `ep_config.h` 并在 `ep_log_init()` 成功后调用 `ep_config_init()`；最终可执行目标负责链接 `ep_components_config`，`ep_core` 只增加 config 公共头文件 include 路径。

**Tech Stack:** C11、CMake、`components/config`、`components/log`、`components/event`、`components/timer`、host POSIX、Linux demo skeleton、pytest。

---

## 文件结构

- 修改 `tests/host_unit/test_framework_bootstrap.py`
  - 增加 framework 到 config 的源码契约测试。
  - 约束 include、初始化调用、初始化顺序和 core include 路径。
- 修改 `core/src/ep_framework.c`
  - include `ep_config.h`。
  - 在 `ep_log_init()` 成功后、`ep_event_init()` 前调用 `ep_config_init()`。
- 修改 `core/CMakeLists.txt`
  - 给 `ep_core` 增加 `${CMAKE_SOURCE_DIR}/components/config/include` 私有 include 路径。
- 修改 `tests/api_contract/test_platform_bootstrap.py`
  - 检查 host POSIX 和 linux demo 都链接 `ep_components_config`。
- 修改 `platforms/host/posix/CMakeLists.txt`
  - 给最终 host 可执行目标链接 `ep_components_config`。
- 修改 `platforms/linux/demo_family/CMakeLists.txt`
  - 给最终 linux demo 可执行目标链接 `ep_components_config`。

## Task 1: 锁定 framework 到 config 的源码契约

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: 写失败测试**

修改 `tests/host_unit/test_framework_bootstrap.py` 中的 `test_framework_bootstrap_symbols_exist()`，加入 config 相关断言。

目标函数完整内容应为：

```python
def test_framework_bootstrap_symbols_exist():
    header = Path("core/include/ep_framework.h").read_text()
    app_header = Path("app/include/app_main.h").read_text()
    source = Path("core/src/ep_framework.c").read_text()
    cmake = Path("core/CMakeLists.txt").read_text()
    assert "int ep_platform_boot(void);" in header
    assert "int ep_framework_init(void);" in header
    assert "int ep_framework_start(void);" in header
    assert "int app_main(void);" in app_header
    assert "int ep_framework_init(void)" in source
    assert "int ep_framework_start(void)" in source
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PUBLIC\n    ${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "PRIVATE\n    ${CMAKE_SOURCE_DIR}/app/include" in cmake
    assert "PUBLIC\n    ${CMAKE_SOURCE_DIR}/app/include" not in cmake
    assert '#include "ep_log.h"' in source
    assert '#include "elog.h"' not in source
    assert '#include "ep_config.h"' in source
    assert '#include "ep_event.h"' in source
    assert '#include "ep_timer.h"' in source
    assert "int rc = ep_log_init();" in source
    assert "rc = ep_config_init();" in source
    assert "rc = ep_event_init();" in source
    assert "return ep_event_init();" not in source
    assert "return ep_timer_init();" in source
    assert "EP_LOGI(" not in source
    assert "EP_LOGE(" not in source
    assert source.index("ep_log_init()") < source.index("ep_config_init()")
    assert source.index("ep_config_init()") < source.index("ep_event_init()")
    assert source.index("ep_event_init()") < source.index("ep_timer_init()")
    assert "${CMAKE_SOURCE_DIR}/components/log/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/config/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
FAILED ... assert '#include "ep_config.h"' in source
```

- [ ] **Step 3: 提交失败测试**

```bash
git add tests/host_unit/test_framework_bootstrap.py
git commit -m "test: 增加 framework config 初始化契约"
```

## Task 2: 接入 core 初始化顺序

**Files:**
- Modify: `core/src/ep_framework.c`
- Modify: `core/CMakeLists.txt`

- [ ] **Step 1: 修改 framework 初始化代码**

将 `core/src/ep_framework.c` 改为：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_log.h"
#include "ep_config.h"
#include "ep_event.h"
#include "ep_timer.h"

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

- [ ] **Step 2: 修改 core include 路径**

将 `core/CMakeLists.txt` 改为：

```cmake
add_library(ep_core STATIC
  src/ep_framework.c
)

target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/config/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
)
```

- [ ] **Step 3: 运行 framework 契约测试确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
PASSED
```

- [ ] **Step 4: 运行 core 构建烟测确认当前链接缺口**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py -v
```

Expected:

```text
2 passed
```

说明：`ep_core` 是静态库，单独构建不会解析 `ep_config_init()` 最终链接符号。平台最终可执行目标链接在 Task 3 处理。

- [ ] **Step 5: 提交 core 初始化接入**

```bash
git add core/src/ep_framework.c core/CMakeLists.txt
git commit -m "feat: 接入 framework config 初始化"
```

## Task 3: 补齐平台最终链接关系

**Files:**
- Modify: `tests/api_contract/test_platform_bootstrap.py`
- Modify: `platforms/host/posix/CMakeLists.txt`
- Modify: `platforms/linux/demo_family/CMakeLists.txt`

- [ ] **Step 1: 写失败测试**

修改 `tests/api_contract/test_platform_bootstrap.py` 中的 `test_platform_executables_link_framework_components()`，加入 `ep_components_config` 检查。

目标函数完整内容应为：

```python
def test_platform_executables_link_framework_components():
    linux_cmake = (REPO_ROOT / "platforms/linux/demo_family/CMakeLists.txt").read_text()
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    timer_cmake = (REPO_ROOT / "components/timer/CMakeLists.txt").read_text()

    assert "ep_components_timer" in host_cmake
    assert "ep_components_timer" in linux_cmake
    assert "ep_components_log" in host_cmake
    assert "ep_components_log" in linux_cmake
    assert "ep_components_config" in host_cmake
    assert "ep_components_config" in linux_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected:

```text
FAILED ... assert 'ep_components_config' in host_cmake
```

- [ ] **Step 3: 修改 host POSIX 链接关系**

将 `platforms/host/posix/CMakeLists.txt` 的 `target_link_libraries(ep_platform_host_posix ...)` 改为：

```cmake
target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    ep_components_config
    Threads::Threads
)
```

- [ ] **Step 4: 修改 linux demo 链接关系**

将 `platforms/linux/demo_family/CMakeLists.txt` 的 `target_link_libraries(ep_platform_linux_demo ...)` 改为：

```cmake
target_link_libraries(ep_platform_linux_demo
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    ep_components_config
)
```

- [ ] **Step 5: 运行平台链接契约测试确认通过**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected:

```text
PASSED
```

- [ ] **Step 6: 运行平台构建烟测确认最终链接通过**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_demo_targets_configure_and_build -v
```

Expected:

```text
PASSED
```

- [ ] **Step 7: 提交平台链接接入**

```bash
git add tests/api_contract/test_platform_bootstrap.py platforms/host/posix/CMakeLists.txt platforms/linux/demo_family/CMakeLists.txt
git commit -m "build: 链接 framework config 组件"
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
Built target ep_platform_host_posix
```

- [ ] **Step 4: 运行 host POSIX 可执行文件**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
返回码为 0
```

- [ ] **Step 5: 运行空白检查**

Run:

```bash
git diff --check
```

Expected:

```text
无输出，返回码为 0
```

- [ ] **Step 6: 推送并创建 PR**

```bash
git status --short --branch
git log --oneline --decorate --max-count=6
git push -u origin feature/framework-config-init
gh pr create --base main --head feature/framework-config-init --title "feat: 接入 framework config 初始化" --body "$(cat <<'EOF'
## Summary
- 让 `ep_framework_init()` 按 `log -> config -> event -> timer` 顺序初始化基础组件
- 给 `ep_core` 增加 config 公共头文件 include 路径
- 给 host POSIX 和 linux demo 补齐 `ep_components_config` 链接关系

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- 本 PR 不改变 config API
- 本 PR 不接文件配置、flash、Luban-Lite 或 RT-Thread
- 本 PR 不把日志等级绑定到 config
EOF
)"
```

## 覆盖检查

- 设计要求 `ep_framework_init()` 自动调用 `ep_config_init()`：Task 1、Task 2。
- 设计要求顺序为 `log -> config -> event -> timer`：Task 1、Task 2。
- 设计要求失败立即返回：Task 2 使用和现有 log/event 一致的 `rc != 0` 返回模式。
- 设计要求 core 只依赖 `ep_config.h`：Task 1、Task 2。
- 设计要求 host POSIX 和 linux demo 链接 `ep_components_config`：Task 3。
- 设计非目标包括不接文件、flash、Luban-Lite、RT-Thread、不绑定日志等级：本计划不修改 config API，不新增平台 port，不修改 log 行为。
