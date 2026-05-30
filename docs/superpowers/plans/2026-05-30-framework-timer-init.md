# Framework Timer Init Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `ep_framework_init()` 在初始化 event bus 后继续初始化 timer 组件，使 framework 启动链路默认具备定时器能力。

**Architecture:** core 层继续负责编排基础组件初始化，先调用 `ep_event_init()`，成功后调用 `ep_timer_init()`，错误码原样返回给 `ep_framework_start()`。构建上给 `ep_core` 增加 timer 公共头路径，最终可执行文件由平台 CMake 链接 `ep_components_timer`，timer 再通过 public 依赖传递 `ep_components_event`。

**Tech Stack:** C11、CMake、`components/event`、`components/timer`、OSAL time/thread/mutex、host POSIX、Linux demo skeleton、pytest。

---

## 文件结构

- Modify: `tests/host_unit/test_framework_bootstrap.py`
  - 锁定 framework 到 timer 的源码契约：include `ep_timer.h`、先调用 `ep_event_init()`、再调用 `ep_timer_init()`，并确认 `ep_core` 有 timer include 路径。
- Modify: `core/src/ep_framework.c`
  - 在 `ep_framework_init()` 中按顺序初始化 event 和 timer，并保持失败传播。
- Modify: `core/CMakeLists.txt`
  - 给 `ep_core` 增加 `components/timer/include` 私有 include 路径。
- Modify: `tests/api_contract/test_platform_bootstrap.py`
  - 锁定 host POSIX 和 Linux demo 都链接 timer 组件，并确认 timer public 依赖 event。
- Modify: `platforms/linux/demo_family/CMakeLists.txt`
  - 让 Linux demo 链接 `ep_components_timer`，由 timer public 依赖带入 event。
- Modify: `platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c`
  - 给 Linux demo skeleton 补齐 timer 链接需要的 OSAL time 符号。

## Task 1: 锁定 framework 到 timer 的初始化契约

**Files:**
- Modify: `tests/host_unit/test_framework_bootstrap.py`
- Modify: `core/src/ep_framework.c`
- Modify: `core/CMakeLists.txt`

- [ ] **Step 1: 写失败的 framework timer 接入测试**

修改 `tests/host_unit/test_framework_bootstrap.py` 的 `test_framework_bootstrap_symbols_exist()`。

将函数改为：

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
    assert '#include "ep_event.h"' in source
    assert '#include "ep_timer.h"' in source
    assert "int rc = ep_event_init();" in source
    assert "return ep_event_init();" not in source
    assert "return ep_timer_init();" in source
    assert source.index("ep_event_init()") < source.index("ep_timer_init()")
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake
```

- [ ] **Step 2: 运行测试，确认因为 timer 尚未接入而失败**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist -v
```

Expected:

```text
FAILED tests/host_unit/test_framework_bootstrap.py::test_framework_bootstrap_symbols_exist
assert '#include "ep_timer.h"' in source
```

- [ ] **Step 3: 修改 `core/src/ep_framework.c`**

将 `core/src/ep_framework.c` 改为：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_event.h"
#include "ep_timer.h"

