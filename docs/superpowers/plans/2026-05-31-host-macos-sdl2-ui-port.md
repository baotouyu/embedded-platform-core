# host macOS SDL2 UI port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `embedded-platform-core` 消费 host macOS SDL2 LVGL 预编译包，并在 Mac host 上创建最小 SDL2 LVGL 窗口 demo。

**Architecture:** `lvgl-prebuilt-host-macos` 继续负责 LVGL 9.1 + SDL2 的预编译产物；主工程只同步 `dist/lvgl/host_macos`。`components/ui` 继续保持平台无关，host SDL2 display/input 创建放在 `platforms/host/posix/ui_port`。CMake 根据 manifest 识别 SDL2 后端并把 SDL2 编译、包含、链接参数挂到 `ep_thirdparty_lvgl`。

**Tech Stack:** C11、CMake、pytest、LVGL 9.1、LVGL SDL2 driver、Homebrew SDL2、GitHub flow。

---

## 文件结构

- Modify: `third_party/prebuilt/lvgl/host_macos/**`
  - 从 `/Users/yuwei/Documents/KitchenIdea/项目/C08/lvgl-prebuilt-host-macos/dist/lvgl/host_macos` 同步。
  - 新 manifest 必须包含 `display_backend=sdl2`、`input_backend=sdl2`、`sdl2.version`、`sdl2.cflags`、`sdl2.libs`。
- Modify: `cmake/modules/ep_lvgl_prebuilt.cmake`
  - 当 manifest 声明 SDL2 后端时查找 `sdl2-config`。
  - 读取 `--cflags`、`--prefix`、`--libs`。
  - 给 `ep_thirdparty_lvgl` 增加 SDL2 include、compile options、link options。
- Create: `platforms/host/posix/ui_port/ep_host_ui_port.h`
  - host 平台专属 UI port 头文件。
  - 暴露 `ep_host_ui_port_init()` 和 `ep_host_ui_port_deinit()`。
- Create: `platforms/host/posix/ui_port/ep_host_ui_port.c`
  - 包含 LVGL SDL2 driver 头文件。
  - 创建 480x320 窗口、mouse、keyboard。
  - 不调用 `lv_init()` 或 `lv_deinit()`。
- Modify: `platforms/host/posix/CMakeLists.txt`
  - host 可执行目标加入 `ui_port/ep_host_ui_port.c`。
  - Apple arm64 时定义 `EP_HAS_HOST_SDL2_UI=1`。
  - Apple arm64 时给 app 暴露 host ui port include。
- Modify: `app/CMakeLists.txt`
  - 当 `EP_HAS_HOST_SDL2_UI` 为真时，允许 `ep_app` 包含 host ui port 头文件并链接 `ep_components_ui`、`ep_thirdparty_lvgl`。
- Modify: `app/main.c`
  - 在 `EP_HAS_HOST_SDL2_UI` 下运行最小 LVGL SDL2 demo。
  - 保留原 timer 自检和自动退出。
- Modify: `tests/host_unit/test_lvgl_prebuilt.py`
  - 增加 manifest、`lv_conf.h`、CMake SDL2 接线测试。
- Create: `tests/host_unit/test_host_macos_sdl2_ui_port.py`
  - 覆盖 host ui port 文件、CMake 接线、app demo 宏隔离和 macOS smoke。
- Modify: `tests/host_unit/test_lvgl_ui_component.py`
  - 增加断言确保 `components/ui` 不包含 SDL2 和 host ui port 头文件。

## Task 1: 添加 SDL2 prebuilt 和 host UI port 红测

**Files:**
- Modify: `tests/host_unit/test_lvgl_prebuilt.py`
- Create: `tests/host_unit/test_host_macos_sdl2_ui_port.py`
- Modify: `tests/host_unit/test_lvgl_ui_component.py`

- [ ] **Step 1: 扩展 LVGL prebuilt 测试**

Modify `tests/host_unit/test_lvgl_prebuilt.py`:

