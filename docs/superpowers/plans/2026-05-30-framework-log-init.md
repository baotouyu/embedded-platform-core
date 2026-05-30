# Framework Log Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ep_framework_init()` 统一初始化 `log -> event -> timer`，并让 host POSIX 与 linux demo 都能链接包含 log 的 framework。

**Architecture:** 采用显式初始化顺序，不引入组件初始化表。`core` 只 include `ep_log.h` 公共接口，最终平台可执行目标负责链接 `ep_components_log`。本计划不增加日志输出语句、不改 EasyLogger 能力、不接真实 Luban-Lite/RT-Thread port。

**Tech Stack:** C、CMake、pytest、host POSIX demo、linux demo stub、EasyLogger 作为 `ep_log` 内部后端。

---

## 文件结构

- `tests/host_unit/test_framework_bootstrap.py`
  - 负责约束 framework 初始化代码的 include、调用顺序和 `core` include 路径。
- `tests/api_contract/test_platform_bootstrap.py`
  - 负责约束平台 demo 的入口和组件链接关系。
- `core/src/ep_framework.c`
  - 负责 framework 启动流程，新增 `ep_log_init()` 调用。
- `core/CMakeLists.txt`
  - 负责 `ep_core` 的 include 路径，新增 `components/log/include` 私有路径。
- `platforms/linux/demo_family/CMakeLists.txt`
  - 负责 linux demo 可执行目标链接组件，新增 `ep_components_log`。

## Task 1: 增加 framework log 初始化契约测试

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`

- [ ] **Step 1: 写失败测试**

修改 `tests/host_unit/test_framework_bootstrap.py` 中的 `test_framework_bootstrap_symbols_exist()`，加入对 `ep_log` 的断言。

目标函数完整内容如下：

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
    assert '#include "ep_event.h"' in source
    assert '#include "ep_timer.h"' in source
    assert "int rc = ep_log_init();" in source
    assert "rc = ep_event_init();" in source
    assert "return ep_event_init();" not in source
    assert "return ep_timer_init();" in source
    assert "EP_LOGI(" not in source
    assert "EP_LOGE(" not in source
    assert source.index("ep_log_init()") < source.index("ep_event_init()")
    assert source.index("ep_event_init()") < source.index("ep_timer_init()")
    assert "${CMAKE_SOURCE_DIR}/components/log/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake
```

- [ ] **Step 2: 运行单测，确认因为实现未接入而失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected: FAIL，失败点包含：

```text
assert '#include "ep_log.h"' in source
```

- [ ] **Step 3: 提交失败测试**

Run:

```bash
git add tests/host_unit/test_framework_bootstrap.py
git commit -m "test: 约束 framework log 初始化顺序"
```

## Task 2: 增加平台 log 链接契约测试

**Files:**
- Modify: `tests/api_contract/test_platform_bootstrap.py`

- [ ] **Step 1: 写失败测试**

修改 `tests/api_contract/test_platform_bootstrap.py` 中的 `test_platform_executables_link_framework_components()`，加入 host 和 linux demo 对 `ep_components_log` 的链接断言。

目标函数完整内容如下：

```python
def test_platform_executables_link_framework_components():
    linux_cmake = (REPO_ROOT / "platforms/linux/demo_family/CMakeLists.txt").read_text()
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    timer_cmake = (REPO_ROOT / "components/timer/CMakeLists.txt").read_text()

    assert "ep_components_timer" in host_cmake
    assert "ep_components_timer" in linux_cmake
    assert "ep_components_log" in host_cmake
    assert "ep_components_log" in linux_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
```

- [ ] **Step 2: 运行单测，确认 linux demo 断言失败**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected: FAIL，失败点包含：

```text
assert 'ep_components_log' in linux_cmake
```

- [ ] **Step 3: 提交失败测试**

Run:

```bash
git add tests/api_contract/test_platform_bootstrap.py
git commit -m "test: 约束 demo 平台链接 log 组件"
```

## Task 3: 接入 framework log 初始化实现

**Files:**
- Modify: `core/src/ep_framework.c`
- Modify: `core/CMakeLists.txt`

- [ ] **Step 1: 修改 framework 初始化代码**

将 `core/src/ep_framework.c` 改为：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_log.h"
#include "ep_event.h"
#include "ep_timer.h"

int ep_framework_init(void)
{
    int rc = ep_log_init();
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
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
)
```

- [ ] **Step 3: 运行 framework 单测，确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
1 passed
```

- [ ] **Step 4: 提交 framework 实现**

Run:

```bash
git add core/src/ep_framework.c core/CMakeLists.txt
git commit -m "feat: 接入 framework log 初始化"
```

## Task 4: 接入 linux demo log 组件链接

**Files:**
- Modify: `platforms/linux/demo_family/CMakeLists.txt`

- [ ] **Step 1: 修改 linux demo CMake 链接**

将 `platforms/linux/demo_family/CMakeLists.txt` 改为：

```cmake
add_executable(ep_platform_linux_demo
  startup/main.c
  osal_port/ep_linux_osal_stub.c
  hal_port/ep_linux_hal_stub.c
  component_port/ep_linux_component_stub.c
)

target_include_directories(ep_platform_linux_demo
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_linux_demo
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
)
```

- [ ] **Step 2: 运行平台链接契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: 提交 linux demo 链接实现**

Run:

```bash
git add platforms/linux/demo_family/CMakeLists.txt
git commit -m "build: 让 linux demo 链接 log 组件"
```

## Task 5: 验证构建闭环并收尾

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
Built target ep_platform_host_posix
```

- [ ] **Step 4: 运行 host POSIX demo**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected: exit code 0。

本阶段不新增 framework 日志输出语句，所以这里不要求 stdout 出现新的日志内容。

- [ ] **Step 5: 检查 diff 空白问题**

Run:

```bash
git diff --check
```

Expected: exit code 0，无输出。

- [ ] **Step 6: 检查最近提交和工作区状态**

Run:

```bash
git status --short --branch
git log --oneline --decorate -5
```

Expected:

```text
## feature/framework-log-init
```

最近提交包含：

```text
build: 让 linux demo 链接 log 组件
feat: 接入 framework log 初始化
test: 约束 demo 平台链接 log 组件
test: 约束 framework log 初始化顺序
```

## PR 内容建议

标题：

```text
feat: 接入 framework log 初始化
```

正文：

```markdown
## Summary
- 让 `ep_framework_init()` 按 `log -> event -> timer` 初始化基础组件
- 让 `core` 只依赖 `ep_log.h` 公共接口，不暴露 EasyLogger
- 让 linux demo 补充链接 `ep_components_log`，保持 host/linux 构建闭环

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- 本 PR 不新增 framework 日志输出语句
- 本 PR 不接入真实 Luban-Lite/RT-Thread port
```
