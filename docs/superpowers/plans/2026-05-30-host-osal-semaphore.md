# Host OSAL semaphore 实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 在 `platforms/host/posix` 下实现 host 版 OSAL 信号量接口。

**架构：** 保持公共 OSAL 头文件平台无关，在 host POSIX 平台包内新增 `ep_host_osal_sem.c`。信号量使用 `pthread_mutex_t + pthread_cond_t` 实现计数、等待、超时和跨线程唤醒，opaque handle 的内存由已有 `ep_malloc()` / `ep_free()` 管理。

**技术栈：** C11、POSIX pthread、CMake Threads、pytest

---

## 文件结构图

- `platforms/host/posix/CMakeLists.txt`
  把 `osal_port/ep_host_osal_sem.c` 加入 `ep_platform_host_posix`，并显式链接 `Threads::Threads`。
- `platforms/host/posix/osal_port/ep_host_osal_sem.c`
  实现 `ep_sem_create()`、`ep_sem_wait()` 和 `ep_sem_post()`。
- `tests/host_unit/test_host_osal_semaphore.py`
  编译并运行一个小 C 程序，验证 host semaphore OSAL 行为。

## Task 1: 增加失败的 Host OSAL semaphore 测试

**Files:**
- Create: `tests/host_unit/test_host_osal_semaphore.py`

- [ ] **Step 1: 新增 host OSAL semaphore 测试**

创建 `tests/host_unit/test_host_osal_semaphore.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_semaphore_source_and_threads():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_sem.c" in cmake
    assert "Threads::Threads" in cmake


def test_host_osal_semaphore_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_semaphore_smoke.c"
    executable = tmp_path / "host_osal_semaphore_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_sem.h"
            #include "ep_osal_thread.h"
            #include "ep_osal_time.h"

            static void *poster_entry(void *arg)
            {
                ep_sem_t *sem = (ep_sem_t *)arg;

                ep_sleep_ms(10);

                if (ep_sem_post(sem) != EP_OK) {
                    return (void *)1;
                }

                return 0;
            }

            int main(void)
            {
                ep_sem_t *sem = 0;
                ep_thread_t *thread = 0;
                uint64_t before = 0;
                uint64_t after = 0;

                if (ep_sem_create(0, 1) == EP_OK) {
                    return 1;
                }

                if (ep_sem_wait(0, 0) == EP_OK) {
                    return 2;
                }

                if (ep_sem_post(0) == EP_OK) {
                    return 3;
                }

                if (ep_sem_create(&sem, 1) != EP_OK) {
                    return 4;
                }

                if (ep_sem_wait(sem, 0) != EP_OK) {
                    return 5;
                }

                if (ep_sem_wait(sem, 0) != EP_ERR_TIMEOUT) {
                    return 6;
                }

                before = ep_time_now_ms();
                if (ep_sem_wait(sem, 5) != EP_ERR_TIMEOUT) {
                    return 7;
                }
                after = ep_time_now_ms();

                if (after < before) {
                    return 8;
                }

                if (ep_thread_create(&thread, "sem-poster", poster_entry, sem) != EP_OK) {
                    return 9;
                }

                if (ep_sem_wait(sem, 500) != EP_OK) {
                    return 10;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 11;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_sem.c"),
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
pytest tests/host_unit/test_host_osal_semaphore.py -v
```

预期：失败。失败原因应该包含以下至少一项：

- `platforms/host/posix/CMakeLists.txt` 还没有包含 `osal_port/ep_host_osal_sem.c`。
- `platforms/host/posix/CMakeLists.txt` 还没有链接 `Threads::Threads`。
- `platforms/host/posix/osal_port/ep_host_osal_sem.c` 还不存在。

- [ ] **Step 3: 提交失败测试**

运行：

```bash
git add tests/host_unit/test_host_osal_semaphore.py
git commit -m "test: 增加 Host OSAL 信号量测试"
```

## Task 2: 实现 Host OSAL semaphore

**Files:**
- Modify: `platforms/host/posix/CMakeLists.txt`
- Create: `platforms/host/posix/osal_port/ep_host_osal_sem.c`

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