```python
def test_lvgl_host_macos_package_declares_sdl2_backend():
    package_root = REPO_ROOT / "third_party/prebuilt/lvgl/host_macos"
    manifest_text = (package_root / "lvgl_package.txt").read_text(encoding="utf-8")
    lv_conf = (package_root / "include/lv_conf.h").read_text(encoding="utf-8")

    assert "display_backend=sdl2" in manifest_text
    assert "input_backend=sdl2" in manifest_text
    assert "sdl2.version=" in manifest_text
    assert "sdl2.cflags=" in manifest_text
    assert "sdl2.libs=" in manifest_text
    assert "#define LV_USE_SDL 1" in lv_conf
    assert "#define LV_USE_DRAW_SDL 0" in lv_conf
    assert "#define LV_SDL_INCLUDE_PATH <SDL2/SDL.h>" in lv_conf


def test_lvgl_prebuilt_cmake_wires_sdl2_from_manifest():
    module = (REPO_ROOT / "cmake/modules/ep_lvgl_prebuilt.cmake").read_text(encoding="utf-8")

    assert "display_backend=sdl2" in module
    assert "input_backend=sdl2" in module
    assert "find_program(EP_SDL2_CONFIG_EXECUTABLE sdl2-config REQUIRED)" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --cflags" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --prefix" in module
    assert "execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --libs" in module
    assert "separate_arguments(EP_SDL2_CFLAGS_LIST NATIVE_COMMAND" in module
    assert "separate_arguments(EP_SDL2_LIBS_LIST NATIVE_COMMAND" in module
    assert 'set(EP_SDL2_INCLUDE_DIR "${EP_SDL2_PREFIX}/include")' in module
    assert "INTERFACE_COMPILE_OPTIONS" in module
    assert "INTERFACE_LINK_OPTIONS" in module
    assert "INTERFACE_INCLUDE_DIRECTORIES" in module
```

- [ ] **Step 2: 新增 host UI port 测试**

Create `tests/host_unit/test_host_macos_sdl2_ui_port.py`:

```python
import platform
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_host_macos_sdl2_ui_port_files_and_api_are_present():
    header = REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.h"
    source = REPO_ROOT / "platforms/host/posix/ui_port/ep_host_ui_port.c"

    assert header.exists()
    assert source.exists()

    header_text = header.read_text(encoding="utf-8")
    assert "int ep_host_ui_port_init(void);" in header_text
    assert "int ep_host_ui_port_deinit(void);" in header_text
    assert "lvgl.h" not in header_text
    assert "SDL2/SDL.h" not in header_text

    source_text = source.read_text(encoding="utf-8")
    assert '#include "ep_host_ui_port.h"' in source_text
    assert '#include "ep_osal_err.h"' in source_text
    assert '#include "lvgl.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_window.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_mouse.h"' in source_text
    assert '#include "src/drivers/sdl/lv_sdl_keyboard.h"' in source_text
    assert "lv_sdl_window_create(480, 320)" in source_text
    assert "lv_sdl_window_set_title" in source_text
    assert "lv_sdl_mouse_create()" in source_text
    assert "lv_sdl_keyboard_create()" in source_text
    assert "lv_deinit" not in source_text


def test_host_cmake_wires_sdl2_ui_port_only_for_host_macos():
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(encoding="utf-8")
    app_cmake = (REPO_ROOT / "app/CMakeLists.txt").read_text(encoding="utf-8")

    assert "ui_port/ep_host_ui_port.c" in host_cmake
    assert "EP_HAS_HOST_SDL2_UI=1" in host_cmake
    assert "APPLE" in host_cmake
    assert "CMAKE_SYSTEM_PROCESSOR" in host_cmake
    assert "ui_port" in host_cmake
    assert "EP_HAS_HOST_SDL2_UI" in app_cmake
    assert "ep_components_ui" in app_cmake
    assert "ep_thirdparty_lvgl" in app_cmake


def test_app_runs_host_sdl2_demo_behind_compile_flag():
    app_main = (REPO_ROOT / "app/main.c").read_text(encoding="utf-8")

    assert "#if defined(EP_HAS_HOST_SDL2_UI)" in app_main
    assert '#include "ep_ui.h"' in app_main
    assert '#include "ep_host_ui_port.h"' in app_main
    assert '#include "lvgl.h"' in app_main
    assert "ep_ui_init()" in app_main
    assert "ep_host_ui_port_init()" in app_main
    assert "lv_label_create(lv_screen_active())" in app_main
    assert 'lv_label_set_text(label, "embedded-platform-core host SDL2")' in app_main
    assert "ep_ui_process()" in app_main
    assert "ep_sleep_ms(16u)" in app_main
    assert "ep_host_ui_port_deinit()" in app_main
    assert "ep_ui_deinit()" in app_main


def test_host_macos_binary_builds_and_runs_sdl2_demo():
    if platform.system() != "Darwin" or platform.machine() != "arm64":
        pytest.skip("host macOS SDL2 UI smoke only runs on macOS arm64")

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(REPO_ROOT / "build")],
        capture_output=True,
        text=True,
    )
    assert configure.returncode == 0, (
        f"configure failed\nstdout:\n{configure.stdout}\nstderr:\n{configure.stderr}"
    )

    build = subprocess.run(
        ["cmake", "--build", str(REPO_ROOT / "build")],
        capture_output=True,
        text=True,
    )
    assert build.returncode == 0, (
        f"build failed\nstdout:\n{build.stdout}\nstderr:\n{build.stderr}"
    )

    run = subprocess.run(
        [str(REPO_ROOT / "build/platforms/host/posix/ep_platform_host_posix")],
        capture_output=True,
        text=True,
    )
    assert run.returncode == 0, (
        f"run failed\nstdout:\n{run.stdout}\nstderr:\n{run.stderr}"
    )
```

