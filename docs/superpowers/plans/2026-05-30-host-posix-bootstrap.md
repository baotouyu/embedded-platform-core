# Host POSIX 启动骨架实施计划

> **给 agentic workers：** 必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 按任务执行本计划。步骤使用 checkbox（`- [ ]`）语法跟踪。

**目标：** 新增一个很小的 `platforms/host/posix` 启动目标，让框架可以在 macOS 和 Ubuntu 上作为 host 验证平台构建并运行。

**架构：** host 平台作为独立平台包放在 `platforms/host/posix`，和现有 RTOS/Linux demo 平台并列。它只链接 `ep_core` 和 `ep_app`，在 host startup 代码里定义平台启动钩子，并保持 POSIX/系统头文件不进入 `app/`、`core/`、`osal/include/` 和 `hal/include/`。

**技术栈：** C11、CMake、pytest、macOS/Ubuntu host shell

---

## 文件结构图

- `CMakeLists.txt`
  在已有 demo 平台包后面加入 `add_subdirectory(platforms/host/posix)`。
- `platforms/host/common/.gitkeep`
  保留 host 公共目录，后续放共享 host helper。
- `platforms/host/posix/CMakeLists.txt`
  定义 `ep_platform_host_posix` 可执行目标，并链接 `ep_core` 和 `ep_app`。
- `platforms/host/posix/startup/main.c`
  提供 host 进程入口，定义 `ep_platform_boot()`，并调用 `ep_framework_start()`。
- `platforms/host/posix/osal_port/ep_host_osal_stub.c`
  预留给后续 host OSAL 实现。
- `platforms/host/posix/hal_port/ep_host_hal_stub.c`
  预留给后续 host HAL mock/stub 实现。
- `platforms/host/posix/component_port/ep_host_component_stub.c`
  预留给后续 host 组件适配。
- `platforms/host/posix/config/host_posix.cmake`
  预留 host POSIX 配置文件，初始只放注释。
- `tests/api_contract/test_platform_bootstrap.py`
  扩展平台启动契约测试，覆盖 host POSIX，并构建 host 目标。
- `tests/host_unit/test_cmake_layout.py`
  扩展顶层 CMake 布局测试，确认包含 host 包。
- `tests/host_unit/test_host_posix_bootstrap.py`
  新增 host 专项测试，覆盖目录形状、目标命名和可执行运行行为。

## Task 1: 增加失败的 Host POSIX 启动测试

**Files:**
- Modify: `tests/api_contract/test_platform_bootstrap.py`
- Modify: `tests/host_unit/test_cmake_layout.py`
- Create: `tests/host_unit/test_host_posix_bootstrap.py`

- [ ] **Step 1: 更新平台启动契约测试**

将 `tests/api_contract/test_platform_bootstrap.py` 替换为：

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_platform_families_have_bootstrap_entries():
    rtos = (REPO_ROOT / "platforms/rtos/demo_family/startup/app_start.c").read_text()
    linux = (REPO_ROOT / "platforms/linux/demo_family/startup/main.c").read_text()
    host = (REPO_ROOT / "platforms/host/posix/startup/main.c").read_text()

    assert "ep_platform_boot" in rtos
    assert "ep_framework_start" in rtos
    assert "ep_platform_boot" in linux
    assert "ep_framework_start" in linux
    assert "ep_platform_boot" in host
    assert "ep_framework_start" in host


def test_platform_demo_targets_configure_and_build(tmp_path):
    build_dir = tmp_path / "platform-smoke"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        [
            "cmake",
            "--build",
            str(build_dir),
            "--target",
            "ep_platform_rtos_demo",
            "ep_platform_linux_demo",
            "ep_platform_host_posix",
        ],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )
```

- [ ] **Step 2: 更新顶层 CMake 布局测试**

将 `tests/host_unit/test_cmake_layout.py` 替换为：

```python
from pathlib import Path


def test_cmake_bootstrap_layout_matches_task_requirements():
    repo_root = Path(__file__).resolve().parents[2]
    top_level_cmake = (repo_root / "CMakeLists.txt").read_text(encoding="utf-8")

    assert "project(embedded-platform-core" in top_level_cmake
    assert "add_subdirectory(core)" in top_level_cmake
    assert "add_subdirectory(app)" in top_level_cmake
    assert "add_subdirectory(platforms/host/posix)" in top_level_cmake
    assert "EP_PLATFORM_FAMILY" in top_level_cmake
```

- [ ] **Step 3: 增加 host 专项启动测试**

创建 `tests/host_unit/test_host_posix_bootstrap.py`：

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_posix_package_shape_exists():
    expected_paths = [
        "platforms/host/common",
        "platforms/host/posix/CMakeLists.txt",
        "platforms/host/posix/startup/main.c",
        "platforms/host/posix/osal_port/ep_host_osal_stub.c",
        "platforms/host/posix/hal_port/ep_host_hal_stub.c",
        "platforms/host/posix/component_port/ep_host_component_stub.c",
        "platforms/host/posix/config/host_posix.cmake",
    ]

    missing = [path for path in expected_paths if not (REPO_ROOT / path).exists()]
    assert not missing, f"Missing host POSIX paths: {missing}"


def test_host_posix_cmake_target_is_named():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_executable(ep_platform_host_posix" in cmake
    assert "target_link_libraries(ep_platform_host_posix" in cmake
    assert "ep_core" in cmake
    assert "ep_app" in cmake


def test_host_posix_executable_runs_successfully(tmp_path):
    build_dir = tmp_path / "host-posix-build"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir), "--target", "ep_platform_host_posix"],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    executable = build_dir / "platforms/host/posix/ep_platform_host_posix"
    run = subprocess.run([str(executable)], capture_output=True, text=True)
    assert run.returncode == 0, (
        f"host executable failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
```

