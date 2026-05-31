# LVGL 最小运行组件 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `components/ui`，提供最小 LVGL 生命周期接口，并能在 host macOS arm64 上链接运行。

**Architecture:** `components/ui` 是工程自己的 UI 生命周期组件，只封装 `lv_init()`、`lv_tick_inc()`、`lv_timer_handler()` 和 `lv_deinit()`。它链接 `ep_thirdparty_lvgl`，但公共头文件 `ep_ui.h` 不暴露 LVGL 类型，业务以后需要控件 API 时仍可直接使用原生 `lvgl.h`。

**Tech Stack:** C11、CMake、pytest、LVGL 9.1.0 prebuilt `ep_thirdparty_lvgl`、现有 `ep_osal_err.h` 错误码。

---

## 文件结构

- Create: `components/ui/CMakeLists.txt`
  - 定义 `ep_components_ui` 静态库。
  - 暴露 `components/ui/include`。
  - 私有链接 `ep_thirdparty_lvgl`。
  - 私有包含 `osal/include`，用于 `EP_OK` 和错误码。
- Create: `components/ui/include/ep_ui.h`
  - 定义 `ep_ui_init()`、`ep_ui_tick_inc()`、`ep_ui_process()`、`ep_ui_deinit()`。
  - 不包含 `lvgl.h`。
  - 不暴露平台原生类型。
- Create: `components/ui/src/ep_ui.c`
  - 包含 `ep_ui.h`、`ep_osal_err.h`、`lvgl.h`。
  - 内部维护 `g_ui_initialized`。
  - 实现最小生命周期逻辑。
- Modify: `CMakeLists.txt`
  - 增加 `add_subdirectory(components/ui)`。
- Modify: `platforms/host/posix/CMakeLists.txt`
  - 让 host 可执行目标链接 `ep_components_ui`，保证主构建能覆盖组件链接关系。
- Create: `tests/host_unit/test_lvgl_ui_component.py`
  - 覆盖目录结构、公共头文件边界、实现调用、CMake 接线、macOS arm64 链接 smoke。

## Task 1: 添加 UI 组件红测

**Files:**
- Create: `tests/host_unit/test_lvgl_ui_component.py`

- [ ] **Step 1: 写失败测试**

Create `tests/host_unit/test_lvgl_ui_component.py`:

```python
import platform
import subprocess
import textwrap
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ui_component_layout_and_public_header_are_platform_neutral():
    component_root = REPO_ROOT / "components/ui"
    header = component_root / "include/ep_ui.h"

    assert (component_root / "CMakeLists.txt").exists()
    assert header.exists()
    assert (component_root / "src/ep_ui.c").exists()

    header_text = header.read_text(encoding="utf-8")
    assert "int ep_ui_init(void);" in header_text
    assert "int ep_ui_tick_inc(unsigned int elapsed_ms);" in header_text
    assert "int ep_ui_process(void);" in header_text
    assert "int ep_ui_deinit(void);" in header_text

    forbidden_headers = [
        "lvgl.h",
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
    ]
    for forbidden in forbidden_headers:
        assert forbidden not in header_text


def test_ui_component_calls_lvgl_lifecycle_apis_without_platform_headers():
    source = (REPO_ROOT / "components/ui/src/ep_ui.c").read_text(encoding="utf-8")

    assert '#include "ep_ui.h"' in source
    assert '#include "ep_osal_err.h"' in source
    assert '#include "lvgl.h"' in source
    assert "lv_init();" in source
    assert "lv_tick_inc(elapsed_ms);" in source
    assert "lv_timer_handler();" in source
    assert "lv_deinit();" in source

    forbidden_headers = [
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
    ]
    for forbidden in forbidden_headers:
        assert forbidden not in source


def test_ui_component_is_wired_into_cmake():
    top_level = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    component_cmake = (REPO_ROOT / "components/ui/CMakeLists.txt").read_text(encoding="utf-8")
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(encoding="utf-8")

    assert "add_subdirectory(components/ui)" in top_level
    assert "add_library(ep_components_ui STATIC" in component_cmake
    assert "src/ep_ui.c" in component_cmake
    assert "target_include_directories(ep_components_ui" in component_cmake
    assert "ep_thirdparty_lvgl" in component_cmake
    assert "ep_components_ui" in host_cmake


def test_ui_component_cmake_smoke_links_lvgl_lifecycle(tmp_path):
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        pytest.skip("host_macos LVGL package can only be linked on macOS arm64")

    project_dir = tmp_path / "ui-smoke"
    project_dir.mkdir()

    (project_dir / "CMakeLists.txt").write_text(
        textwrap.dedent(
            f"""
            cmake_minimum_required(VERSION 3.20)
            project(ui_smoke C)

            list(APPEND CMAKE_MODULE_PATH "{REPO_ROOT / "cmake/modules"}")
            set(EP_PROJECT_ROOT "{REPO_ROOT}")
            include(ep_lvgl_prebuilt)

            add_subdirectory("{REPO_ROOT / "components/ui"}" ui-build)

            add_executable(ui_smoke main.c)
            target_link_libraries(ui_smoke PRIVATE ep_components_ui)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    (project_dir / "main.c").write_text(
        textwrap.dedent(
            """
            #include "ep_ui.h"

            int main(void)
            {
                int rc = ep_ui_init();
                if (rc != 0) {
                    return rc;
                }

                rc = ep_ui_tick_inc(1u);
                if (rc != 0) {
                    return rc;
                }

                rc = ep_ui_process();
                if (rc != 0) {
                    return rc;
                }

                return ep_ui_deinit();
            }
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )

    build_dir = project_dir / "build"
    configure = subprocess.run(
        ["cmake", "-S", str(project_dir), "-B", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(build_dir)],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    run = subprocess.run(
        [str(build_dir / "ui_smoke")],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        f"run failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
pytest tests/host_unit/test_lvgl_ui_component.py -v
```

