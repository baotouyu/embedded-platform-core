# host LVGL 独立 demo 程序 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `ep_host_lvgl_demo` 独立可执行程序，让 host macOS 上的 LVGL + SDL2 窗口可以长期运行并手动退出。

**Architecture:** `components/ui` 继续只管理 LVGL 生命周期，`platforms/host/posix/ui_port` 继续管理 host SDL2 display/input。新增 `platforms/host/posix/demos/lvgl_demo_main.c` 作为独立 demo 入口，复用 host UI port 和原生 LVGL API，不污染通用 `app/`。

**Tech Stack:** C11、CMake、pytest、LVGL 9.1、SDL2、现有 host OSAL time、现有 `ep_osal_err.h` 错误码。

---

## 文件结构

- 新增 `platforms/host/posix/demos/lvgl_demo_main.c`
  - 独立 demo 入口。
  - 创建最小 LVGL 页面。
  - 运行主循环直到按钮或窗口关闭请求退出。
- 修改 `platforms/host/posix/ui_port/ep_host_ui_port.h`
  - 增加 `ep_host_ui_port_should_quit()`。
- 修改 `platforms/host/posix/ui_port/ep_host_ui_port.c`
  - 保存退出请求状态。
  - 处理 SDL quit 事件。
- 修改 `platforms/host/posix/CMakeLists.txt`
  - 在 Apple arm64 下新增 `ep_host_lvgl_demo` 目标。
  - 复用 host UI port、host OSAL time、UI 组件和 LVGL 预编译库。
- 新增或修改 `tests/host_unit/test_host_lvgl_demo.py`
  - 覆盖 demo 文件、CMake 接线、退出接口、平台边界和 macOS 构建。

## Task 1: 添加 demo 边界红测

**Files:**
- Create: `tests/host_unit/test_host_lvgl_demo.py`

- [ ] **Step 1: 写失败测试**

创建 `tests/host_unit/test_host_lvgl_demo.py`：

```python
import platform
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_lvgl_demo_source_and_behavior_are_declared():
    demo = REPO_ROOT / "platforms/host/posix/demos/lvgl_demo_main.c"

    assert demo.exists()

    text = demo.read_text()
    assert "ep_ui_init()" in text
    assert "ep_host_ui_port_init()" in text
    assert "ep_ui_process()" in text
    assert "ep_sleep_ms(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS)" in text
    assert "#define EP_HOST_LVGL_DEMO_FRAME_DELAY_MS 16u" in text
    assert "ep_host_ui_port_should_quit()" in text
    assert "lv_label_create" in text
    assert "lv_button_create" in text
    assert "lv_obj_add_event_cb" in text
    assert "EP_HOST_LVGL_DEMO_EXIT_TEXT" in text


def test_host_ui_port_exposes_quit_query_without_polluting_public_ui():
    header = (REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.h").read_text()
    source = (REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.c").read_text()
    public_ui = (REPO_ROOT / "components/ui/include/ep_ui.h").read_text()

    assert "int ep_host_ui_port_should_quit(void);" in header
    assert "SDL_PeepEvents" in source
    assert "SDL_PEEKEVENT" in source
    assert "SDL_QUIT" in source
    assert "ep_host_ui_port_should_quit" in source

    assert "ep_host_ui_port" not in public_ui
    assert "SDL" not in public_ui


def test_host_cmake_builds_lvgl_demo_only_for_host_macos():
    cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text()
    app_cmake = (REPO_ROOT / "app/CMakeLists.txt").read_text()

    assert "add_executable(ep_host_lvgl_demo" in cmake
    assert "demos/lvgl_demo_main.c" in cmake
    assert "ui_port/ep_host_ui_port.c" in cmake
    assert "ep_components_ui" in cmake
    assert "ep_thirdparty_lvgl" in cmake
    assert "EP_HAS_HOST_SDL2_UI=1" in cmake
    assert 'if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")' in cmake

    assert "ep_host_lvgl_demo" not in app_cmake
    assert "lvgl_demo_main.c" not in app_cmake


def test_host_lvgl_demo_builds_on_macos_arm64():
    if platform.system() != "Darwin" or platform.machine() not in {"arm64", "aarch64"}:
        pytest.skip("host LVGL demo only builds on macOS arm64")

    build_dir = REPO_ROOT / "build"
    subprocess.run(["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)], check=True)
    subprocess.run(["cmake", "--build", str(build_dir), "--target", "ep_host_lvgl_demo"], check=True)
    assert (build_dir / "platforms/host/posix/ep_host_lvgl_demo").exists()
```

- [ ] **Step 2: 运行红测，确认失败原因正确**

Run:

```bash
pytest tests/host_unit/test_host_lvgl_demo.py -v
```

Expected:

```text
FAILED ... assert demo.exists()
```

测试应该因为 demo 文件不存在、退出接口不存在、CMake 目标不存在而失败。

- [ ] **Step 3: 提交红测**

```bash
git add tests/host_unit/test_host_lvgl_demo.py
git commit -m "test: 增加 host LVGL demo 红测"
```

## Task 2: 实现 host UI port 退出查询

**Files:**
- Modify: `platforms/host/posix/ui_port/ep_host_ui_port.h`
- Modify: `platforms/host/posix/ui_port/ep_host_ui_port.c`

- [ ] **Step 1: 修改头文件**

在 `platforms/host/posix/ui_port/ep_host_ui_port.h` 中暴露接口：

```c
#ifndef EP_HOST_UI_PORT_H
#define EP_HOST_UI_PORT_H

int ep_host_ui_port_init(void);
int ep_host_ui_port_deinit(void);
int ep_host_ui_port_should_quit(void);

#endif
```

- [ ] **Step 2: 修改实现**

更新 `platforms/host/posix/ui_port/ep_host_ui_port.c`：

```c
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_keyboard.h"
#include "src/drivers/sdl/lv_sdl_mouse.h"
#include "src/drivers/sdl/lv_sdl_window.h"
#include <SDL2/SDL.h>

static int g_host_ui_port_initialized;
static int g_host_ui_port_should_quit;
static lv_display_t *g_host_ui_display;

int ep_host_ui_port_init(void)
{
    if (g_host_ui_port_initialized) {
        return EP_OK;
    }

    g_host_ui_display = lv_sdl_window_create(480, 320);
    if (g_host_ui_display == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_sdl_window_set_title(g_host_ui_display, "embedded-platform-core host SDL2");
    lv_sdl_mouse_create();
    lv_sdl_keyboard_create();

    g_host_ui_port_should_quit = 0;
    g_host_ui_port_initialized = 1;
    return EP_OK;
}

int ep_host_ui_port_deinit(void)
{
    g_host_ui_display = 0;
    g_host_ui_port_initialized = 0;
    g_host_ui_port_should_quit = 1;
    return EP_OK;
}

int ep_host_ui_port_should_quit(void)
{
    SDL_Event event;

    if (!g_host_ui_port_initialized) {
        return 1;
    }

    if (SDL_PeepEvents(&event, 1, SDL_PEEKEVENT, SDL_QUIT, SDL_QUIT) > 0) {
        g_host_ui_port_should_quit = 1;
    }

    return g_host_ui_port_should_quit;
}
```

- [ ] **Step 3: 运行局部测试**

Run:

```bash
pytest tests/host_unit/test_host_lvgl_demo.py::test_host_ui_port_exposes_quit_query_without_polluting_public_ui -v
```

Expected:

```text
PASSED
```

- [ ] **Step 4: 提交退出接口**

```bash
git add platforms/host/posix/ui_port/ep_host_ui_port.h platforms/host/posix/ui_port/ep_host_ui_port.c
git commit -m "feat: 增加 host UI 退出查询接口"
```

## Task 3: 新增独立 demo 源文件

**Files:**
- Create: `platforms/host/posix/demos/lvgl_demo_main.c`

- [ ] **Step 1: 创建 demo 源文件**

新增 `platforms/host/posix/demos/lvgl_demo_main.c`：

```c
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_ui.h"
#include "lvgl.h"

#define EP_HOST_LVGL_DEMO_FRAME_DELAY_MS 16u
#define EP_HOST_LVGL_DEMO_EXIT_TEXT "Exit"

static int g_demo_should_exit;

static void ep_host_lvgl_demo_on_exit(lv_event_t *event)
{
    (void)event;
    g_demo_should_exit = 1;
}

static int ep_host_lvgl_demo_create_screen(void)
{
    lv_obj_t *screen = lv_screen_active();
    lv_obj_t *title = lv_label_create(screen);
    lv_obj_t *status = lv_label_create(screen);
    lv_obj_t *button = lv_button_create(screen);
    lv_obj_t *button_label = 0;

    if ((screen == 0) || (title == 0) || (status == 0) || (button == 0)) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(title, "embedded-platform-core");
    lv_obj_align(title, LV_ALIGN_CENTER, 0, -42);

    lv_label_set_text(status, "host macOS LVGL 9.1 + SDL2");
    lv_obj_align(status, LV_ALIGN_CENTER, 0, -12);

    lv_obj_set_size(button, 96, 36);
    lv_obj_align(button, LV_ALIGN_CENTER, 0, 42);
    lv_obj_add_event_cb(button, ep_host_lvgl_demo_on_exit, LV_EVENT_CLICKED, 0);

    button_label = lv_label_create(button);
    if (button_label == 0) {
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(button_label, EP_HOST_LVGL_DEMO_EXIT_TEXT);
    lv_obj_center(button_label);

    return EP_OK;
}

int main(void)
{
    int rc = ep_ui_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_host_ui_port_init();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    rc = ep_host_lvgl_demo_create_screen();
    if (rc != EP_OK) {
        (void)ep_host_ui_port_deinit();
        (void)ep_ui_deinit();
        return rc;
    }

    while (!g_demo_should_exit && !ep_host_ui_port_should_quit()) {
        rc = ep_ui_process();
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        ep_sleep_ms(EP_HOST_LVGL_DEMO_FRAME_DELAY_MS);
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
```