- [ ] **Step 3: 加强 UI 组件边界测试**

Modify `tests/host_unit/test_lvgl_ui_component.py` in `test_ui_component_calls_lvgl_lifecycle_apis_without_platform_headers`:

```python
    forbidden_headers = [
        "pthread.h",
        "unistd.h",
        "signal.h",
        "rtthread.h",
        "windows.h",
        "SDL2/SDL.h",
        "lv_sdl_window.h",
        "ep_host_ui_port.h",
    ]
```

- [ ] **Step 4: 运行红测确认失败**

Run:

```bash
pytest tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_host_macos_package_declares_sdl2_backend tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_prebuilt_cmake_wires_sdl2_from_manifest tests/host_unit/test_host_macos_sdl2_ui_port.py -v
```

Expected:

```text
FAILED tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_host_macos_package_declares_sdl2_backend
FAILED tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_prebuilt_cmake_wires_sdl2_from_manifest
FAILED tests/host_unit/test_host_macos_sdl2_ui_port.py::test_host_macos_sdl2_ui_port_files_and_api_are_present
```

- [ ] **Step 5: 提交红测**

Run:

```bash
git add tests/host_unit/test_lvgl_prebuilt.py tests/host_unit/test_host_macos_sdl2_ui_port.py tests/host_unit/test_lvgl_ui_component.py
git commit -m "test: 增加 host macOS SDL2 UI port 红测"
```

## Task 2: 同步 host macOS SDL2 LVGL 预编译包

**Files:**
- Modify: `third_party/prebuilt/lvgl/host_macos/**`
- Test: `tests/host_unit/test_lvgl_prebuilt.py`

- [ ] **Step 1: 同步预编译包**

Run:

```bash
rsync -a --delete \
  /Users/yuwei/Documents/KitchenIdea/项目/C08/lvgl-prebuilt-host-macos/dist/lvgl/host_macos/ \
  third_party/prebuilt/lvgl/host_macos/
```

- [ ] **Step 2: 检查 manifest**

Run:

```bash
cat third_party/prebuilt/lvgl/host_macos/lvgl_package.txt
```

Expected output contains:

```text
display_backend=sdl2
input_backend=sdl2
sdl2.version=2.32.10
sdl2.cflags=-I/opt/homebrew/include/SDL2 -D_THREAD_SAFE
sdl2.libs=-L/opt/homebrew/lib -lSDL2
```

- [ ] **Step 3: 运行 prebuilt 包结构测试**

Run:

```bash
pytest tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_host_macos_package_declares_sdl2_backend -v
```

Expected:

```text
1 passed
```

- [ ] **Step 4: 提交预编译包更新**

Run:

```bash
git add third_party/prebuilt/lvgl/host_macos
git commit -m "build: 更新 host macOS SDL2 LVGL 预编译包"
```

## Task 3: 让 CMake 从 manifest 接入 SDL2

