# Host OSAL thread/mutex 实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 在 `platforms/host/posix` 下实现 host 版 OSAL 线程和互斥锁接口。

**架构：** 保持公共 OSAL 头文件平台无关，在 host POSIX 平台包内新增 `ep_host_osal_thread.c` 和 `ep_host_osal_mutex.c`。线程映射到 `pthread_create()` / `pthread_join()`，互斥锁映射到 `pthread_mutex_init()` / `pthread_mutex_lock()` / `pthread_mutex_unlock()`，opaque handle 的内存由已有 `ep_malloc()` / `ep_free()` 管理。

**技术栈：** C11、POSIX pthread、CMake、pytest

---

## 文件结构图

- `platforms/host/posix/CMakeLists.txt`
  把 `osal_port/ep_host_osal_thread.c` 和 `osal_port/ep_host_osal_mutex.c` 加入 `ep_platform_host_posix`。
- `platforms/host/posix/osal_port/ep_host_osal_thread.c`
  实现 `ep_thread_create()` 和 `ep_thread_join()`。
- `platforms/host/posix/osal_port/ep_host_osal_mutex.c`
  实现 `ep_mutex_create()`、`ep_mutex_lock()` 和 `ep_mutex_unlock()`。
- `tests/host_unit/test_host_osal_thread_mutex.py`
  编译并运行一个小 C 程序，验证 host thread/mutex OSAL 行为。

## Task 1: 增加失败的 Host OSAL thread/mutex 测试

**Files:**
- Create: `tests/host_unit/test_host_osal_thread_mutex.py`

- [ ] **Step 1: 新增 host OSAL thread/mutex 测试**

创建 `tests/host_unit/test_host_osal_thread_mutex.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_thread_and_mutex_sources():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_thread.c" in cmake
    assert "osal_port/ep_host_osal_mutex.c" in cmake


def test_host_osal_thread_and_mutex_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_thread_mutex_smoke.c"
    executable = tmp_path / "host_osal_thread_mutex_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_err.h"
            #include "ep_osal_mutex.h"
            #include "ep_osal_thread.h"

            typedef struct {
                ep_mutex_t *mutex;
                int value;
            } shared_state_t;

            static void *worker_entry(void *arg)
            {
                shared_state_t *state = (shared_state_t *)arg;

                if (ep_mutex_lock(state->mutex) != EP_OK) {
                    return (void *)1;
                }

                state->value += 1;

                if (ep_mutex_unlock(state->mutex) != EP_OK) {
                    return (void *)2;
                }

                return 0;
            }

            int main(void)
            {
                ep_thread_t *thread = 0;
                shared_state_t state;

                state.mutex = 0;
                state.value = 0;

                if (ep_mutex_create(0) == EP_OK) {
                    return 1;
                }

                if (ep_mutex_lock(0) == EP_OK) {
                    return 2;
                }

                if (ep_mutex_unlock(0) == EP_OK) {
                    return 3;
                }

                if (ep_thread_create(0, "invalid", worker_entry, &state) == EP_OK) {
                    return 4;
                }

                if (ep_thread_create(&thread, "invalid", 0, &state) == EP_OK) {
                    return 5;
                }

                if (ep_thread_join(0) == EP_OK) {
                    return 6;
                }

                if (ep_mutex_create(&state.mutex) != EP_OK) {
                    return 7;
                }

                if (ep_mutex_lock(state.mutex) != EP_OK) {
                    return 8;
                }

                if (ep_mutex_unlock(state.mutex) != EP_OK) {
                    return 9;
                }

                if (ep_thread_create(&thread, "host-worker", worker_entry, &state) != EP_OK) {
                    return 10;
                }

                if (ep_thread_join(thread) != EP_OK) {
                    return 11;
                }

                if (state.value != 1) {
                    return 12;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_thread.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mutex.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
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
pytest tests/host_unit/test_host_osal_thread_mutex.py -v
```

预期：失败。失败原因应该是 `CMakeLists.txt` 还没有包含 `ep_host_osal_thread.c` /
`ep_host_osal_mutex.c`，或这两个实现文件还不存在。

- [ ] **Step 3: 提交失败测试**

运行：

```bash
git add tests/host_unit/test_host_osal_thread_mutex.py
git commit -m "test: 增加 Host OSAL 线程和互斥锁测试"
```

## Task 2: 实现 Host OSAL thread/mutex

**Files:**
- Modify: `platforms/host/posix/CMakeLists.txt`
- Create: `platforms/host/posix/osal_port/ep_host_osal_thread.c`
- Create: `platforms/host/posix/osal_port/ep_host_osal_mutex.c`

- [ ] **Step 1: 更新 host POSIX CMake target**

