# Host OSAL queue 实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 在 `platforms/host/posix` 下实现 host 版 OSAL 队列接口。

**架构：** 保持公共 OSAL 头文件平台无关，在 host POSIX 平台包内新增 `ep_host_osal_queue.c`。队列使用环形缓冲区保存固定大小 item，使用 `pthread_mutex_t` 保护内部状态，并用 `not_empty` / `not_full` 两个条件变量实现空队列等待、满队列等待和超时返回。

**技术栈：** C11、POSIX pthread、CMake Threads、pytest

---

## 文件结构图

- `platforms/host/posix/CMakeLists.txt`
  把 `osal_port/ep_host_osal_queue.c` 加入 `ep_platform_host_posix`。
- `platforms/host/posix/osal_port/ep_host_osal_queue.c`
  实现 `ep_queue_create()`、`ep_queue_send()` 和 `ep_queue_recv()`。
- `tests/host_unit/test_host_osal_queue.py`
  编译并运行一个小 C 程序，验证 host queue OSAL 行为。

## Task 1: 增加失败的 Host OSAL queue 测试

**Files:**
- Create: `tests/host_unit/test_host_osal_queue.py`

- [ ] **Step 1: 新增 host OSAL queue 测试**

创建 `tests/host_unit/test_host_osal_queue.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_queue_source():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_queue.c" in cmake


def test_host_osal_queue_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_queue_smoke.c"
    executable = tmp_path / "host_osal_queue_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_queue.h"
            #include "ep_osal_thread.h"
            #include "ep_osal_time.h"

            typedef struct {
                int id;
                int value;
            } message_t;

            typedef struct {
                ep_queue_t *queue;
                message_t message;
            } worker_state_t;

            static void *delayed_sender(void *arg)
            {
                worker_state_t *state = (worker_state_t *)arg;

                ep_sleep_ms(10);

                if (ep_queue_send(state->queue, &state->message, 500) != EP_OK) {
                    return (void *)1;
                }

                return 0;
            }

            static void *delayed_receiver(void *arg)
            {
                worker_state_t *state = (worker_state_t *)arg;
                message_t received;

                ep_sleep_ms(10);

                if (ep_queue_recv(state->queue, &received, 500) != EP_OK) {
                    return (void *)1;
                }

                if (received.id != state->message.id || received.value != state->message.value) {
                    return (void *)2;
                }

                return 0;
            }

            int main(void)
            {
                ep_queue_t *queue = 0;
                ep_thread_t *thread = 0;
                worker_state_t state;
                message_t first = { .id = 1, .value = 100 };
                message_t second = { .id = 2, .value = 200 };
                message_t third = { .id = 3, .value = 300 };
                message_t received = { .id = 0, .value = 0 };
                int scalar = 42;

                if (ep_queue_create(0, sizeof(message_t), 2) == EP_OK) {
                    return 1;
                }

                if (ep_queue_create(&queue, 0, 2) == EP_OK) {
                    return 2;
                }

                if (ep_queue_create(&queue, sizeof(message_t), 0) == EP_OK) {
                    return 3;
                }

                if (ep_queue_send(0, &first, 0) == EP_OK) {
                    return 4;
                }

                if (ep_queue_recv(0, &received, 0) == EP_OK) {
                    return 5;
                }

                if (ep_queue_create(&queue, sizeof(message_t), 1) != EP_OK) {
                    return 6;
                }

                if (ep_queue_send(queue, 0, 0) == EP_OK) {
                    return 7;
                }

                if (ep_queue_recv(queue, 0, 0) == EP_OK) {
                    return 8;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_ERR_TIMEOUT) {
                    return 9;
                }

                if (ep_queue_send(queue, &first, 0) != EP_OK) {
                    return 10;
                }

                if (ep_queue_send(queue, &second, 0) != EP_ERR_TIMEOUT) {
                    return 11;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_OK) {
                    return 12;
                }

                if (received.id != first.id || received.value != first.value) {
                    return 13;
                }

                state.queue = queue;
                state.message = second;
                thread = 0;

                if (ep_thread_create(&thread, "queue-sender", delayed_sender, &state) != EP_OK) {
                    return 14;
                }

                if (ep_queue_recv(queue, &received, 500) != EP_OK) {
                    return 15;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 16;
                }

                if (received.id != second.id || received.value != second.value) {
                    return 17;
                }

                if (ep_queue_send(queue, &third, 0) != EP_OK) {
                    return 18;
                }

                state.message = third;
                thread = 0;

                if (ep_thread_create(&thread, "queue-receiver", delayed_receiver, &state) != EP_OK) {
                    return 19;
                }

                if (ep_queue_send(queue, &second, 500) != EP_OK) {
                    return 20;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 21;
                }

                if (ep_queue_recv(queue, &received, 0) != EP_OK) {
                    return 22;
                }

                if (received.id != second.id || received.value != second.value) {
                    return 23;
                }

                if (ep_queue_create(&queue, sizeof(int), 1) != EP_OK) {
                    return 24;
                }

                if (ep_queue_send(queue, &scalar, 0) != EP_OK) {
                    return 25;
                }

                scalar = 0;
                if (ep_queue_recv(queue, &scalar, 0) != EP_OK) {
                    return 26;
                }

                if (scalar != 42) {
                    return 27;
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
            str(REPO_ROOT / "osal/include"),
            str(source),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_queue.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            "-pthread",
            "-o",
            str(executable),
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert compile_result.returncode == 0, (
        f"compile failed\nstdout:\n{compile_result.stdout}\nstderr:\n{compile_result.stderr}"
    )

    run_result = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run_result.returncode == 0, (
        f"run failed\nstdout:\n{run_result.stdout}\nstderr:\n{run_result.stderr}"
    )
```