**Files:**
- Modify: `cmake/modules/ep_lvgl_prebuilt.cmake`
- Test: `tests/host_unit/test_lvgl_prebuilt.py`

- [ ] **Step 1: 修改 CMake 模块**

Replace `cmake/modules/ep_lvgl_prebuilt.cmake` with:

```cmake
set(EP_LVGL_PACKAGE "host_macos" CACHE STRING "LVGL prebuilt package name")

if(NOT DEFINED EP_PROJECT_ROOT)
  set(EP_PROJECT_ROOT "${CMAKE_CURRENT_LIST_DIR}/../..")
endif()

get_filename_component(EP_PROJECT_ROOT "${EP_PROJECT_ROOT}" ABSOLUTE)

set(EP_LVGL_ROOT "${EP_PROJECT_ROOT}/third_party/prebuilt/lvgl/${EP_LVGL_PACKAGE}")
set(EP_LVGL_INCLUDE_DIR "${EP_LVGL_ROOT}/include")
set(EP_LVGL_LIBRARY "${EP_LVGL_ROOT}/lib/liblvgl.a")
set(EP_LVGL_MANIFEST "${EP_LVGL_ROOT}/lvgl_package.txt")

if(NOT EXISTS "${EP_LVGL_MANIFEST}")
  message(FATAL_ERROR "LVGL manifest not found: ${EP_LVGL_MANIFEST}")
endif()

if(NOT EXISTS "${EP_LVGL_INCLUDE_DIR}/lvgl.h")
  message(FATAL_ERROR "LVGL header not found: ${EP_LVGL_INCLUDE_DIR}/lvgl.h")
endif()

if(NOT EXISTS "${EP_LVGL_INCLUDE_DIR}/lv_conf.h")
  message(FATAL_ERROR "LVGL config not found: ${EP_LVGL_INCLUDE_DIR}/lv_conf.h")
endif()

if(NOT EXISTS "${EP_LVGL_LIBRARY}")
  message(FATAL_ERROR "LVGL static library not found: ${EP_LVGL_LIBRARY}")
endif()

file(READ "${EP_LVGL_MANIFEST}" EP_LVGL_MANIFEST_TEXT)
if(NOT EP_LVGL_MANIFEST_TEXT MATCHES "lvgl.version=9\\.1\\.")
  message(FATAL_ERROR "LVGL package must use LVGL 9.1.x: ${EP_LVGL_MANIFEST}")
endif()

set(EP_LVGL_INTERFACE_INCLUDE_DIRS "${EP_LVGL_INCLUDE_DIR}")
set(EP_LVGL_INTERFACE_COMPILE_OPTIONS "")
set(EP_LVGL_INTERFACE_LINK_OPTIONS "")

if(EP_LVGL_MANIFEST_TEXT MATCHES "display_backend=sdl2" OR EP_LVGL_MANIFEST_TEXT MATCHES "input_backend=sdl2")
  find_program(EP_SDL2_CONFIG_EXECUTABLE sdl2-config REQUIRED)

  execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --cflags
    OUTPUT_VARIABLE EP_SDL2_CFLAGS
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --prefix
    OUTPUT_VARIABLE EP_SDL2_PREFIX
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  execute_process(COMMAND ${EP_SDL2_CONFIG_EXECUTABLE} --libs
    OUTPUT_VARIABLE EP_SDL2_LIBS
    OUTPUT_STRIP_TRAILING_WHITESPACE
  )

  separate_arguments(EP_SDL2_CFLAGS_LIST NATIVE_COMMAND "${EP_SDL2_CFLAGS}")
  separate_arguments(EP_SDL2_LIBS_LIST NATIVE_COMMAND "${EP_SDL2_LIBS}")
  set(EP_SDL2_INCLUDE_DIR "${EP_SDL2_PREFIX}/include")

  list(APPEND EP_LVGL_INTERFACE_INCLUDE_DIRS "${EP_SDL2_INCLUDE_DIR}")
  list(APPEND EP_LVGL_INTERFACE_COMPILE_OPTIONS ${EP_SDL2_CFLAGS_LIST})
  list(APPEND EP_LVGL_INTERFACE_LINK_OPTIONS ${EP_SDL2_LIBS_LIST})
endif()

if(NOT TARGET ep_thirdparty_lvgl)
  add_library(ep_thirdparty_lvgl STATIC IMPORTED GLOBAL)
  set_target_properties(ep_thirdparty_lvgl PROPERTIES
    IMPORTED_LOCATION "${EP_LVGL_LIBRARY}"
    INTERFACE_INCLUDE_DIRECTORIES "${EP_LVGL_INTERFACE_INCLUDE_DIRS}"
    INTERFACE_COMPILE_OPTIONS "${EP_LVGL_INTERFACE_COMPILE_OPTIONS}"
    INTERFACE_LINK_OPTIONS "${EP_LVGL_INTERFACE_LINK_OPTIONS}"
  )
endif()
```

