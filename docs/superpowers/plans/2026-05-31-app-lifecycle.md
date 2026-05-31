# App Lifecycle Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `app_main()` 执行一个最小应用生命周期流程：启动日志、订阅事件、启动短定时器、等待事件回调、成功后自动退出。

**Architecture:** 第一版只在 `app/` 层实现，不新增独立 app lifecycle 模块。`app/main.c` 通过公共组件接口使用 log、event、timer 和 OSAL time；`app/include/app_events.h` 定义应用内部事件 ID。测试先锁定应用层依赖边界和 host bin 可观察输出，再实现最小代码。

**Tech Stack:** C11、CMake、pytest、host POSIX 平台、现有 `ep_log`、`ep_event`、`ep_timer`、`ep_osal_time`、`ep_osal_err`。

---

## 文件结构

- Create: `app/include/app_events.h`
  - 只定义应用内部事件 ID。
  - 第一版包含 `APP_EVENT_TIMER_DONE`。
- Modify: `app/main.c`
  - 实现最小应用生命周期流程。
  - 不包含平台原生头文件。
- Modify: `app/CMakeLists.txt`
  - 给 `ep_app` 增加对 `components/log/include`、`components/event/include`、`components/timer/include`、`osal/include` 的 include 路径。
  - 给 `ep_app` 链接需要的公共组件目标，保证 app 可单独编译。
- Modify: `tests/host_unit/test_host_posix_bootstrap.py`
  - 增加 app 运行骨架结构测试。
  - 扩展 host bin smoke 测试，断言应用启动和完成日志。

## Task 1: 写应用运行骨架红灯测试

**Files:**
- Modify: `tests/host_unit/test_host_posix_bootstrap.py`
- Expected later Create: `app/include/app_events.h`
- Expected later Modify: `app/main.c`
- Expected later Modify: `app/CMakeLists.txt`

- [ ] **Step 1: 添加结构测试**

在 `tests/host_unit/test_host_posix_bootstrap.py` 中，放在 `test_host_posix_cmake_target_is_named()` 后面，新增：

```python
def test_app_lifecycle_uses_framework_services_without_platform_headers():
    app_events = REPO_ROOT / "app/include/app_events.h"
    app_main = REPO_ROOT / "app/main.c"
    app_cmake = REPO_ROOT / "app/CMakeLists.txt"

    assert app_events.exists()

    events_header = app_events.read_text(encoding="utf-8")
    source = app_main.read_text(encoding="utf-8")
    cmake = app_cmake.read_text(encoding="utf-8")

    assert "APP_EVENT_TIMER_DONE" in events_header
    assert "#define APP_EVENT_TIMER_DONE 1000" in events_header

    assert '#include "app_events.h"' in source
    assert '#include "app_main.h"' in source
    assert '#include "ep_event.h"' in source
    assert '#include "ep_log.h"' in source
    assert '#include "ep_osal_err.h"' in source
    assert '#include "ep_osal_time.h"' in source
    assert '#include "ep_timer.h"' in source

    forbidden_headers = [
        "<pthread.h>",
        "<signal.h>",
        "<unistd.h>",
        "\"pthread.h\"",
        "\"signal.h\"",
        "\"unistd.h\"",
    ]
    for header in forbidden_headers:
        assert header not in source

    assert "APP_TIMER_ID_SELF_TEST" in source
    assert "APP_TIMER_TIMEOUT_MS" in source
    assert "APP_WAIT_STEP_MS" in source
    assert "APP_WAIT_TIMEOUT_MS" in source
    assert "static volatile int g_app_timer_done;" in source
    assert "static void app_timer_done_handler(" in source
    assert "ep_event_subscribe(APP_EVENT_TIMER_DONE, app_timer_done_handler, 0)" in source
    assert "ep_timer_start(APP_TIMER_ID_SELF_TEST, APP_TIMER_TIMEOUT_MS, APP_EVENT_TIMER_DONE)" in source
    assert "ep_sleep_ms(APP_WAIT_STEP_MS)" in source
    assert "return EP_ERR_TIMEOUT;" in source
    assert "EP_LOGI(\"app\", \"app lifecycle start\")" in source
    assert "EP_LOGI(\"app\", \"app lifecycle done\")" in source
    assert "EP_LOGE(\"app\", \"app lifecycle timeout\")" in source

    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/log/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/event/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/components/timer/include" in cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in cmake
    assert "ep_components_log" in cmake
    assert "ep_components_event" in cmake
    assert "ep_components_timer" in cmake
```