Expected:

```text
FAILED tests/host_unit/test_lvgl_ui_component.py::test_ui_component_layout_and_public_header_are_platform_neutral
```

失败原因应是 `components/ui/CMakeLists.txt`、`components/ui/include/ep_ui.h` 或 `components/ui/src/ep_ui.c` 不存在。

## Task 2: 实现最小 UI 组件

**Files:**
- Create: `components/ui/CMakeLists.txt`
- Create: `components/ui/include/ep_ui.h`
- Create: `components/ui/src/ep_ui.c`
- Modify: `CMakeLists.txt`
- Modify: `platforms/host/posix/CMakeLists.txt`
- Test: `tests/host_unit/test_lvgl_ui_component.py`

- [ ] **Step 1: 新增公共头文件**

Create `components/ui/include/ep_ui.h`:

```c
#ifndef EP_UI_H
#define EP_UI_H

int ep_ui_init(void);
int ep_ui_tick_inc(unsigned int elapsed_ms);
int ep_ui_process(void);
int ep_ui_deinit(void);

#endif
```

- [ ] **Step 2: 新增实现文件**

Create `components/ui/src/ep_ui.c`:

```c
#include "ep_ui.h"
#include "ep_osal_err.h"
#include "lvgl.h"

static int g_ui_initialized;

int ep_ui_init(void)
{
    if (g_ui_initialized) {
        return EP_OK;
    }

    lv_init();
    g_ui_initialized = 1;
    return EP_OK;
}

int ep_ui_tick_inc(unsigned int elapsed_ms)
{
    if (!g_ui_initialized) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_tick_inc(elapsed_ms);
    return EP_OK;
}

int ep_ui_process(void)
{
    if (!g_ui_initialized) {
        return EP_ERR_UNSUPPORTED;
    }

    (void)lv_timer_handler();
    return EP_OK;
}

int ep_ui_deinit(void)
{
    if (!g_ui_initialized) {
        return EP_OK;
    }

    lv_deinit();
    g_ui_initialized = 0;
    return EP_OK;
}
```

- [ ] **Step 3: 新增组件 CMake**

Create `components/ui/CMakeLists.txt`:

```cmake
add_library(ep_components_ui STATIC
  src/ep_ui.c
)

target_include_directories(ep_components_ui
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)

target_link_libraries(ep_components_ui
  PRIVATE
    ep_thirdparty_lvgl
)
```

- [ ] **Step 4: 接入顶层 CMake**

Modify `CMakeLists.txt` and add `components/ui` after existing components:

```cmake
add_subdirectory(components/event)
add_subdirectory(components/timer)
add_subdirectory(components/log)
add_subdirectory(components/file)
add_subdirectory(components/config)
add_subdirectory(components/ui)
```

- [ ] **Step 5: 让 host 目标链接 UI 组件**

Modify `platforms/host/posix/CMakeLists.txt` target libraries:

```cmake
target_link_libraries(ep_platform_host_posix
  PRIVATE
    ep_core
    ep_app
    ep_components_timer
    ep_components_log
    ep_components_config
    ep_components_ui
    Threads::Threads
)
```

- [ ] **Step 6: 运行 UI 测试确认通过**

Run:

```bash
pytest tests/host_unit/test_lvgl_ui_component.py -v
```

Expected on macOS arm64:

```text
4 passed
```

Expected on non-Darwin arm64:

```text
3 passed, 1 skipped
```

- [ ] **Step 7: 提交实现**

Run:

```bash
git add CMakeLists.txt platforms/host/posix/CMakeLists.txt components/ui tests/host_unit/test_lvgl_ui_component.py
git commit -m "feat: 实现 LVGL 最小运行组件"
```

## Task 3: 增加 API contract 测试

**Files:**
- Create: `tests/api_contract/test_ui_headers.py`

- [ ] **Step 1: 写失败测试**

Create `tests/api_contract/test_ui_headers.py`:

```python
from pathlib import Path

from test_hal_headers import compile_header_standalone, require_compiler


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ui_header_is_platform_neutral():
    header = REPO_ROOT / "components/ui/include/ep_ui.h"
    text = header.read_text(encoding="utf-8")

    forbidden_tokens = [
        "lvgl.h",
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
        "platforms/",
    ]

    for token in forbidden_tokens:
        assert token not in text


def test_ui_header_compiles_standalone():
    compiler = require_compiler()
    compile_header_standalone(
        compiler,
        "components/ui/include/ep_ui.h",
        include_dirs=["components/ui/include"],
    )
```

- [ ] **Step 2: 运行单个 API contract 测试**

Run:

```bash
pytest tests/api_contract/test_ui_headers.py -v
```

Expected:

```text
2 passed
```

如果第一步在 Task 2 后执行，该测试可能直接通过；这仍然是 API contract 补充测试，重点是防止后续公共头文件泄漏 LVGL 或平台头文件。

- [ ] **Step 3: 提交 API contract 测试**

Run:

```bash
git add tests/api_contract/test_ui_headers.py
git commit -m "test: 增加 UI 头文件契约测试"
```

## Task 4: 全量验证

**Files:**
- Verify only.

- [ ] **Step 1: 运行完整 pytest**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
所有测试通过
```

macOS arm64 上预期 UI smoke 测试执行；Ubuntu CI 上预期 UI smoke 测试跳过。

- [ ] **Step 2: 运行 CMake configure/build**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
configure 成功
build 成功
```

- [ ] **Step 3: 运行 host bin**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
进程返回 0
输出仍包含 app lifecycle start
输出仍包含 app lifecycle done
```

- [ ] **Step 4: 检查空白和工作树状态**

Run:

```bash
git diff --check
git status --short --branch
```

Expected:

```text
git diff --check 无输出
git status 显示当前分支干净
```

## Task 5: PR 和合并清理

**Files:**
- GitHub PR only.

- [ ] **Step 1: 推送分支**

Run:

```bash
git push -u origin docs/lvgl-ui-design
```

- [ ] **Step 2: 创建中文 PR**

Run:

```bash
gh pr create --base main --head docs/lvgl-ui-design --title "feat: 实现 LVGL 最小运行组件" --body "$(cat <<'EOF'
## Summary
- 新增 `components/ui` 最小 LVGL 生命周期组件
- 提供 `ep_ui_init/tick_inc/process/deinit` 接口
- 增加 host 单元测试和 UI 头文件契约测试

## Validation
- [x] `pytest tests/host_unit tests/api_contract -v`
- [x] `cmake -S . -B build`
- [x] `cmake --build build`
- [x] `./build/platforms/host/posix/ep_platform_host_posix`
- [x] `git diff --check`

## Notes
- 本 PR 不封装 LVGL 控件 API
- 本 PR 不接窗口、显示 flush 或输入设备
- 本 PR 不改变当前 host bin 自动退出行为
EOF
)"
```

- [ ] **Step 3: 等待 CI**

Run:

```bash
gh pr checks --watch --interval 5
```

Expected:

```text
host-tests pass
```

- [ ] **Step 4: squash merge**

Run:

```bash
gh pr merge --squash --delete-branch --subject "feat: 实现 LVGL 最小运行组件" --body $'实现 LVGL 最小运行组件：\n\n- 新增 components/ui 生命周期组件\n- 提供 ep_ui_init/tick_inc/process/deinit 接口\n- 增加 host 单元测试和 UI 头文件契约测试'
```

- [ ] **Step 5: 本地清理**

If `gh pr merge` reports local worktree failure because `main` is already used by the main worktree, run:

```bash
cd /Users/yuwei/Documents/KitchenIdea/项目/C08/embedded-platform-core
git pull --ff-only
git worktree remove .worktrees/docs-lvgl-ui-design
git branch -d docs/lvgl-ui-design
git fetch --prune
git status --short --branch
git branch -vv
git branch -r
git worktree list
```