- [ ] **Step 2: 运行 demo 源码测试**

Run:

```bash
pytest tests/host_unit/test_host_lvgl_demo.py::test_host_lvgl_demo_source_and_behavior_are_declared -v
```

Expected:

```text
PASSED
```

- [ ] **Step 3: 提交 demo 源文件**

```bash
git add platforms/host/posix/demos/lvgl_demo_main.c
git commit -m "feat: 增加 host LVGL 独立 demo 入口"
```

## Task 4: 接入 CMake 目标

**Files:**
- Modify: `platforms/host/posix/CMakeLists.txt`

- [ ] **Step 1: 修改 CMake**

在 `if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")` 块内新增目标：

```cmake
  add_executable(ep_host_lvgl_demo
    demos/lvgl_demo_main.c
    ui_port/ep_host_ui_port.c
    osal_port/ep_host_osal_time.c
  )

  target_include_directories(ep_host_lvgl_demo
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${CMAKE_SOURCE_DIR}/osal/include
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_host_lvgl_demo
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_host_lvgl_demo
    PRIVATE
      ep_components_ui
      ep_components_log
      ep_thirdparty_lvgl
  )
```

- [ ] **Step 2: 运行 CMake 边界测试**

Run:

```bash
pytest tests/host_unit/test_host_lvgl_demo.py::test_host_cmake_builds_lvgl_demo_only_for_host_macos -v
```

Expected:

```text
PASSED
```

- [ ] **Step 3: 运行 macOS 构建测试**

Run:

```bash
pytest tests/host_unit/test_host_lvgl_demo.py::test_host_lvgl_demo_builds_on_macos_arm64 -v
```

Expected on macOS arm64:

```text
PASSED
```

Expected on other platforms:

```text
SKIPPED
```

- [ ] **Step 4: 提交 CMake 接入**

```bash
git add platforms/host/posix/CMakeLists.txt
git commit -m "feat: 接入 host LVGL demo 构建目标"
```

## Task 5: 全量验证和 PR

**Files:**
- No new source files.

- [ ] **Step 1: 运行全部测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
PASSED
```

- [ ] **Step 2: 运行 CMake 配置和构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
Build files have been written to: .../build
[100%] Built target ep_host_lvgl_demo
```

- [ ] **Step 3: 验证主程序仍然自动退出**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
app lifecycle start
app lifecycle done
```

命令应自动退出，退出码为 0。

- [ ] **Step 4: 人工运行 demo**

Run:

```bash
./build/platforms/host/posix/ep_host_lvgl_demo
```

Expected:

```text
打开一个 LVGL SDL2 窗口，显示 embedded-platform-core、host macOS LVGL 9.1 + SDL2 和 Exit 按钮。点击 Exit 或关闭窗口后程序退出，退出码为 0。
```

- [ ] **Step 5: 检查格式和工作区**

Run:

```bash
git diff --check
git status --short --branch
```

Expected:

```text
git diff --check 没有输出
工作区只包含本 PR 相关提交
```

- [ ] **Step 6: 推送并创建 PR**

```bash
git push -u origin feature/host-lvgl-demo
gh pr create --base main --head feature/host-lvgl-demo --title "feat: 增加 host LVGL 独立 demo 程序" --body "$(cat <<'EOF'
## 变更

- 新增 host macOS 独立 LVGL demo 目标 `ep_host_lvgl_demo`
- 增加 host UI port 退出查询接口
- demo 使用原生 LVGL API 创建最小页面和退出按钮
- 保留 `ep_platform_host_posix` 自动退出行为

## 验证

- `pytest tests/host_unit tests/api_contract -v`
- `cmake -S . -B build`
- `cmake --build build`
- `./build/platforms/host/posix/ep_platform_host_posix`
- `./build/platforms/host/posix/ep_host_lvgl_demo`
EOF
)"
```