- [ ] **Step 2: 扩展 host bin smoke 测试**

在同一个文件的 `test_host_posix_executable_runs_successfully()` 结尾，保留现有 returncode 断言，并追加：

```python
    assert "app lifecycle start" in run.stdout
    assert "app lifecycle done" in run.stdout
    assert "app lifecycle timeout" not in run.stdout
```

- [ ] **Step 3: 运行测试确认红灯**

Run:

```bash
pytest tests/host_unit/test_host_posix_bootstrap.py::test_app_lifecycle_uses_framework_services_without_platform_headers \
       tests/host_unit/test_host_posix_bootstrap.py::test_host_posix_executable_runs_successfully -v
```

Expected:

```text
FAILED tests/host_unit/test_host_posix_bootstrap.py::test_app_lifecycle_uses_framework_services_without_platform_headers
```

失败原因应包含：

```text
AssertionError: assert False
```

或说明 `app/include/app_events.h` 不存在。host bin smoke 也应因为缺少应用日志断言失败。

不要在红灯前写实现代码。

## Task 2: 增加应用事件头文件

**Files:**
- Create: `app/include/app_events.h`
- Test: `tests/host_unit/test_host_posix_bootstrap.py`

- [ ] **Step 1: 创建应用事件头文件**

Create `app/include/app_events.h`:

```c
#ifndef APP_EVENTS_H
#define APP_EVENTS_H

#define APP_EVENT_TIMER_DONE 1000

#endif
```

- [ ] **Step 2: 运行结构测试确认仍有红灯**

Run:

```bash
pytest tests/host_unit/test_host_posix_bootstrap.py::test_app_lifecycle_uses_framework_services_without_platform_headers -v
```

Expected:

```text
FAILED
```

失败原因应转移到 `app/main.c` 或 `app/CMakeLists.txt` 还没包含对应内容。

- [ ] **Step 3: 提交事件头**

```bash
git add app/include/app_events.h tests/host_unit/test_host_posix_bootstrap.py
git commit -m "feat: 增加应用事件定义"
```

## Task 3: 实现 app_main 最小生命周期

**Files:**
- Modify: `app/main.c`
- Test: `tests/host_unit/test_host_posix_bootstrap.py`

- [ ] **Step 1: 替换 `app/main.c`**

Replace `app/main.c` with:

```c
#include "app_events.h"
#include "app_main.h"
#include "ep_event.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_timer.h"

#define APP_TIMER_ID_SELF_TEST 1
#define APP_TIMER_TIMEOUT_MS 50u
#define APP_WAIT_STEP_MS 10u
#define APP_WAIT_TIMEOUT_MS 500u

static volatile int g_app_timer_done;

static void app_timer_done_handler(
    ep_event_id_t event_id,
    const void *payload,
    size_t payload_size,
    void *user_data
)
{
    (void)payload;
    (void)payload_size;
    (void)user_data;

    if (event_id == APP_EVENT_TIMER_DONE) {
        g_app_timer_done = 1;
    }
}

int app_main(void)
{
    unsigned int waited_ms = 0u;
    int rc;

    g_app_timer_done = 0;

    EP_LOGI("app", "app lifecycle start");

    rc = ep_event_subscribe(APP_EVENT_TIMER_DONE, app_timer_done_handler, 0);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_timer_start(APP_TIMER_ID_SELF_TEST, APP_TIMER_TIMEOUT_MS, APP_EVENT_TIMER_DONE);
    if (rc != EP_OK) {
        return rc;
    }

    while (!g_app_timer_done && waited_ms < APP_WAIT_TIMEOUT_MS) {
        ep_sleep_ms(APP_WAIT_STEP_MS);
        waited_ms += APP_WAIT_STEP_MS;
    }

    if (!g_app_timer_done) {
        EP_LOGE("app", "app lifecycle timeout");
        return EP_ERR_TIMEOUT;
    }

    EP_LOGI("app", "app lifecycle done");
    return 0;
}
```