- [ ] **Step 2: 实现 host 信号量接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_sem.c`：

```c
#if !defined(__APPLE__)
#define _POSIX_C_SOURCE 200809L
#endif

#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_sem.h"

#include <errno.h>
#include <pthread.h>
#include <sys/time.h>
#include <time.h>

struct ep_sem {
    pthread_mutex_t lock;
    pthread_cond_t cond;
    unsigned int count;
};

static int ep_sem_init_cond(pthread_cond_t *cond)
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

static int ep_sem_make_deadline(struct timespec *deadline, unsigned int timeout_ms)
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

int ep_sem_create(ep_sem_t **sem, unsigned int initial_count)
{
    ep_sem_t *new_sem;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    new_sem = (ep_sem_t *)ep_malloc(sizeof(*new_sem));
    if (new_sem == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    rc = pthread_mutex_init(&new_sem->lock, 0);
    if (rc != 0) {
        ep_free(new_sem);
        return EP_ERR_UNSUPPORTED;
    }

    rc = ep_sem_init_cond(&new_sem->cond);
    if (rc != 0) {
        (void)pthread_mutex_destroy(&new_sem->lock);
        ep_free(new_sem);
        return EP_ERR_UNSUPPORTED;
    }

    new_sem->count = initial_count;
    *sem = new_sem;

    return EP_OK;
}

int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms)
{
    struct timespec deadline;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    if (sem->count == 0 && timeout_ms > 0u) {
        rc = ep_sem_make_deadline(&deadline, timeout_ms);
        if (rc != EP_OK) {
            (void)pthread_mutex_unlock(&sem->lock);
            return rc;
        }
    }

    while (sem->count == 0) {
        if (timeout_ms == 0u) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_TIMEOUT;
        }

        rc = pthread_cond_timedwait(&sem->cond, &sem->lock, &deadline);
        if (rc == ETIMEDOUT) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_TIMEOUT;
        }
        if (rc != 0) {
            (void)pthread_mutex_unlock(&sem->lock);
            return EP_ERR_UNSUPPORTED;
        }
    }

    sem->count -= 1u;

    rc = pthread_mutex_unlock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}

int ep_sem_post(ep_sem_t *sem)
{
    int signal_rc;
    int unlock_rc;
    int rc;

    if (sem == 0) {
        return EP_ERR_INVAL;
    }

    rc = pthread_mutex_lock(&sem->lock);
    if (rc != 0) {
        return EP_ERR_INVAL;
    }

    sem->count += 1u;
    signal_rc = pthread_cond_signal(&sem->cond);
    unlock_rc = pthread_mutex_unlock(&sem->lock);

    if (signal_rc != 0) {
        return EP_ERR_UNSUPPORTED;
    }
    if (unlock_rc != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
```

- [ ] **Step 3: 运行 semaphore 单项测试，确认通过**

运行：

```bash
pytest tests/host_unit/test_host_osal_semaphore.py -v
```

预期：`2 passed`。

- [ ] **Step 4: 提交实现**

运行：

```bash
git add platforms/host/posix/CMakeLists.txt platforms/host/posix/osal_port/ep_host_osal_sem.c
git commit -m "feat: 实现 Host OSAL 信号量接口"
```

## Task 3: 全量验证

**Files:**
- No source changes

- [ ] **Step 1: 运行 host/api 测试**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：所有测试通过，数量应包含新增的 `test_host_osal_semaphore.py` 测试。

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
git log --oneline --decorate -3
```

预期：

- 工作区干净。
- 分支上包含两个中文提交：
  - `test: 增加 Host OSAL 信号量测试`
  - `feat: 实现 Host OSAL 信号量接口`

## 执行边界

- 不修改 `osal/include/ep_osal_sem.h` 的函数签名。
- 不新增 semaphore destroy/free 公共接口。
- 不实现 queue。
- 不适配匠芯创 Luban-Lite 或 RT-Thread。
- 不引入 vendor SDK 或板级 SDK。
- 不把 `pthread.h`、`sys/time.h`、`time.h` 暴露到公共 OSAL 头文件。
