# Host Timer Implementation Plan

> **给 agentic 执行者:** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务逐步执行。本计划使用 checkbox（`- [ ]`）跟踪每个步骤。

**目标:** 实现第一版平台无关 `components/timer` 全局一次性定时器组件，并让 host POSIX 测试验证初始化、启动、停止、到期事件、重启和错误路径。

**架构:** `components/timer` 暴露 `ep_timer.h`，实现文件只依赖 OSAL time/thread/mutex/err 公共接口和 `components/event` 公共接口。全局 timer service 在 `ep_timer_init()` 中初始化 event bus、创建互斥锁和后台扫描线程；`ep_timer_start()` 写入固定 timer 表，扫描线程到期后释放 timer lock，再通过 `ep_event_publish()` 投递空 payload 事件。

**技术栈:** C11、CMake、OSAL 公共接口、`components/event`、host POSIX OSAL 实现、pytest 生成 C smoke 程序。

---

## 文件结构

- Create: `components/timer/include/ep_timer.h`
  - timer 公共头文件，只暴露平台无关类型和函数。
- Create: `components/timer/src/ep_timer.c`
  - timer 平台无关实现，只 include OSAL 公共头和 event 公共头。
- Create: `components/timer/CMakeLists.txt`
  - 构建 `ep_components_timer` 静态库，并 public 传递 `ep_components_event`。
- Modify: `CMakeLists.txt`
  - 新增 `add_subdirectory(components/timer)`。
- Modify: `platforms/host/posix/CMakeLists.txt`
  - host POSIX 可执行文件链接 `ep_components_timer`，方便全仓构建验证 timer 组件。
- Create: `tests/api_contract/test_timer_headers.py`
  - 验证 `ep_timer.h` 可独立编译、接口签名稳定、没有平台原生头文件。
- Create: `tests/host_unit/test_host_timer.py`
  - 生成 C 程序验证 CMake 接入、初始化、一次性到期投递、停止、重启、未初始化和容量错误路径。

## Task 1: 锁定 timer 公共接口契约

**Files:**
- Create: `tests/api_contract/test_timer_headers.py`
- Create: `components/timer/include/ep_timer.h`

- [ ] **Step 1: 写失败的公共头文件契约测试**

创建 `tests/api_contract/test_timer_headers.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TIMER_INCLUDE = REPO_ROOT / "components" / "timer" / "include"
EVENT_INCLUDE = REPO_ROOT / "components" / "event" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_timer_header_does_not_include_platform_native_headers():
    header = TIMER_INCLUDE / "ep_timer.h"

    assert header.exists(), "Expected components/timer/include/ep_timer.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = ["pthread.h", "rtthread.h", "unistd.h", "sys/", "platforms/"]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_timer.h must stay platform-neutral, found: {found}"


def test_timer_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "timer_header_smoke.c"
    obj = tmp_path / "timer_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_timer.h"
            #include "ep_timer.h"

            int main(void)
            {
                ep_timer_id_t timer_id = 1;
                ep_event_id_t event_id = 10;
                int (*init_fn)(void) = ep_timer_init;
                int (*start_fn)(ep_timer_id_t, unsigned int, ep_event_id_t) = ep_timer_start;
                int (*stop_fn)(ep_timer_id_t) = ep_timer_stop;

                return (timer_id == 1 && event_id == 10 && init_fn && start_fn && stop_fn) ? 0 : 1;
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
            str(TIMER_INCLUDE),
            "-I",
            str(EVENT_INCLUDE),
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
pytest tests/api_contract/test_timer_headers.py -v
```

Expected:

```text
FAILED tests/api_contract/test_timer_headers.py::test_timer_header_does_not_include_platform_native_headers
Expected components/timer/include/ep_timer.h to exist
```

- [ ] **Step 3: 写最小公共头文件**

创建 `components/timer/include/ep_timer.h`：

```c
#ifndef EP_TIMER_H
#define EP_TIMER_H

#include "ep_event.h"

typedef int ep_timer_id_t;

int ep_timer_init(void);
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id);
int ep_timer_stop(ep_timer_id_t timer_id);

#endif
```

- [ ] **Step 4: 运行接口契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_timer_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交公共接口契约**

