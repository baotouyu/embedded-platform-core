# Host Event Bus Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现第一版平台无关 `components/event` 全局事件总线，并让 host POSIX 测试验证异步事件分发。

**Architecture:** `components/event` 暴露 `ep_event.h`，实现文件只依赖 OSAL queue/thread/mutex/mem/err 公共接口。全局 event bus 在 `ep_event_init()` 中创建一个队列、一个互斥锁和一个后台分发线程；`ep_event_publish()` 复制固定长度 payload 到队列，分发线程按注册顺序调用匹配 handler。

**Tech Stack:** C11、CMake、OSAL 公共接口、host POSIX OSAL 实现、pytest 生成 C smoke 程序。

---

## 文件结构

- Create: `components/event/include/ep_event.h`
  - event bus 公共头文件，只暴露平台无关类型和函数。
- Create: `components/event/src/ep_event.c`
  - event bus 平台无关实现，只 include OSAL 公共头。
- Create: `components/event/CMakeLists.txt`
  - 构建 `ep_components_event` 静态库。
- Modify: `CMakeLists.txt`
  - 新增 `add_subdirectory(components/event)`。
- Modify: `platforms/host/posix/CMakeLists.txt`
  - host POSIX 可执行文件链接 `ep_components_event`。
- Create: `tests/api_contract/test_event_headers.py`
  - 验证 `ep_event.h` 可独立编译、接口签名稳定、没有平台原生头文件。
- Create: `tests/host_unit/test_host_event_bus.py`
  - 生成 C 程序验证初始化、订阅、投递、分发和错误分支。

## Task 1: 锁定 event 公共接口契约

**Files:**
- Create: `tests/api_contract/test_event_headers.py`
- Create: `components/event/include/ep_event.h`

- [ ] **Step 1: 写失败的公共头文件契约测试**

创建 `tests/api_contract/test_event_headers.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
EVENT_INCLUDE = REPO_ROOT / "components" / "event" / "include"
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_event_header_does_not_include_platform_native_headers():
    header = EVENT_INCLUDE / "ep_event.h"

    assert header.exists(), "Expected components/event/include/ep_event.h to exist"

    content = header.read_text(encoding="utf-8")
    forbidden = ["pthread.h", "rtthread.h", "unistd.h", "sys/", "platforms/"]
    found = [name for name in forbidden if name in content]

    assert not found, f"ep_event.h must stay platform-neutral, found: {found}"


def test_event_header_compiles_standalone(tmp_path):
    assert COMPILER, "Expected clang or cc to be available for compile smoke test"

    source = tmp_path / "event_header_smoke.c"
    obj = tmp_path / "event_header_smoke.o"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_event.h"

            static void handler(
                ep_event_id_t event_id,
                const void *payload,
                size_t payload_size,
                void *user_data
            )
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                ep_event_id_t event_id = 1;
                ep_event_handler_t handler_fn = handler;
                int (*init_fn)(void) = ep_event_init;
                int (*subscribe_fn)(ep_event_id_t, ep_event_handler_t, void *) = ep_event_subscribe;
                int (*publish_fn)(ep_event_id_t, const void *, size_t, unsigned int) = ep_event_publish;

                return (event_id == 1 && handler_fn && init_fn && subscribe_fn && publish_fn) ? 0 : 1;
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
pytest tests/api_contract/test_event_headers.py -v
```

Expected:

```text
FAILED tests/api_contract/test_event_headers.py::test_event_header_does_not_include_platform_native_headers
Expected components/event/include/ep_event.h to exist
```

- [ ] **Step 3: 写最小公共头文件**

创建 `components/event/include/ep_event.h`：

```c
#ifndef EP_EVENT_H
#define EP_EVENT_H

#include <stddef.h>

typedef int ep_event_id_t;

typedef void (*ep_event_handler_t)(
    ep_event_id_t event_id,
    const void *payload,
    size_t payload_size,
    void *user_data
);

int ep_event_init(void);
int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data);
int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms);

#endif
```

- [ ] **Step 4: 运行接口契约测试，确认通过**

Run:

```bash
pytest tests/api_contract/test_event_headers.py -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交公共接口**

Run:

```bash
git add tests/api_contract/test_event_headers.py components/event/include/ep_event.h
git commit -m "test: 增加 event 公共接口契约"
```

## Task 2: 建立 event 组件构建骨架

**Files:**
- Create: `tests/host_unit/test_host_event_bus.py`
- Create: `components/event/CMakeLists.txt`
- Create: `components/event/src/ep_event.c`
- Modify: `CMakeLists.txt`
- Modify: `platforms/host/posix/CMakeLists.txt`

- [ ] **Step 1: 写失败的 CMake 构建测试**

创建 `tests/host_unit/test_host_event_bus.py`：

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_event_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    event_cmake_path = REPO_ROOT / "components/event/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/event)" in root_cmake
    assert event_cmake_path.exists()

    event_cmake = event_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_event STATIC" in event_cmake
    assert "src/ep_event.c" in event_cmake
    assert "components/event/include" not in event_cmake
    assert "ep_components_event" in host_cmake
```

- [ ] **Step 2: 运行测试，确认因为 CMake 未接入而失败**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_event_component_is_wired_into_cmake -v
```

Expected:

```text
FAILED tests/host_unit/test_host_event_bus.py::test_event_component_is_wired_into_cmake
assert 'add_subdirectory(components/event)' in ...
```

- [ ] **Step 3: 新增 event 组件 CMake**

创建 `components/event/CMakeLists.txt`：

```cmake
add_library(ep_components_event STATIC
  src/ep_event.c
)

target_include_directories(ep_components_event
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
```

- [ ] **Step 4: 新增临时最小 event 实现**

创建 `components/event/src/ep_event.c`：

```c
#include "ep_event.h"
#include "ep_osal_err.h"

int ep_event_init(void)
{
    return EP_ERR_UNSUPPORTED;
}

int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data)
{
    (void)event_id;
    (void)handler;
    (void)user_data;

    return EP_ERR_UNSUPPORTED;
}

int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms)
{
    (void)event_id;
    (void)payload;
    (void)payload_size;
    (void)timeout_ms;

    return EP_ERR_UNSUPPORTED;
}
```

- [ ] **Step 5: 接入顶层 CMake**

修改根目录 `CMakeLists.txt`，在 `add_subdirectory(app)` 后加入：

```cmake
add_subdirectory(components/event)
```

修改后的片段为：

```cmake
# EP_PLATFORM_FAMILY is configured via ep_options.cmake.
add_subdirectory(core)
add_subdirectory(app)
add_subdirectory(components/event)
add_subdirectory(platforms/rtos/demo_family)
add_subdirectory(platforms/linux/demo_family)
add_subdirectory(platforms/host/posix)
```

- [ ] **Step 6: 接入 host POSIX 链接**

修改 `platforms/host/posix/CMakeLists.txt` 的 `target_link_libraries`：

```cmake
target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_event
    Threads::Threads
)
```

- [ ] **Step 7: 运行 CMake 构建测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_event_component_is_wired_into_cmake -v
```

Expected:

```text
1 passed
```

- [ ] **Step 8: 运行 CMake 配置和构建，确认骨架可链接**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
[100%] Built target ep_platform_host_posix
```

- [ ] **Step 9: 提交构建骨架**

Run:

```bash
git add CMakeLists.txt platforms/host/posix/CMakeLists.txt components/event/CMakeLists.txt components/event/src/ep_event.c tests/host_unit/test_host_event_bus.py
git commit -m "build: 接入 event 组件构建骨架"
```

## Task 3: 实现 event 初始化和参数错误行为

**Files:**
- Modify: `tests/host_unit/test_host_event_bus.py`
- Modify: `components/event/src/ep_event.c`

- [ ] **Step 1: 增加失败的初始化和参数测试**

在 `tests/host_unit/test_host_event_bus.py` 追加：

```python
import shutil
import subprocess
import textwrap


COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_event_bus_init_and_invalid_arguments(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_invalid_smoke.c"
    executable = tmp_path / "host_event_invalid_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"

            static void handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                unsigned char payload[65] = {0};

                if (ep_event_subscribe(1, handler, 0) != EP_ERR_UNSUPPORTED) {
                    return 1;
                }

                if (ep_event_publish(1, 0, 0, 0) != EP_ERR_UNSUPPORTED) {
                    return 2;
                }

                if (ep_event_init() != EP_OK) {
                    return 3;
                }

                if (ep_event_init() != EP_OK) {
                    return 4;
                }

                if (ep_event_subscribe(1, 0, 0) != EP_ERR_INVAL) {
                    return 5;
                }

                if (ep_event_publish(1, 0, 1, 0) != EP_ERR_INVAL) {
                    return 6;
                }

                if (ep_event_publish(1, payload, sizeof(payload), 0) != EP_ERR_INVAL) {
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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

- [ ] **Step 2: 运行测试，确认因为 `ep_event_init()` 未实现而失败**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_init_and_invalid_arguments -v
```

Expected:

```text
FAILED tests/host_unit/test_host_event_bus.py::test_host_event_bus_init_and_invalid_arguments
assert 3 == 0
```

- [ ] **Step 3: 实现初始化和参数检查**

替换 `components/event/src/ep_event.c` 为：

```c
#include "ep_event.h"
#include "ep_osal_err.h"
#include "ep_osal_mutex.h"
#include "ep_osal_queue.h"
#include "ep_osal_thread.h"

#include <string.h>

#define EP_EVENT_MAX_HANDLERS 16u
#define EP_EVENT_MAX_PAYLOAD_SIZE 64u
#define EP_EVENT_QUEUE_DEPTH 16u

struct ep_event_message {
    ep_event_id_t event_id;
    size_t payload_size;
    unsigned char payload[EP_EVENT_MAX_PAYLOAD_SIZE];
};

struct ep_event_subscription {
    int used;
    ep_event_id_t event_id;
    ep_event_handler_t handler;
    void *user_data;
};

static ep_queue_t *g_event_queue;
static ep_thread_t *g_event_thread;
static ep_mutex_t *g_event_lock;
static struct ep_event_subscription g_subscriptions[EP_EVENT_MAX_HANDLERS];
static int g_event_started;

static void *ep_event_dispatch_loop(void *arg)
{
    (void)arg;

    for (;;) {
        struct ep_event_message message;
        (void)ep_queue_recv(g_event_queue, &message, 1000u);
    }

    return 0;
}

int ep_event_init(void)
{
    int rc;

    if (g_event_started) {
        return EP_OK;
    }

    rc = ep_mutex_create(&g_event_lock);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_queue_create(&g_event_queue, sizeof(struct ep_event_message), EP_EVENT_QUEUE_DEPTH);
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_thread_create(&g_event_thread, "event-bus", ep_event_dispatch_loop, 0);
    if (rc != EP_OK) {
        return rc;
    }

    g_event_started = 1;
    return EP_OK;
}

int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data)
{
    (void)event_id;
    (void)user_data;

    if (handler == 0) {
        return EP_ERR_INVAL;
    }

    if (!g_event_started) {
        return EP_ERR_UNSUPPORTED;
    }

    return EP_ERR_UNSUPPORTED;
}

int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms)
{
    struct ep_event_message message;

    if (!g_event_started) {
        return EP_ERR_UNSUPPORTED;
    }

    if (payload_size > EP_EVENT_MAX_PAYLOAD_SIZE) {
        return EP_ERR_INVAL;
    }

    if (payload_size > 0u && payload == 0) {
        return EP_ERR_INVAL;
    }

    message.event_id = event_id;
    message.payload_size = payload_size;
    if (payload_size > 0u) {
        (void)memcpy(message.payload, payload, payload_size);
    }

    return ep_queue_send(g_event_queue, &message, timeout_ms);
}
```

- [ ] **Step 4: 运行初始化和参数测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_init_and_invalid_arguments -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交初始化行为**

Run:

```bash
git add components/event/src/ep_event.c tests/host_unit/test_host_event_bus.py
git commit -m "feat: 实现 event 初始化和参数检查"
```

## Task 4: 实现订阅表和 handler 表满行为

**Files:**
- Modify: `tests/host_unit/test_host_event_bus.py`
- Modify: `components/event/src/ep_event.c`

- [ ] **Step 1: 增加失败的订阅容量测试**

在 `tests/host_unit/test_host_event_bus.py` 追加：

```python
def test_host_event_bus_subscription_capacity(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_capacity_smoke.c"
    executable = tmp_path / "host_event_capacity_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"

            static void handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                (void)event_id;
                (void)payload;
                (void)payload_size;
                (void)user_data;
            }

            int main(void)
            {
                int i;

                if (ep_event_init() != EP_OK) {
                    return 1;
                }

                for (i = 0; i < 16; ++i) {
                    if (ep_event_subscribe(100 + i, handler, 0) != EP_OK) {
                        return 2;
                    }
                }

                if (ep_event_subscribe(200, handler, 0) != EP_ERR_BUSY) {
                    return 3;
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "components/event/src/ep_event.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
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

- [ ] **Step 2: 运行测试，确认因为 subscribe 未实现而失败**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_subscription_capacity -v
```

Expected:

```text
FAILED tests/host_unit/test_host_event_bus.py::test_host_event_bus_subscription_capacity
assert 2 == 0
```

- [ ] **Step 3: 实现订阅表**

将 `components/event/src/ep_event.c` 中的 `ep_event_subscribe()` 替换为：

```c
int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data)
{
    size_t i;
    int rc;

    if (handler == 0) {
        return EP_ERR_INVAL;
    }

    if (!g_event_started) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_mutex_lock(g_event_lock);
    if (rc != EP_OK) {
        return rc;
    }

    for (i = 0u; i < EP_EVENT_MAX_HANDLERS; ++i) {
        if (!g_subscriptions[i].used) {
            g_subscriptions[i].used = 1;
            g_subscriptions[i].event_id = event_id;
            g_subscriptions[i].handler = handler;
            g_subscriptions[i].user_data = user_data;
            (void)ep_mutex_unlock(g_event_lock);
            return EP_OK;
        }
    }

    (void)ep_mutex_unlock(g_event_lock);
    return EP_ERR_BUSY;
}
```

- [ ] **Step 4: 运行订阅容量测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_subscription_capacity -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 提交订阅表行为**

Run:

```bash
git add components/event/src/ep_event.c tests/host_unit/test_host_event_bus.py
git commit -m "feat: 实现 event 订阅表"
```

## Task 5: 实现异步事件分发

**Files:**
- Modify: `tests/host_unit/test_host_event_bus.py`
- Modify: `components/event/src/ep_event.c`

- [ ] **Step 1: 增加失败的异步分发测试**

在 `tests/host_unit/test_host_event_bus.py` 追加：

```python
def test_host_event_bus_dispatches_published_event(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_event_dispatch_smoke.c"
    executable = tmp_path / "host_event_dispatch_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_event.h"
            #include "ep_osal_err.h"
            #include "ep_osal_time.h"

            #include <string.h>

            struct payload {
                int value;
                char label[8];
            };

            struct observed_state {
                volatile int call_count;
                volatile int second_call_count;
                ep_event_id_t event_id;
                size_t payload_size;
                int value;
                char label[8];
                int user_value;
            };

            static void first_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;
                const struct payload *body = (const struct payload *)payload;

                state->event_id = event_id;
                state->payload_size = payload_size;
                state->value = body->value;
                (void)memcpy(state->label, body->label, sizeof(state->label));
                state->user_value = 1234;
                state->call_count += 1;
            }

            static void second_handler(ep_event_id_t event_id, const void *payload, size_t payload_size, void *user_data)
            {
                struct observed_state *state = (struct observed_state *)user_data;

                (void)event_id;
                (void)payload;
                (void)payload_size;

                state->second_call_count += 1;
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
                struct payload body;

                (void)memset(&state, 0, sizeof(state));
                body.value = 77;
                (void)memcpy(body.label, "kitchen", 8);

                if (ep_event_init() != EP_OK) {
                    return 1;
                }

                if (ep_event_subscribe(10, first_handler, &state) != EP_OK) {
                    return 2;
                }

                if (ep_event_subscribe(10, second_handler, &state) != EP_OK) {
                    return 3;
                }

                if (ep_event_publish(99, &body, sizeof(body), 0) != EP_OK) {
                    return 4;
                }

                ep_sleep_ms(20);
                if (state.call_count != 0 || state.second_call_count != 0) {
                    return 5;
                }

                if (ep_event_publish(10, &body, sizeof(body), 100) != EP_OK) {
                    return 6;
                }

                if (wait_for_count(&state.call_count, 1) != 0) {
                    return 7;
                }

                if (wait_for_count(&state.second_call_count, 1) != 0) {
                    return 8;
                }

                if (state.event_id != 10) {
                    return 9;
                }

                if (state.payload_size != sizeof(body)) {
                    return 10;
                }

                if (state.value != 77) {
                    return 11;
                }

                if (memcmp(state.label, "kitchen", 8) != 0) {
                    return 12;
                }

                if (state.user_value != 1234) {
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
            str(REPO_ROOT / "components/event/include"),
            "-I",
            str(REPO_ROOT / "osal/include"),
            str(source),
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

- [ ] **Step 2: 运行测试，确认因为 dispatch loop 不调用 handler 而失败**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_dispatches_published_event -v
```

Expected:

```text
FAILED tests/host_unit/test_host_event_bus.py::test_host_event_bus_dispatches_published_event
assert 7 == 0
```

- [ ] **Step 3: 实现 handler 快照和异步分发**

在 `components/event/src/ep_event.c` 中加入快照结构：

```c
struct ep_event_handler_snapshot {
    ep_event_handler_t handler;
    void *user_data;
};
```

将 `ep_event_dispatch_loop()` 替换为：

```c
static void *ep_event_dispatch_loop(void *arg)
{
    (void)arg;

    for (;;) {
        struct ep_event_message message;
        struct ep_event_handler_snapshot snapshots[EP_EVENT_MAX_HANDLERS];
        size_t snapshot_count = 0u;
        size_t i;

        if (ep_queue_recv(g_event_queue, &message, 1000u) != EP_OK) {
            continue;
        }

        if (ep_mutex_lock(g_event_lock) != EP_OK) {
            continue;
        }

        for (i = 0u; i < EP_EVENT_MAX_HANDLERS; ++i) {
            if (g_subscriptions[i].used && g_subscriptions[i].event_id == message.event_id) {
                snapshots[snapshot_count].handler = g_subscriptions[i].handler;
                snapshots[snapshot_count].user_data = g_subscriptions[i].user_data;
                snapshot_count += 1u;
            }
        }

        (void)ep_mutex_unlock(g_event_lock);

        for (i = 0u; i < snapshot_count; ++i) {
            snapshots[i].handler(message.event_id, message.payload, message.payload_size, snapshots[i].user_data);
        }
    }

    return 0;
}
```

- [ ] **Step 4: 运行异步分发测试，确认通过**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py::test_host_event_bus_dispatches_published_event -v
```

Expected:

```text
1 passed
```

- [ ] **Step 5: 运行 event 测试文件，确认全部通过**

Run:

```bash
pytest tests/host_unit/test_host_event_bus.py tests/api_contract/test_event_headers.py -v
```

Expected:

```text
5 passed
```

- [ ] **Step 6: 提交异步分发行为**

Run:

```bash
git add components/event/src/ep_event.c tests/host_unit/test_host_event_bus.py
git commit -m "feat: 实现 event 异步分发"
```

## Task 6: 做完整验证和 PR 前收尾

**Files:**
- Verify only.

- [ ] **Step 1: 运行完整 host 和契约测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
所有测试通过，当前基线应为 33 passed
```

说明：如果测试数量因并行文档或后续测试增加而变化，以 pytest 输出的实际 passed 数为准，但必须是 0 failed。

- [ ] **Step 2: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
配置成功，构建成功，输出包含 Built target ep_platform_host_posix
```

- [ ] **Step 3: 运行 host POSIX 程序**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
命令退出码为 0
```

- [ ] **Step 4: 检查工作区和提交记录**

Run:

```bash
git status --short --branch
git log --oneline --decorate -6
```

Expected:

```text
工作区干净，最近提交包含 event 设计、计划和实现提交
```

- [ ] **Step 5: PR 标题和正文使用中文**

PR 标题：

```text
feat: 实现 Host event bus 组件
```

PR 正文：

```markdown
## 变更内容

- 新增 `components/event` 平台无关事件总线接口和实现
- 基于 OSAL queue/thread/mutex 实现全局异步事件分发
- 补充 event 公共头文件契约测试和 host 单元测试

## 测试

- [ ] `pytest tests/host_unit tests/api_contract -v`
- [ ] `cmake -S . -B build`
- [ ] `cmake --build build`
- [ ] `./build/platforms/host/posix/ep_platform_host_posix`
```

## 自检结果

- 设计文档要求均有对应任务：
  - 公共接口：Task 1。
  - 构建模型：Task 2。
  - 初始化和参数错误：Task 3。
  - handler 表容量：Task 4。
  - 异步分发、未注册事件、payload 复制、多个 handler：Task 5。
  - 完整验证和 PR 中文内容：Task 6。
- 没有多实例、取消订阅、优先级、动态扩容、deinit、framework 自动接入等非目标任务。
- 类型名和函数签名与设计文档一致：`ep_event_id_t`、`ep_event_handler_t`、`ep_event_init()`、`ep_event_subscribe()`、`ep_event_publish()`。