- [ ] **Step 2: 运行新测试，确认失败**

运行：

```bash
pytest tests/host_unit/test_host_osal_queue.py -v
```

预期：失败。失败原因应该包含以下至少一项：

- `platforms/host/posix/CMakeLists.txt` 还没有包含 `osal_port/ep_host_osal_queue.c`。
- `platforms/host/posix/osal_port/ep_host_osal_queue.c` 还不存在。

- [ ] **Step 3: 提交失败测试**

运行：

```bash
git add tests/host_unit/test_host_osal_queue.py
git commit -m "test: 增加 Host OSAL 队列测试"
```

## Task 2: 实现 Host OSAL queue

**Files:**
- Modify: `platforms/host/posix/CMakeLists.txt`
- Create: `platforms/host/posix/osal_port/ep_host_osal_queue.c`

- [ ] **Step 1: 更新 host POSIX CMake target**

将 `platforms/host/posix/CMakeLists.txt` 替换为：

```cmake
find_package(Threads REQUIRED)

add_executable(ep_platform_host_posix
  startup/main.c
  osal_port/ep_host_osal_stub.c
  osal_port/ep_host_osal_time.c
  osal_port/ep_host_osal_mem.c
  osal_port/ep_host_osal_thread.c
  osal_port/ep_host_osal_mutex.c
  osal_port/ep_host_osal_sem.c
  osal_port/ep_host_osal_queue.c
  hal_port/ep_host_hal_stub.c
  component_port/ep_host_component_stub.c
)

target_include_directories(ep_platform_host_posix
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    Threads::Threads
)
```

- [ ] **Step 2: 实现 host 队列接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_queue.c`：

```c
#if !defined(__APPLE__)
#define _POSIX_C_SOURCE 200809L
#endif

#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_queue.h"

#include <errno.h>
#include <pthread.h>
#include <stddef.h>
#include <string.h>
#include <sys/time.h>
#include <time.h>

struct ep_queue {
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    unsigned char *buffer;
    size_t item_size;
    size_t depth;
    size_t head;
    size_t tail;
    size_t count;
};