- [ ] **Step 2: 运行结构测试确认仍可能因 CMake 红灯**

Run:

```bash
pytest tests/host_unit/test_host_posix_bootstrap.py::test_app_lifecycle_uses_framework_services_without_platform_headers -v
```

Expected:

```text
FAILED
```

如果 `app/CMakeLists.txt` 尚未更新，失败原因应包含缺少 include 路径或组件 target 名称。若这个测试已经 PASS，也继续执行 Task 4，确保真实构建通过。

- [ ] **Step 3: 提交 app_main 实现**

```bash
git add app/main.c
git commit -m "feat: 实现应用运行骨架"
```

## Task 4: 更新 app CMake 依赖并跑通 host bin

**Files:**
- Modify: `app/CMakeLists.txt`
- Test: `tests/host_unit/test_host_posix_bootstrap.py`

- [ ] **Step 1: 更新 `app/CMakeLists.txt`**

Replace `app/CMakeLists.txt` with:

```cmake
add_library(ep_app STATIC
  main.c
)

target_include_directories(ep_app
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_app
  PRIVATE
    ep_components_log
    ep_components_event
    ep_components_timer
)
```

- [ ] **Step 2: 运行 host posix 测试确认绿灯**

Run:

```bash
pytest tests/host_unit/test_host_posix_bootstrap.py -v
```

Expected:

```text
4 passed
```

- [ ] **Step 3: 手动构建并运行 host bin**

Run:

```bash
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
```

Expected output includes:

```text
app lifecycle start
app lifecycle done
```

Expected output does not include:

```text
app lifecycle timeout
```

- [ ] **Step 4: 提交 CMake 和测试更新**

```bash
git add app/CMakeLists.txt tests/host_unit/test_host_posix_bootstrap.py
git commit -m "test: 验证应用运行骨架"
```

## Task 5: 完整验证和收尾

**Files:**
- Verify only

- [ ] **Step 1: 运行完整测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
66 passed
```

如果实际数量不是 `66 passed`，但所有测试通过，要记录实际通过数量，不要改测试数量去迎合计划。

- [ ] **Step 2: 运行完整构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
Build files have been written
Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 host bin**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
app lifecycle start
app lifecycle done
```

- [ ] **Step 4: 检查空白和分支状态**

Run:

```bash
git diff --check
git status --short --branch
git log --oneline --decorate --graph --max-count=8
git diff --stat origin/main..HEAD
```

Expected:

- `git diff --check` 无输出。
- `git status --short --branch` 不包含未提交文件。
- diff stat 只包含 `app/` 和 `tests/host_unit/test_host_posix_bootstrap.py`。

- [ ] **Step 5: 创建 PR**

```bash
git push -u origin feature/app-lifecycle
gh pr create --base main --head feature/app-lifecycle --title "feat: 实现应用运行骨架" --body "$(cat <<'EOF'
## Summary
- 新增应用内部事件定义 `APP_EVENT_TIMER_DONE`
- `app_main()` 执行启动日志、事件订阅、短定时器、等待回调和自动退出流程
- host smoke 测试验证应用日志和自动退出行为

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- 本 PR 不做常驻主循环
- 本 PR 不接设备抽象、Luban-Lite、RT-Thread 或真实芯片 SDK
- app 层不包含平台原生头文件
EOF
)"
```