- [ ] **Step 4: 运行新测试，确认失败**

运行：

```bash
pytest tests/host_unit/test_cmake_layout.py tests/api_contract/test_platform_bootstrap.py tests/host_unit/test_host_posix_bootstrap.py -v
```

预期：失败。失败信息应该指向缺少 `platforms/host/posix` 文件、缺少
`add_subdirectory(platforms/host/posix)`，或缺少 `ep_platform_host_posix`。

- [ ] **Step 5: 提交失败测试**

运行：

```bash
git add tests/api_contract/test_platform_bootstrap.py tests/host_unit/test_cmake_layout.py tests/host_unit/test_host_posix_bootstrap.py
git commit -m "test: add host posix bootstrap checks"
```

## Task 2: 增加 Host POSIX 平台骨架

**Files:**
- Modify: `CMakeLists.txt`
- Create: `platforms/host/common/.gitkeep`
- Create: `platforms/host/posix/CMakeLists.txt`
- Create: `platforms/host/posix/startup/main.c`
- Create: `platforms/host/posix/osal_port/ep_host_osal_stub.c`
- Create: `platforms/host/posix/hal_port/ep_host_hal_stub.c`
- Create: `platforms/host/posix/component_port/ep_host_component_stub.c`
- Create: `platforms/host/posix/config/host_posix.cmake`

- [ ] **Step 1: 顶层 CMake 加入 host 包**

将 `CMakeLists.txt` 替换为：

```cmake
cmake_minimum_required(VERSION 3.20)

project(embedded-platform-core C)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake/modules")

include(ep_options)

# EP_PLATFORM_FAMILY is configured via ep_options.cmake.
add_subdirectory(core)
add_subdirectory(app)
add_subdirectory(platforms/rtos/demo_family)
add_subdirectory(platforms/linux/demo_family)
add_subdirectory(platforms/host/posix)
```

- [ ] **Step 2: 创建 host POSIX CMake target**

创建 `platforms/host/posix/CMakeLists.txt`：

```cmake
add_executable(ep_platform_host_posix
  startup/main.c
  osal_port/ep_host_osal_stub.c
  hal_port/ep_host_hal_stub.c
  component_port/ep_host_component_stub.c
)

target_include_directories(ep_platform_host_posix
  PRIVATE
    ${CMAKE_SOURCE_DIR}/core/include
)

target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
)
```

- [ ] **Step 3: 创建 host 启动入口**

创建 `platforms/host/posix/startup/main.c`：

```c
#include "ep_framework.h"

int ep_platform_boot(void)
{
    return 0;
}

int main(void)
{
    return ep_framework_start();
}
```

- [ ] **Step 4: 创建 host OSAL stub**

创建 `platforms/host/posix/osal_port/ep_host_osal_stub.c`：

```c
int ep_host_osal_stub_link_anchor(void)
{
    return 0;
}
```

- [ ] **Step 5: 创建 host HAL stub**

创建 `platforms/host/posix/hal_port/ep_host_hal_stub.c`：

```c
int ep_host_hal_stub_link_anchor(void)
{
    return 0;
}
```

- [ ] **Step 6: 创建 host component stub**

创建 `platforms/host/posix/component_port/ep_host_component_stub.c`：

```c
int ep_host_component_stub_link_anchor(void)
{
    return 0;
}
```

- [ ] **Step 7: 创建 host 配置占位文件和 common 目录**

创建 `platforms/host/posix/config/host_posix.cmake`：

```cmake
# Reserved for host POSIX platform configuration.
```

创建空文件：

```text
platforms/host/common/.gitkeep
```

- [ ] **Step 8: 运行聚焦测试，确认通过**

运行：

```bash
pytest tests/host_unit/test_cmake_layout.py tests/api_contract/test_platform_bootstrap.py tests/host_unit/test_host_posix_bootstrap.py -v
```

预期：通过。

- [ ] **Step 9: 提交 host POSIX 骨架**

运行：

```bash
git add CMakeLists.txt platforms/host
git commit -m "feat: add host posix bootstrap target"
```

## Task 3: 运行完整验证

**Files:**
- 正常情况下不需要修改代码文件。
- 如果出现构建产物或缓存，不要提交。

- [ ] **Step 1: 运行完整 Python 验证**

运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

预期：所有收集到的测试通过。

- [ ] **Step 2: 运行完整 CMake configure**

运行：

```bash
cmake -S . -B build
```

预期：退出码为 `0`，输出显示 build files 写入 `build`。

- [ ] **Step 3: 运行完整 CMake build**

运行：

```bash
cmake --build build
```

预期：退出码为 `0`，并包含这些构建目标：

```text
ep_core
ep_app
ep_platform_rtos_demo
ep_platform_linux_demo
ep_platform_host_posix
```

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

预期：完成 Task 1 和 Task 2 的提交后，工作区干净。如果中途确实需要测试修正，用下面命令提交：

```bash
git add tests/host_unit/test_host_posix_bootstrap.py tests/api_contract/test_platform_bootstrap.py tests/host_unit/test_cmake_layout.py
git commit -m "test: tighten host posix validation"
```

不要提交 `build/`、`.pytest_cache/`、`__pycache__/` 或其他生成文件。

## 自检

- 规格覆盖：本计划覆盖 host POSIX bootstrap 设计里的仓库结构、顶层 CMake target、host 可执行入口路径、分层边界和测试策略。
- 范围控制：本计划不实现真实 OSAL、HAL、日志、Luban-Lite、RT-Thread 或匠芯创 SDK 集成。
- 命名一致性：CMake target 全文统一为 `ep_platform_host_posix`，构建目录下的可执行路径统一为 `platforms/host/posix/ep_platform_host_posix`。