- [ ] **Step 2: 运行 CMake SDL2 结构测试**

Run:

```bash
pytest tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_prebuilt_cmake_wires_sdl2_from_manifest -v
```

Expected:

```text
1 passed
```

- [ ] **Step 3: 运行 LVGL 链接 smoke**

Run:

```bash
pytest tests/host_unit/test_lvgl_prebuilt.py::test_lvgl_prebuilt_cmake_smoke_links_lv_init -v
```

Expected on macOS arm64:

```text
1 passed
```

- [ ] **Step 4: 提交 CMake SDL2 接线**

Run:

```bash
git add cmake/modules/ep_lvgl_prebuilt.cmake
git commit -m "build: 从 LVGL manifest 接入 SDL2 依赖"
```

## Task 4: 新增 host macOS SDL2 UI port

**Files:**
- Create: `platforms/host/posix/ui_port/ep_host_ui_port.h`
- Create: `platforms/host/posix/ui_port/ep_host_ui_port.c`
- Modify: `platforms/host/posix/CMakeLists.txt`
- Test: `tests/host_unit/test_host_macos_sdl2_ui_port.py`

- [ ] **Step 1: 新增 host UI port 头文件**

Create `platforms/host/posix/ui_port/ep_host_ui_port.h`:

```c
#ifndef EP_HOST_UI_PORT_H
#define EP_HOST_UI_PORT_H

int ep_host_ui_port_init(void);
int ep_host_ui_port_deinit(void);

#endif
```

- [ ] **Step 2: 新增 host UI port 实现**

Create `platforms/host/posix/ui_port/ep_host_ui_port.c`:

```c
#include "ep_host_ui_port.h"
#include "ep_osal_err.h"
#include "lvgl.h"
#include "src/drivers/sdl/lv_sdl_keyboard.h"
#include "src/drivers/sdl/lv_sdl_mouse.h"
#include "src/drivers/sdl/lv_sdl_window.h"

static int g_host_ui_port_initialized;
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

    g_host_ui_port_initialized = 1;
    return EP_OK;
}

int ep_host_ui_port_deinit(void)
{
    g_host_ui_display = 0;
    g_host_ui_port_initialized = 0;
    return EP_OK;
}
```

- [ ] **Step 3: 修改 host CMake**

Modify `platforms/host/posix/CMakeLists.txt` so `ui_port/ep_host_ui_port.c` is added only for Apple arm64:

```cmake
if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
  target_sources(ep_platform_host_posix
    PRIVATE
      ui_port/ep_host_ui_port.c
  )

  target_include_directories(ep_platform_host_posix
    PRIVATE
      ${CMAKE_CURRENT_SOURCE_DIR}/ui_port
  )

  target_compile_definitions(ep_platform_host_posix
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_platform_host_posix
    PRIVATE
      ep_components_ui
  )
endif()
```

Keep existing non-Apple target sources and libraries unchanged.

- [ ] **Step 4: 运行 host UI port 结构测试**

Run:

```bash
pytest tests/host_unit/test_host_macos_sdl2_ui_port.py::test_host_macos_sdl2_ui_port_files_and_api_are_present tests/host_unit/test_host_macos_sdl2_ui_port.py::test_host_cmake_wires_sdl2_ui_port_only_for_host_macos -v
```

Expected:

```text
2 passed
```

- [ ] **Step 5: 提交 host UI port**

Run:

```bash
git add platforms/host/posix/ui_port/ep_host_ui_port.h platforms/host/posix/ui_port/ep_host_ui_port.c platforms/host/posix/CMakeLists.txt
git commit -m "feat: 增加 host macOS SDL2 UI port"
```

## Task 5: 在 app 中运行最小 host SDL2 LVGL demo

**Files:**
- Modify: `app/CMakeLists.txt`
- Modify: `app/main.c`
- Test: `tests/host_unit/test_host_macos_sdl2_ui_port.py`
- Test: `tests/host_unit/test_lvgl_ui_component.py`

- [ ] **Step 1: 修改 app CMake 暴露 host demo 依赖**

Append to `app/CMakeLists.txt`:

```cmake
if(APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$")
  target_include_directories(ep_app
    PRIVATE
      ${CMAKE_SOURCE_DIR}/components/ui/include
      ${CMAKE_SOURCE_DIR}/platforms/host/posix/ui_port
      ${EP_LVGL_INCLUDE_DIR}
  )

  target_compile_definitions(ep_app
    PRIVATE
      EP_HAS_HOST_SDL2_UI=1
  )

  target_link_libraries(ep_app
    PRIVATE
      ep_components_ui
      ep_thirdparty_lvgl
  )
endif()
```

- [ ] **Step 2: 修改 app main 引入 host demo 头文件**

Modify the includes at the top of `app/main.c`:

```c
#include "app_events.h"
#include "app_main.h"
#include "ep_event.h"
#include "ep_log.h"
#include "ep_osal_err.h"
#include "ep_osal_time.h"
#include "ep_timer.h"

#if defined(EP_HAS_HOST_SDL2_UI)
#include "ep_host_ui_port.h"
#include "ep_ui.h"
#include "lvgl.h"
#endif
```

- [ ] **Step 3: 新增 host demo helper**

Add after `app_timer_done_handler` in `app/main.c`:

```c
#if defined(EP_HAS_HOST_SDL2_UI)
#define APP_HOST_UI_FRAME_COUNT 30u
#define APP_HOST_UI_FRAME_DELAY_MS 16u

static int app_run_host_sdl2_ui_demo(void)
{
    unsigned int frame;
    int rc = ep_ui_init();
    if (rc != EP_OK) {
        return rc;
    }

    rc = ep_host_ui_port_init();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    lv_obj_t *label = lv_label_create(lv_screen_active());
    if (label == 0) {
        (void)ep_host_ui_port_deinit();
        (void)ep_ui_deinit();
        return EP_ERR_UNSUPPORTED;
    }

    lv_label_set_text(label, "embedded-platform-core host SDL2");
    lv_obj_center(label);

    for (frame = 0u; frame < APP_HOST_UI_FRAME_COUNT; frame++) {
        rc = ep_ui_process();
        if (rc != EP_OK) {
            (void)ep_host_ui_port_deinit();
            (void)ep_ui_deinit();
            return rc;
        }

        ep_sleep_ms(APP_HOST_UI_FRAME_DELAY_MS);
    }

    rc = ep_host_ui_port_deinit();
    if (rc != EP_OK) {
        (void)ep_ui_deinit();
        return rc;
    }

    return ep_ui_deinit();
}
#endif
```

- [ ] **Step 4: 从 app_main 调用 host demo**

Add before final `"app lifecycle done"` log in `app_main()`:

```c
#if defined(EP_HAS_HOST_SDL2_UI)
    rc = app_run_host_sdl2_ui_demo();
    if (rc != EP_OK) {
        return rc;
    }
#endif
```

- [ ] **Step 5: 运行 app demo 结构测试**

Run:

```bash
pytest tests/host_unit/test_host_macos_sdl2_ui_port.py::test_app_runs_host_sdl2_demo_behind_compile_flag tests/host_unit/test_lvgl_ui_component.py::test_ui_component_calls_lvgl_lifecycle_apis_without_platform_headers -v
```

Expected:

```text
2 passed
```

- [ ] **Step 6: 提交 app demo**

Run:

```bash
git add app/CMakeLists.txt app/main.c tests/host_unit/test_lvgl_ui_component.py
git commit -m "feat: 运行 host macOS SDL2 LVGL 最小 demo"
```

## Task 6: 构建、调试并验证 host binary