将 `platforms/host/posix/CMakeLists.txt` 替换为：

```cmake
add_executable(ep_platform_host_posix
  startup/main.c
  osal_port/ep_host_osal_stub.c
  osal_port/ep_host_osal_time.c
  osal_port/ep_host_osal_mem.c
  osal_port/ep_host_osal_thread.c
  osal_port/ep_host_osal_mutex.c
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
)
```

- [ ] **Step 2: 实现 host 线程接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_thread.c`：

```c
#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_thread.h"

#include <pthread.h>

struct ep_thread {
    pthread_t handle;
};

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)
{
    ep_thread_t *new_thread;

    (void)name;

    if (thread == 0 || entry == 0) {
        return EP_ERR_INVAL;
    }

    new_thread = (ep_thread_t *)ep_malloc(sizeof(*new_thread));
    if (new_thread == 0) {
        return EP_ERR_BUSY;
    }

    if (pthread_create(&new_thread->handle, 0, entry, arg) != 0) {
        ep_free(new_thread);
        return EP_ERR_UNSUPPORTED;
    }

    *thread = new_thread;
    return EP_OK;
}

int ep_thread_join(ep_thread_t *thread)
{
    if (thread == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_join(thread->handle, 0) != 0) {
        return EP_ERR_INVAL;
    }

    ep_free(thread);
    return EP_OK;
}
```

- [ ] **Step 3: 实现 host 互斥锁接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_mutex.c`：

```c
#include "ep_osal_err.h"
#include "ep_osal_mem.h"
#include "ep_osal_mutex.h"

#include <pthread.h>

struct ep_mutex {
    pthread_mutex_t handle;
};

int ep_mutex_create(ep_mutex_t **mutex)
{
    ep_mutex_t *new_mutex;

    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    new_mutex = (ep_mutex_t *)ep_malloc(sizeof(*new_mutex));
    if (new_mutex == 0) {
        return EP_ERR_BUSY;
    }

    if (pthread_mutex_init(&new_mutex->handle, 0) != 0) {
        ep_free(new_mutex);
        return EP_ERR_UNSUPPORTED;
    }

    *mutex = new_mutex;
    return EP_OK;
}

int ep_mutex_lock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_mutex_lock(&mutex->handle) != 0) {
        return EP_ERR_BUSY;
    }

    return EP_OK;
}

int ep_mutex_unlock(ep_mutex_t *mutex)
{
    if (mutex == 0) {
        return EP_ERR_INVAL;
    }

    if (pthread_mutex_unlock(&mutex->handle) != 0) {
        return EP_ERR_INVAL;
    }

    return EP_OK;
}
```

- [ ] **Step 4: 运行聚焦测试，确认通过**

运行：

```bash
pytest tests/host_unit/test_host_osal_thread_mutex.py -v
```

预期：通过。

- [ ] **Step 5: 提交实现**

运行：

```bash
git add platforms/host/posix/CMakeLists.txt platforms/host/posix/osal_port/ep_host_osal_thread.c platforms/host/posix/osal_port/ep_host_osal_mutex.c
git commit -m "feat: 实现 Host OSAL 线程和互斥锁接口"
```

## Task 3: 完整验证

**Files:**
- 正常情况下不需要修改代码文件。
- 如果出现构建产物或缓存，不要提交。

- [ ] **Step 1: 运行完整 Python 验证**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：所有测试通过。

- [ ] **Step 2: 运行 CMake configure**

运行：

```bash
cmake -S . -B build
```

预期：退出码为 `0`，输出显示 build files 写入 `build`。

- [ ] **Step 3: 运行 CMake build**

运行：

```bash
cmake --build build
```

预期：退出码为 `0`，并包含 `ep_platform_host_posix` 构建成功。

- [ ] **Step 4: 运行 host POSIX 可执行文件**

运行：

```bash
./build/platforms/host/posix/ep_platform_host_posix
echo $?
```

预期：输出 `0`。

- [ ] **Step 5: 确认 git 状态**

运行：

```bash
git status --short --branch
```

预期：工作区干净。不要提交 `build/`、`.pytest_cache/`、`__pycache__/` 或其他生成文件。

## 自检

- 规格覆盖：本计划覆盖 thread/mutex 实现文件、host target 链接、编译链接运行测试、公共头文件平台无关要求。
- 范围控制：本计划不实现 semaphore、queue、日志、事件、定时器或 Luban-Lite。
- 命名一致性：公共函数名保持为 `ep_thread_create()`、`ep_thread_join()`、`ep_mutex_create()`、`ep_mutex_lock()`、`ep_mutex_unlock()`，实现文件名保持为 `ep_host_osal_thread.c` 和 `ep_host_osal_mutex.c`。