int ep_framework_init(void)
{
    int rc = ep_event_init();
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

- [ ] **Step 4: 修改 `core/CMakeLists.txt`**

将 `target_include_directories(ep_core ...)` 改为：

```cmake
target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
)
```

- [ ] **Step 5: 运行 framework bootstrap 测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_framework_bootstrap.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交 framework timer 初始化接入**

Run:

```bash
git add core/src/ep_framework.c core/CMakeLists.txt tests/host_unit/test_framework_bootstrap.py
git commit -m "feat: 接入 framework timer 初始化"
```

## Task 2: 锁定平台可执行文件的 timer 链接契约

**Files:**
- Modify: `tests/api_contract/test_platform_bootstrap.py`
- Modify: `platforms/linux/demo_family/CMakeLists.txt`
- Modify: `platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c`

- [ ] **Step 1: 写失败的平台链接契约测试**

修改 `tests/api_contract/test_platform_bootstrap.py` 的 `test_platform_executables_link_framework_components()`。

将函数改为：

```python
def test_platform_executables_link_framework_components():
    linux_cmake = (REPO_ROOT / "platforms/linux/demo_family/CMakeLists.txt").read_text()
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    timer_cmake = (REPO_ROOT / "components/timer/CMakeLists.txt").read_text()

    assert "ep_components_timer" in host_cmake
    assert "ep_components_timer" in linux_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
```

- [ ] **Step 2: 运行测试，确认因为 Linux demo 尚未链接 timer 而失败**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected:

```text
FAILED tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components
assert 'ep_components_timer' in linux_cmake
```

- [ ] **Step 3: 修改 Linux demo CMake 链接 timer**

将 `platforms/linux/demo_family/CMakeLists.txt` 的 `target_link_libraries()` 改为：

```cmake
target_link_libraries(ep_platform_linux_demo
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
)
```

说明：不再直接链接 `ep_components_event`，因为 `ep_components_timer` 已经通过 `PUBLIC` 依赖传递 `ep_components_event`。

- [ ] **Step 4: 给 Linux demo stub 补齐 OSAL time 符号**

修改 `platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c` 的 include 区域：

```c
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"
#include "ep_osal_time.h"
```

在 `ep_linux_osal_stub()` 后追加：

```c
uint64_t ep_time_now_ms(void)
{
    return 0u;
}

void ep_sleep_ms(unsigned int timeout_ms)
{
    (void)timeout_ms;
}
```

修改后的文件开头应为：

```c
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"
#include "ep_osal_time.h"

int ep_linux_osal_stub(void)
{
    return 0;
}

uint64_t ep_time_now_ms(void)
{
    return 0u;
}

void ep_sleep_ms(unsigned int timeout_ms)
{
    (void)timeout_ms;
}

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)
{
    (void)name;
    (void)arg;

    if (thread == 0 || entry == 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_UNSUPPORTED;
}
```

- [ ] **Step 5: 运行平台链接契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_executables_link_framework_components -v
```

Expected:

```text
1 passed
```

- [ ] **Step 6: 运行平台 demo 构建测试，确认 Linux demo 可链接**

Run:

```bash
pytest tests/api_contract/test_platform_bootstrap.py::test_platform_demo_targets_configure_and_build -v
```

Expected:

```text
1 passed
```

- [ ] **Step 7: 提交平台 timer 链接接入**

Run:

```bash
git add tests/api_contract/test_platform_bootstrap.py platforms/linux/demo_family/CMakeLists.txt platforms/linux/demo_family/osal_port/ep_linux_osal_stub.c
git commit -m "build: 接入 timer 平台链接"
```

## Task 3: 完整验证和 PR 前收尾

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
构建成功，输出包含 Built target ep_platform_host_posix
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
工作区干净，最近提交包含 framework timer 初始化和平台 timer 链接两个提交
```

- [ ] **Step 7: PR 标题和正文使用中文**

PR 标题：

```text
feat: 接入 framework timer 初始化
```

PR 正文：

```markdown
## 变更内容

- 让 `ep_framework_init()` 在 event 初始化成功后调用 `ep_timer_init()`
- 为 `ep_core` 增加 timer 公共头文件 include 路径
- 让 host 和 Linux demo 的平台可执行文件链接 `ep_components_timer`
- 为 Linux demo skeleton 补齐 timer 链接需要的 OSAL time stub
- 补充 framework timer 初始化和平台 timer 链接契约测试

## 测试

- [ ] `pytest tests/host_unit tests/api_contract -v`
- [ ] `cmake -S . -B build`
- [ ] `cmake --build build`
- [ ] `./build/platforms/host/posix/ep_platform_host_posix`
- [ ] `git diff --check`
```

## 自检结果

- 设计文档要求均有对应任务：
  - `ep_framework_init()` 顺序调用 `ep_event_init()` 和 `ep_timer_init()`：Task 1。
  - 初始化失败原样传播，不进入 `app_main()`：Task 1 保持 `ep_framework_start()` 现有失败返回逻辑。
  - `ep_core` 能 include `ep_timer.h`：Task 1 修改 `core/CMakeLists.txt`。
  - `components/timer` 保持平台无关：本计划不修改 timer 组件实现。
  - host 和 Linux demo 最终链接 timer：Task 2。
  - 本阶段不接入 Luban-Lite、RT-Thread 或真实板级 SDK：本计划只改 host/Linux demo skeleton 和 core。
- 任务按 TDD 顺序拆分：先改测试看到失败，再改实现，再运行对应测试。
- 每个代码修改步骤都给出完整代码片段或完整目标块。
