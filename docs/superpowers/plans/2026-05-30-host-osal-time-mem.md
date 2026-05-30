# Host OSAL time/mem 实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 在 `platforms/host/posix` 下实现 host 版 OSAL 时间和内存接口。

**架构：** 保持公共 OSAL 头文件平台无关，在 host POSIX 平台包内新增 `ep_host_osal_time.c` 和 `ep_host_osal_mem.c`。`ep_time_now_ms()` 和 `ep_sleep_ms()` 映射到 POSIX 单调时间和 `nanosleep()`，`ep_malloc()` 和 `ep_free()` 映射到 C 标准库 `malloc()` / `free()`。

**技术栈：** C11、POSIX `clock_gettime` / `nanosleep`、C 标准库、CMake、pytest

---

## 文件结构图

- `platforms/host/posix/CMakeLists.txt`
  把 `osal_port/ep_host_osal_time.c` 和 `osal_port/ep_host_osal_mem.c` 加入 `ep_platform_host_posix`。
- `platforms/host/posix/osal_port/ep_host_osal_time.c`
  实现 `ep_time_now_ms()` 和 `ep_sleep_ms()`。
- `platforms/host/posix/osal_port/ep_host_osal_mem.c`
  实现 `ep_malloc()` 和 `ep_free()`。
- `tests/host_unit/test_host_osal_time_mem.py`
  编译并运行一个小 C 程序，验证 host time/mem OSAL 行为。

## Task 1: 增加失败的 Host OSAL time/mem 测试

**Files:**
- Create: `tests/host_unit/test_host_osal_time_mem.py`

- [ ] **Step 1: 新增 host OSAL time/mem 测试**

创建 `tests/host_unit/test_host_osal_time_mem.py`：

```python
import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_host_posix_cmake_links_time_and_mem_sources():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "osal_port/ep_host_osal_time.c" in cmake
    assert "osal_port/ep_host_osal_mem.c" in cmake


def test_host_osal_time_and_mem_compile_link_and_run(tmp_path):
    assert COMPILER, "Expected clang or cc to be available"

    source = tmp_path / "host_osal_time_mem_smoke.c"
    executable = tmp_path / "host_osal_time_mem_smoke"
    source.write_text(
        textwrap.dedent(
            """
            #include "ep_osal_mem.h"
            #include "ep_osal_time.h"

            int main(void)
            {
                unsigned char *buffer = (unsigned char *)ep_malloc(4);
                uint64_t before = 0;
                uint64_t after = 0;

                if (buffer == 0) {
                    return 1;
                }

                buffer[0] = 0x12;
                buffer[1] = 0x34;
                buffer[2] = 0x56;
                buffer[3] = 0x78;

                before = ep_time_now_ms();
                ep_sleep_ms(1);
                after = ep_time_now_ms();

                ep_free(buffer);
                ep_free(0);

                if (after < before) {
                    return 2;
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
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_time.c"),
            str(REPO_ROOT / "platforms/host/posix/osal_port/ep_host_osal_mem.c"),
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
pytest tests/host_unit/test_host_osal_time_mem.py -v
```

预期：失败。失败原因应该是 `CMakeLists.txt` 还没有包含 `ep_host_osal_time.c` /
`ep_host_osal_mem.c`，或这两个实现文件还不存在。

- [ ] **Step 3: 提交失败测试**

运行：

```bash
git add tests/host_unit/test_host_osal_time_mem.py
git commit -m "test: 增加 Host OSAL 时间和内存测试"
```

## Task 2: 实现 Host OSAL time/mem

**Files:**
- Modify: `platforms/host/posix/CMakeLists.txt`
- Create: `platforms/host/posix/osal_port/ep_host_osal_time.c`
- Create: `platforms/host/posix/osal_port/ep_host_osal_mem.c`

- [ ] **Step 1: 更新 host POSIX CMake target**

将 `platforms/host/posix/CMakeLists.txt` 替换为：

```cmake
add_executable(ep_platform_host_posix
  startup/main.c
  osal_port/ep_host_osal_stub.c
  osal_port/ep_host_osal_time.c
  osal_port/ep_host_osal_mem.c
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

- [ ] **Step 2: 实现 host 时间接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_time.c`：

```c
#include "ep_osal_time.h"

#include <errno.h>
#include <time.h>

uint64_t ep_time_now_ms(void)
{
    struct timespec now;

    if (clock_gettime(CLOCK_MONOTONIC, &now) != 0) {
        return 0;
    }

    return ((uint64_t)now.tv_sec * 1000u) + ((uint64_t)now.tv_nsec / 1000000u);
}

void ep_sleep_ms(unsigned int timeout_ms)
{
    struct timespec request;
    struct timespec remaining;

    request.tv_sec = (time_t)(timeout_ms / 1000u);
    request.tv_nsec = (long)(timeout_ms % 1000u) * 1000000L;

    while (nanosleep(&request, &remaining) != 0) {
        if (errno != EINTR) {
            return;
        }
        request = remaining;
    }
}
```

- [ ] **Step 3: 实现 host 内存接口**

创建 `platforms/host/posix/osal_port/ep_host_osal_mem.c`：

```c
#include "ep_osal_mem.h"

#include <stdlib.h>

void *ep_malloc(size_t size)
{
    return malloc(size);
}

void ep_free(void *ptr)
{
    free(ptr);
}
```

- [ ] **Step 4: 运行聚焦测试，确认通过**

运行：

```bash
pytest tests/host_unit/test_host_osal_time_mem.py -v
```

预期：通过。

- [ ] **Step 5: 提交实现**

运行：

```bash
git add platforms/host/posix/CMakeLists.txt platforms/host/posix/osal_port/ep_host_osal_time.c platforms/host/posix/osal_port/ep_host_osal_mem.c
git commit -m "feat: 实现 Host OSAL 时间和内存接口"
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

- 规格覆盖：本计划覆盖 time/mem 实现文件、host target 链接、编译链接运行测试、公共头文件平台无关要求。
- 范围控制：本计划不实现 thread、mutex、semaphore、queue、日志、事件、定时器或 Luban-Lite。
- 命名一致性：公共函数名保持为 `ep_time_now_ms()`、`ep_sleep_ms()`、`ep_malloc()`、`ep_free()`，实现文件名保持为 `ep_host_osal_time.c` 和 `ep_host_osal_mem.c`。