static int ep_queue_init_cond(pthread_cond_t *cond)
{
#if defined(__APPLE__)
    return pthread_cond_init(cond, 0);
#else
    pthread_condattr_t attr;
    int rc;

    rc = pthread_condattr_init(&attr);
    if (rc != 0) {
        return rc;
    }

    rc = pthread_condattr_setclock(&attr, CLOCK_MONOTONIC);
    if (rc != 0) {
        (void)pthread_condattr_destroy(&attr);
        return rc;
    }

    rc = pthread_cond_init(cond, &attr);
    if (pthread_condattr_destroy(&attr) != 0 && rc == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    return rc;
#endif
}

static int ep_queue_make_deadline(struct timespec *deadline, unsigned int timeout_ms)
{
#if defined(__APPLE__)
    struct timeval now;
    long nsec;

    if (gettimeofday(&now, 0) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    deadline->tv_sec = now.tv_sec + (time_t)(timeout_ms / 1000u);
    nsec = ((long)now.tv_usec * 1000L) + ((long)(timeout_ms % 1000u) * 1000000L);
    deadline->tv_sec += (time_t)(nsec / 1000000000L);
    deadline->tv_nsec = nsec % 1000000000L;
#else
    long nsec;

    if (clock_gettime(CLOCK_MONOTONIC, deadline) != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    deadline->tv_sec += (time_t)(timeout_ms / 1000u);
    nsec = deadline->tv_nsec + ((long)(timeout_ms % 1000u) * 1000000L);
    deadline->tv_sec += (time_t)(nsec / 1000000000L);
    deadline->tv_nsec = nsec % 1000000000L;
#endif

    return EP_OK;
}

static int ep_queue_init_sync(ep_queue_t *queue)
{
    int rc;

    rc = pthread_mutex_init(&queue->lock, 0);
    if (rc != 0) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_queue_init_cond(&queue->not_empty);
    if (rc != 0) {
        (void)pthread_mutex_destroy(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_queue_init_cond(&queue->not_full);
    if (rc != 0) {
        (void)pthread_cond_destroy(&queue->not_empty);
        (void)pthread_mutex_destroy(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    return EP_OK;
}

static unsigned char *ep_queue_slot(ep_queue_t *queue, size_t index)
{
    return queue->buffer + (index * queue->item_size);
}

int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth)
{
    ep_queue_t *new_queue;
    int rc;

    if (queue == 0 || item_size == 0u || depth == 0u) {
        return EP_ERR_INVAL;
    }

    if (depth > ((size_t)-1) / item_size) {
        return EP_ERR_INVAL;
    }

    new_queue = (ep_queue_t *)ep_malloc(sizeof(*new_queue));
    if (new_queue == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    new_queue->buffer = (unsigned char *)ep_malloc(item_size * depth);
    if (new_queue->buffer == 0) {
        ep_free(new_queue);
        return EP_ERR_UNSUPPORTED;
    }

    new_queue->item_size = item_size;
    new_queue->depth = depth;
    new_queue->head = 0u;
    new_queue->tail = 0u;
    new_queue->count = 0u;

    rc = ep_queue_init_sync(new_queue);
    if (rc != EP_OK) {
        ep_free(new_queue->buffer);
        ep_free(new_queue);
        return rc;
    }

    *queue = new_queue;

    return EP_OK;
}

int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (queue->count == queue->depth && timeout_ms > 0u) {
        rc = ep_queue_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&queue->lock);
            return rc;
        }
    }

    while (queue->count == queue->depth) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&queue->not_full, &queue->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    memcpy(ep_queue_slot(queue, queue->tail), item, queue->item_size);
    queue->tail = (queue->tail + 1u) % queue->depth;
    queue->count += 1u;

    rc = pthread_cond_signal(&queue->not_empty);
    if (rc != 0) {
        (void)pthread_mutex_unlock(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_unlock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (queue == 0 || item == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (queue->count == 0u && timeout_ms > 0u) {
        rc = ep_queue_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&queue->lock);
            return rc;
        }
    }

    while (queue->count == 0u) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&queue->not_empty, &queue->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&queue->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    memcpy(item, ep_queue_slot(queue, queue->head), queue->item_size);
    queue->head = (queue->head + 1u) % queue->depth;
    queue->count -= 1u;

    rc = pthread_cond_signal(&queue->not_full);
    if (rc != 0) {
        (void)pthread_mutex_unlock(&queue->lock);
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_unlock(&queue->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
```

- [ ] **Step 3: 运行 queue 单项测试，确认通过**

运行：

```bash
pytest tests/host_unit/test_host_osal_queue.py -v
```

预期：`2 passed`。

- [ ] **Step 4: 提交实现**

运行：

```bash
git add platforms/host/posix/CMakeLists.txt platforms/host/posix/osal_port/ep_host_osal_queue.c
git commit -m "feat: 实现 Host OSAL 队列接口"
```

## Task 3: 全量验证

**Files:**
- No source changes

- [ ] **Step 1: 运行 host/api 测试**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：所有测试通过，数量应包含新增的 `test_host_osal_queue.py` 测试。

- [ ] **Step 2: 运行 CMake configure**

运行：

```bash
cmake -S . -B build
```

预期：configure 成功，输出包含 `Build files have been written to`。

- [ ] **Step 3: 运行 CMake build**

运行：

```bash
cmake --build build
```

预期：构建成功，`ep_platform_host_posix` 可以链接通过。

- [ ] **Step 4: 运行 host POSIX 可执行文件**

运行：

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

预期：命令返回退出码 `0`，没有崩溃。

- [ ] **Step 5: 检查提交和工作区**

运行：

```bash
git status --short --branch
git log --oneline --decorate -4
```

预期：

- 工作区干净。
- 分支上包含两个中文提交：
  - `test: 增加 Host OSAL 队列测试`
  - `feat: 实现 Host OSAL 队列接口`

## 执行边界

- 不修改 `osal/include/ep_osal_queue.h` 的函数签名。
- 不新增 queue destroy/free 公共接口。
- 不实现 event、timer 或 log。
- 不适配匠芯创 Luban-Lite 或 RT-Thread。
- 不引入 vendor SDK 或板级 SDK。
- 不把 `pthread.h`、`sys/time.h`、`time.h` 暴露到公共 OSAL 头文件。