**Files:**
- May modify: files from previous tasks if build exposes issues
- Test: `tests/host_unit/test_host_macos_sdl2_ui_port.py`

- [ ] **Step 1: 运行 host binary smoke 测试**

Run:

```bash
pytest tests/host_unit/test_host_macos_sdl2_ui_port.py::test_host_macos_binary_builds_and_runs_sdl2_demo -v
```

Expected on macOS arm64:

```text
1 passed
```

- [ ] **Step 2: 如果失败，使用 systematic-debugging**

If Step 1 fails:

1. Read the exact compile or run error.
2. Identify whether the failure is CMake dependency propagation, static link order, SDL2 runtime window creation, or app lifecycle.
3. Fix one cause at a time.
4. Re-run Step 1.

- [ ] **Step 3: 手动运行 host bin**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
I/app          ... app lifecycle start
I/app          ... app lifecycle done
```

If the SDL2 window cannot open in the current environment, capture the exact stderr/stdout and decide whether to guard runtime window execution behind an environment variable in a follow-up fix.

- [ ] **Step 4: 提交调试修正**

If no changes were required, do not create a commit. If code changes were required, add the exact files shown by `git status --short`, then commit:

```bash
git status --short
git add app/main.c app/CMakeLists.txt platforms/host/posix/CMakeLists.txt platforms/host/posix/ui_port/ep_host_ui_port.c platforms/host/posix/ui_port/ep_host_ui_port.h cmake/modules/ep_lvgl_prebuilt.cmake tests/host_unit/test_host_macos_sdl2_ui_port.py tests/host_unit/test_lvgl_prebuilt.py tests/host_unit/test_lvgl_ui_component.py
git commit -m "fix: 修正 host macOS SDL2 UI demo 构建运行"
```

## Task 7: 最终验证、PR、合并清理

**Files:**
- No planned file changes

- [ ] **Step 1: 运行完整测试**

Run:

```bash
pytest tests/host_unit tests/api_contract -v
```

Expected:

```text
all selected tests passed
```

- [ ] **Step 2: 运行完整构建**

Run:

```bash
cmake -S . -B build
cmake --build build
```

Expected:

```text
build succeeds
```

- [ ] **Step 3: 运行 host binary**

Run:

```bash
./build/platforms/host/posix/ep_platform_host_posix
```

Expected:

```text
exit code 0
```

- [ ] **Step 4: 检查 diff 和状态**

Run:

```bash
git diff --check
git status --short --branch
```

Expected:

```text
no diff check errors
clean working tree
```

- [ ] **Step 5: 推送分支**

Run:

```bash
git push -u origin feature/host-macos-sdl2-ui
```

- [ ] **Step 6: 创建 PR**

Run:

```bash
gh pr create --base main --head feature/host-macos-sdl2-ui --title "feat: 接入 host macOS SDL2 LVGL UI port" --body "$(cat <<'EOF'
## 变更内容

- 更新 host macOS LVGL 预编译包到 SDL2 display/input 后端版本。
- 根据 LVGL manifest 在 CMake 中接入 SDL2 编译和链接参数。
- 新增 host macOS SDL2 UI port，创建 LVGL SDL2 window、mouse、keyboard。
- 在 host app 中运行最小 LVGL label demo，并保持自动退出。

## 验证

- [ ] pytest tests/host_unit tests/api_contract -v
- [ ] cmake -S . -B build
- [ ] cmake --build build
- [ ] ./build/platforms/host/posix/ep_platform_host_posix
EOF
)"
```

- [ ] **Step 7: 等待 CI 并合并**

Run:

```bash
gh pr checks --watch
```

If checks pass, run:

```bash
gh pr merge --squash --delete-branch --subject "feat: 接入 host macOS SDL2 LVGL UI port" --body "接入 host macOS SDL2 LVGL UI port。"
```

- [ ] **Step 8: 清理本地**

After PR is merged:

```bash
cd /Users/yuwei/Documents/KitchenIdea/项目/C08/embedded-platform-core
git fetch origin
git pull --ff-only origin main
git worktree remove .worktrees/feature-host-macos-sdl2-ui
git branch -d feature/host-macos-sdl2-ui
git fetch --prune origin
git status --short --branch
git branch --all
```