Run:

```bash
git add tests/api_contract/test_timer_headers.py components/timer/include/ep_timer.h
git commit -m "test: 增加 timer 公共接口契约"
```

## Task 2: 建立 timer 组件构建骨架

**Files:**
- Create: `tests/host_unit/test_host_timer.py`
- Create: `components/timer/CMakeLists.txt`
- Create: `components/timer/src/ep_timer.c`
- Modify: `CMakeLists.txt`
- Modify: `platforms/host/posix/CMakeLists.txt`

- [ ] **Step 1: 写失败的 CMake 接入测试**

创建 `tests/host_unit/test_host_timer.py`，先放入 CMake 接入测试：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_timer_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    timer_cmake_path = REPO_ROOT / "components/timer/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/timer)" in root_cmake
    assert timer_cmake_path.exists()

    timer_cmake = timer_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_timer STATIC" in timer_cmake
    assert "src/ep_timer.c" in timer_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
    assert "ep_components_timer" in host_cmake
```

- [ ] **Step 2: 运行测试，确认因为 CMake 未接入而失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_timer_component_is_wired_into_cmake -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_timer_component_is_wired_into_cmake
assert 'add_subdirectory(components/timer)' in ...
```

- [ ] **Step 3: 新增 timer 组件 CMake**

创建 `components/timer/CMakeLists.txt`：

```cmake
add_library(ep_components_timer STATIC
  src/ep_timer.c
)

target_include_directories(ep_components_timer
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_components_timer
  PUBLIC
    ep_components_event
)
```

- [ ] **Step 4: 新增临时最小 timer 实现**

创建 `components/timer/src/ep_timer.c`：

```c
#include "ep_timer.h"
#include "ep_osal_err.h"

int ep_timer_init(void)
{
    return EP_ERR_UNSUPPORTED;
}

int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    (void)timer_id;
    (void)timeout_ms;
    (void)event_id;

    return EP_ERR_UNSUPPORTED;
}

int ep_timer_stop(ep_timer_id_t timer_id)
{
    (void)timer_id;

    return EP_ERR_UNSUPPORTED;
}
```

- [ ] **Step 5: 接入顶层 CMake 和 host POSIX target**

修改 `CMakeLists.txt`，在 event 后面加入：

```cmake
add_subdirectory(components/timer)
```

修改 `platforms/host/posix/CMakeLists.txt`，在 `target_link_libraries(ep_platform_host_posix PRIVATE ...)` 中加入：

```cmake
    ep_components_timer
```

- [ ] **Step 6: 运行 CMake 接入测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_timer_component_is_wired_into_cmake -v
```

Expected:

```text
1 passed
```

- [ ] **Step 7: 运行 CMake 构建 smoke，确认临时实现可构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
build 退出码为 0
```

- [ ] **Step 8: 提交构建骨架**

Run:

```bash
git add CMakeLists.txt platforms/host/posix/CMakeLists.txt components/timer/CMakeLists.txt components/timer/src/ep_timer.c tests/host_unit/test_host_timer.py
git commit -m "build: 接入 timer 组件骨架"
```

## Task 3: 实现 timer 初始化和未初始化错误路径

**Files:**
- Modify: `tests/host_unit/test_host_timer.py`
- Modify: `components/timer/src/ep_timer.c`

- [ ] **Step 1: 写失败的初始化和错误路径测试**

在 `tests/host_unit/test_host_timer.py` 追加：

```python
def test_host_timer_init_and_invalid_arguments(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_invalid_smoke.c"
    executable = tmp_path / "host_timer_invalid_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_timer.h"
            #include "ep_osal_err.h"

            int main(void)
            {
                if (ep_timer_start(1, 10, 100) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_timer_stop(1) != EP_ERR_UNSUPPORTED) {
                    return 2;
                }

                if (ep_timer_init() != EP_OK) {
                    return 3;
                }

                if (ep_timer_init() != EP_OK) {
                    return 4;
                }

                if (ep_timer_start(-1, 10, 100) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_timer_stop(-1) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_timer_stop(999) != EP_ERR_INVAL) {
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
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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
```

- [ ] **Step 2: 运行测试，确认临时实现失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_init_and_invalid_arguments -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_host_timer_init_and_invalid_arguments
assert run_result.returncode == 0
```

- [ ] **Step 3: 实现初始化、全局状态和基础参数检查**

替换 `components/timer/src/ep_timer.c`：

```c
#include "ep_timer.h"
#include "ep_event.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_thread.h"
#include "ep_osal_time.h"

#include <stdint.h>

#define EP_TIMER_MAX_TIMERS 16u
#define EP_TIMER_SCAN_PERIOD_MS 10u

struct ep_timer_entry {
    int active;
    ep_timer_id_t timer_id;
    ep_event_id_t event_id;
    uint64_t deadline_ms;
};

static ep_thread_t *g_timer_thread;
static ep_mutex_t *g_timer_lock;
static struct ep_timer_entry g_timers[EP_TIMER_MAX_TIMERS];
static int g_timer_started;

static void *ep_timer_scan_loop(void *arg)
{
    (void)arg;

    for (;;) {
        ep_sleep_ms(EP_TIMER_SCAN_PERIOD_MS);
    }

    return 0;
}

int ep_timer_init(void)
{
    int rc;

    if (g_timer_started) {
        return EP_OK;
    }

    rc = ep_event_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_mutex_create(&g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_thread_create(&g_timer_thread, "timer", ep_timer_scan_loop, 0);
    if (rc != EP_OK) {
        return rc;
    }

    g_timer_started = 1;
    return EP_OK;
}

int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    (void)timeout_ms;
    (void)event_id;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_timer_stop(ep_timer_id_t timer_id)
{
    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    return EP_ERR_INVAL;
}
```

- [ ] **Step 4: 运行初始化和错误路径测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_init_and_invalid_arguments -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交初始化行为**

Run:

```bash
git add components/timer/src/ep_timer.c tests/host_unit/test_host_timer.py
git commit -m "feat: 实现 timer 初始化"
```

## Task 4: 实现 timer 到期投递事件

**Files:**
- Modify: `tests/host_unit/test_host_timer.py`
- Modify: `components/timer/src/ep_timer.c`

- [ ] **Step 1: 写失败的到期投递测试**

在 `tests/host_unit/test_host_timer.py` 追加：

```python
def test_host_timer_publishes_event_when_expired(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_expire_smoke.c"
    executable = tmp_path / "host_timer_expire_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int call_count;
                ep_event_id_t event_id;
                size_t payload_size;
            };

            static void timer_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)payload;
                state->event_id = event_id;
                state->payload_size = payload_size;
                state->call_count += 1;
            }

            static int wait_for_count(volatile int *value, int expected)
            {
                int i;

                for (i = 0; i < 100; ++i) {
                    if (*value == expected) {
                        return 0;
                    }
                    ep_sleep_ms(5);
                }

                return 1;
            }

            int main(void)
            {
                struct observed_state state;

                state.call_count = 0;
                state.event_id = 0;
                state.payload_size = 99;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(500, timer_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_timer_start(1, 20, 500) != EP_OK) {
                    return 3;
                }

                if (wait_for_count(&state.call_count, 1) != 0) {
                    return 4;
                }

                if (state.event_id != 500) {
                    return 5;
                }

                if (state.payload_size != 0) {
                    return 6;
                }

                ep_sleep_ms(60);
                if (state.call_count != 1) {
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
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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
```

- [ ] **Step 2: 运行测试，确认因为 timer 不投递事件而失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_publishes_event_when_expired -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_host_timer_publishes_event_when_expired
assert run_result.returncode == 0
```

- [ ] **Step 3: 实现 start 写表和扫描线程投递事件**

更新 `components/timer/src/ep_timer.c`。

在 `struct ep_timer_entry` 后新增：

```c
struct ep_timer_expired_event {
    ep_event_id_t event_id;
};
```

替换 `ep_timer_scan_loop()`：

```c
static void *ep_timer_scan_loop(void *arg)
{
    (void)arg;

    for (;;) {
        struct ep_timer_expired_event expired[EP_TIMER_MAX_TIMERS];
        size_t expired_count = 0u;
        uint64_t now_ms;
        size_t i;

        ep_sleep_ms(EP_TIMER_SCAN_PERIOD_MS);
        now_ms = ep_time_now_ms();

        if (ep_mutex_lock(g_timer_lock) != EP_OK) {
            continue;
        }

        for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
            if (g_timers[i].active && g_timers[i].deadline_ms <= now_ms) {
                expired[expired_count].event_id = g_timers[i].event_id;
                expired_count += 1u;
                g_timers[i].active = 0;
            }
        }

        (void)ep_mutex_unlock(g_timer_lock);

        for (i = 0u; i < expired_count; ++i) {
            (void)ep_event_publish(expired[i].event_id, 0, 0, 0);
        }
    }

    return 0;
}
```

替换 `ep_timer_start()`：

```c
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    uint64_t deadline_ms;
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    deadline_ms = ep_time_now_ms() + timeout_ms;

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (!g_timers[i].active) {
            g_timers[i].active = 1;
            g_timers[i].timer_id = timer_id;
            g_timers[i].deadline_ms = deadline_ms;
            g_timers[i].event_id = event_id;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }
    }

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_OK;
}
```

- [ ] **Step 4: 运行到期投递测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_publishes_event_when_expired -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 运行前面 timer 测试，确认没有回归**

Run:

```bash
pytest tests/host_unit/test_host_timer.py -v
```

Expected:

```text
3 passed
```

- [ ] **Step 6: 提交到期投递行为**

Run:

```bash
git add components/timer/src/ep_timer.c tests/host_unit/test_host_timer.py
git commit -m "feat: 实现 timer 到期事件"
```

## Task 5: 覆盖停止、重启和容量错误路径

**Files:**
- Modify: `tests/host_unit/test_host_timer.py`
- Modify: `components/timer/src/ep_timer.c`

- [ ] **Step 1: 写停止 timer 的测试**

在 `tests/host_unit/test_host_timer.py` 追加：

```python
def test_host_timer_stop_prevents_pending_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_stop_smoke.c"
    executable = tmp_path / "host_timer_stop_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int call_count;
            };

            static void timer_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->call_count += 1;
            }

            int main(void)
            {
                struct observed_state state;

                state.call_count = 0;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(510, timer_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_timer_start(2, 80, 510) != EP_OK) {
                    return 3;
                }

                if (ep_timer_stop(2) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(140);
                if (state.call_count != 0) {
                    return 5;
                }

                if (ep_timer_stop(2) != EP_ERR_INVAL) {
                    return 6;
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
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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
```

- [ ] **Step 2: 运行停止测试，确认当前实现失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_stop_prevents_pending_event -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_host_timer_stop_prevents_pending_event
assert run_result.returncode == 0
```

- [ ] **Step 3: 实现停止 active timer**

替换 `components/timer/src/ep_timer.c` 中的 `ep_timer_stop()`：

```c
int ep_timer_stop(ep_timer_id_t timer_id)
{
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (g_timers[i].active && g_timers[i].timer_id == timer_id) {
            g_timers[i].active = 0;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }
    }

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_ERR_INVAL;
}
```

- [ ] **Step 4: 运行停止测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_stop_prevents_pending_event -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 写重启相同 timer id 的测试**

在 `tests/host_unit/test_host_timer.py` 追加：

```python
def test_host_timer_restart_same_id_updates_deadline_and_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_restart_smoke.c"
    executable = tmp_path / "host_timer_restart_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"
            #include "ep_timer.h"

            struct observed_state {
                volatile int first_count;
                volatile int second_count;
            };

            static void first_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->first_count += 1;
            }

            static void second_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->second_count += 1;
            }

            static int wait_for_count(volatile int *value, int expected)
            {
                int i;

                for (i = 0; i < 100; ++i) {
                    if (*value == expected) {
                        return 0;
                    }
                    ep_sleep_ms(5);
                }

                return 1;
            }

            int main(void)
            {
                struct observed_state state;

                state.first_count = 0;
                state.second_count = 0;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(520, first_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_event_subscribe(521, second_handler, &state) != EP_OK) {
                    return 3;
                }

                if (ep_timer_start(3, 120, 520) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(20);

                if (ep_timer_start(3, 20, 521) != EP_OK) {
                    return 5;
                }

                if (wait_for_count(&state.second_count, 1) != 0) {
                    return 6;
                }

                ep_sleep_ms(140);
                if (state.first_count != 0) {
                    return 7;
                }

                if (state.second_count != 1) {
                    return 8;
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
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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
```

- [ ] **Step 6: 运行重启测试，确认当前实现失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_restart_same_id_updates_deadline_and_event -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_host_timer_restart_same_id_updates_deadline_and_event
assert run_result.returncode == 0
```

- [ ] **Step 7: 实现相同 timer id 重启**

替换 `components/timer/src/ep_timer.c` 中的 `ep_timer_start()`：

```c
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    uint64_t deadline_ms;
    size_t first_free = EP_TIMER_MAX_TIMERS;
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    deadline_ms = ep_time_now_ms() + timeout_ms;

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (g_timers[i].active && g_timers[i].timer_id == timer_id) {
            g_timers[i].deadline_ms = deadline_ms;
            g_timers[i].event_id = event_id;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }

        if (!g_timers[i].active && first_free == EP_TIMER_MAX_TIMERS) {
            first_free = i;
        }
    }

    if (first_free != EP_TIMER_MAX_TIMERS) {
        g_timers[first_free].active = 1;
        g_timers[first_free].timer_id = timer_id;
        g_timers[first_free].event_id = event_id;
        g_timers[first_free].deadline_ms = deadline_ms;
    }

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_OK;
}
```

这个版本故意还不返回 `EP_ERR_BUSY`，容量错误由下一步测试驱动。

- [ ] **Step 8: 运行重启测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_restart_same_id_updates_deadline_and_event -v
```

Expected:

```text
1 passed
```

- [ ] **Step 9: 写容量错误测试**

在 `tests/host_unit/test_host_timer.py` 追加：

```python
def test_host_timer_capacity_limit(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_timer_capacity_smoke.c"
    executable = tmp_path / "host_timer_capacity_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_timer.h"

            int main(void)
            {
                int i;

                if (ep_timer_init() != EP_OK) {
                    return 1;
                }

                for (i = 0; i < 16; ++i) {
                    if (ep_timer_start(i, 10000, 600 + i) != EP_OK) {
                        return 2;
                    }
                }

                if (ep_timer_start(99, 10000, 700) != EP_ERR_BUSY) {
                    return 3;
                }

                if (ep_timer_start(0, 10000, 800) != EP_OK) {
                    return 4;
                }

                if (ep_timer_stop(0) != EP_OK) {
                    return 5;
                }

                if (ep_timer_start(99, 10000, 700) != EP_OK) {
                    return 6;
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
            str(REPO_ROOT / "components/timer/include"),
            "-I",
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/timer/src/ep_timer.c"),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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
```

- [ ] **Step 10: 运行容量测试，确认当前实现失败**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_capacity_limit -v
```

Expected:

```text
FAILED tests/host_unit/test_host_timer.py::test_host_timer_capacity_limit
assert run_result.returncode == 0
```

- [ ] **Step 11: 实现 timer 表满返回 `EP_ERR_BUSY`**

再次替换 `components/timer/src/ep_timer.c` 中的 `ep_timer_start()`：

```c
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id)
{
    uint64_t deadline_ms;
    size_t first_free = EP_TIMER_MAX_TIMERS;
    size_t i;
    int rc;

    if (!g_timer_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (timer_id < 0) {
        return EP_ERR_INVAL;
    }

    deadline_ms = ep_time_now_ms() + timeout_ms;

    rc = ep_mutex_lock(g_timer_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_TIMER_MAX_TIMERS; ++i) {
        if (g_timers[i].active && g_timers[i].timer_id == timer_id) {
            g_timers[i].deadline_ms = deadline_ms;
            g_timers[i].event_id = event_id;
            (void)ep_mutex_unlock(g_timer_lock);
            return EP_OK;
        }

        if (!g_timers[i].active && first_free == EP_TIMER_MAX_TIMERS) {
            first_free = i;
        }
    }

    if (first_free == EP_TIMER_MAX_TIMERS) {
        (void)ep_mutex_unlock(g_timer_lock);
        return EP_ERR_BUSY;
    }

    g_timers[first_free].active = 1;
    g_timers[first_free].timer_id = timer_id;
    g_timers[first_free].event_id = event_id;
    g_timers[first_free].deadline_ms = deadline_ms;

    (void)ep_mutex_unlock(g_timer_lock);
    return EP_OK;
}
```

- [ ] **Step 12: 运行容量测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py::test_host_timer_capacity_limit -v
```

Expected:

```text
1 passed
```

- [ ] **Step 13: 运行完整 timer 测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_timer.py tests/api_contract/test_timer_headers.py -v
```

Expected:

```text
所有收集到的 timer 测试通过
```

- [ ] **Step 14: 提交 timer 行为覆盖**

Run:

```bash
git add tests/host_unit/test_host_timer.py components/timer/src/ep_timer.c
git commit -m "test: 覆盖 timer 停止重启和容量"
```

## Task 6: 全量验证和最终提交准备

**Files:**
- Inspect: `components/timer/include/ep_timer.h`
- Inspect: `components/timer/src/ep_timer.c`
- Inspect: `components/timer/CMakeLists.txt`
- Inspect: `tests/api_contract/test_timer_headers.py`
- Inspect: `tests/host_unit/test_host_timer.py`

- [ ] **Step 1: 检查 timer 实现没有平台原生 include**

Run:

```bash
rg -n "pthread.h|rtthread.h|unistd.h|sys/|platforms/" components/timer components/timer/include components/timer/src
```

Expected:

```text
无输出，退出码可以是 1
```

- [ ] **Step 2: 检查 timer API 和 spec 一致**

Run:

```bash
rg -n "ep_timer_init|ep_timer_start|ep_timer_stop|EP_TIMER_MAX_TIMERS|EP_TIMER_SCAN_PERIOD_MS" components/timer docs/superpowers/specs/2026-05-30-host-timer-design.md
```

Expected:

```text
能看到 ep_timer_init、ep_timer_start、ep_timer_stop
能看到 EP_TIMER_MAX_TIMERS 16 和 EP_TIMER_SCAN_PERIOD_MS 10
```

- [ ] **Step 3: 运行 host 和 API 契约测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
所有测试通过
```

- [ ] **Step 4: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
两个命令退出码都是 0
```

- [ ] **Step 5: 运行 host POSIX 可执行文件**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
命令退出码为 0
```

- [ ] **Step 6: 检查 Git diff**

Run:

```bash
git diff --check
git status --short
```

Expected:

```text
git diff --check 无输出
git status --short 只显示本次 timer 相关文件
```

- [ ] **Step 7: 如有未提交变更，做最后一次提交**

Run:

```bash
git add components/timer CMakeLists.txt platforms/host/posix/CMakeLists.txt tests/api_contract/test_timer_headers.py tests/host_unit/test_host_timer.py
git commit -m "feat: 实现 Host timer 组件"
```

如果 Task 1 到 Task 5 已经把所有变更分别提交完，这一步应显示没有可提交内容，不需要强行创建空提交。

## 实现完成后的 PR 内容

标题：

```text
feat: 实现 Host timer 组件
```

PR 描述：

```markdown
## Summary

- 新增 `components/timer` 平台无关一次性 timer 组件
- 通过 OSAL time/thread/mutex 和 event bus 实现到期事件投递
- 增加 host/API 测试覆盖初始化、启动、停止、重启、容量和错误路径

## Validation

- [ ] pytest tests/host_unit tests/api_contract -v
- [ ] cmake -S . -B build
- [ ] cmake --build build
- [ ] ./build/platforms/host/posix/ep_platform_host_posix
```

## 计划自检

- spec 的公共 API、全局一次性 timer、固定 16 个 timer、10ms 扫描周期、event 投递、未初始化错误、负数 timer id、停止、重启、容量错误都已映射到任务。
- 本计划不包含 framework 自动初始化、周期 timer、deinit、Luban-Lite 或 RT-Thread 实现。
- 计划里的函数名、类型名和错误码与现有 `ep_event.h`、`ep_osal_err.h`、OSAL thread/mutex/time 头文件一致。
