# host macOS SDL2 UI port 设计

## 背景

当前主工程已经有两层基础：

- `third_party/prebuilt/lvgl/host_macos` 保存 LVGL 9.1 host macOS 预编译包。
- `components/ui` 提供平台无关的 LVGL 生命周期接口：`ep_ui_init()`、`ep_ui_tick_inc()`、`ep_ui_process()`、`ep_ui_deinit()`。

刚完成的 `lvgl-prebuilt-host-macos` 仓库已经把 host macOS 包升级为 SDL2 display/input 后端包。主工程下一步不应该重新移植 LVGL，也不应该在 `components/ui` 里写 SDL2 细节，而应该消费新的预编译包，并在 host 平台目录下新增最小 UI port。

## 目标

- 更新主工程内置的 `host_macos` LVGL 预编译包到 SDL2 后端版本。
- 让 CMake 能根据 `lvgl_package.txt` 识别 SDL2 后端并接入 `sdl2-config`。
- 在 host macOS 上新增最小 SDL2 UI port，创建 LVGL SDL2 window、mouse、keyboard。
- 让 host demo 可以创建一个最小 LVGL label，并跑若干帧后退出。
- 保持 `components/ui` 平台无关，不包含 SDL2、macOS、Linux、RT-Thread 或厂商 SDK 头文件。
- 为后续匠芯创 Luban-Lite、全志 Linux 等平台各自接入平台 port 保留边界。

## 非目标

- 不在主工程编译 LVGL 源码。
- 不在主工程维护 LVGL 官方 SDL2 driver。
- 不封装 LVGL 控件 API。
- 不把 SDL2 逻辑写入 `components/ui`。
- 不接匠芯创 Luban-Lite、全志 Linux 或其他真实芯片平台。
- 不把当前 app 改成长期运行的正式图形应用主循环。
- 不引入 SDL2_image 或 LVGL SDL draw backend。

## 方案比较

### 方案一：只更新预编译包，不做窗口 port

把 `third_party/prebuilt/lvgl/host_macos` 更新到新包，但主程序仍只跑 `lv_init()`、`lv_timer_handler()`、`lv_deinit()`。

优点：

- 改动最小。
- 低风险。

缺点：

- Mac 上仍然看不到窗口。
- 无法验证主工程是否真正能使用 SDL2 display/input 后端。
- SDL2 依赖只存在于包里，主工程消费路径还没有打通。

### 方案二：主工程消费新包，并新增 host 平台 UI port

更新预编译包；`ep_lvgl_prebuilt.cmake` 读取 manifest 后接入 SDL2；`platforms/host/posix/ui_port` 创建 SDL2 window/input；app 在 host 上创建最小 label 并跑若干帧。

优点：

- 能在 Mac 上看到真实 LVGL SDL2 窗口。
- 平台代码留在 `platforms/host/posix`，公共 UI 组件保持干净。
- 证明“预编译仓库负责适配，主工程负责消费”的流程是可行的。
- 后续其他平台可以照这个边界新增自己的 UI port。

缺点：

- 需要新增一个 host 平台 port。
- CMake 需要处理 SDL2 依赖。

### 方案三：直接在 `components/ui` 中创建 SDL2 window

把 `lv_sdl_window_create()`、`lv_sdl_mouse_create()`、`lv_sdl_keyboard_create()` 直接放到 `components/ui/src/ep_ui.c`。

优点：

- 文件更少。
- 调用链短。

缺点：

- `components/ui` 会绑定 host macOS SDL2，不再平台无关。
- 后续匠芯创和全志接入时会和 host 逻辑混在一起。
- 不符合当前工程按 `components/*` 与 `platforms/*` 分层的思想。

## 推荐方案

采用方案二：主工程消费新包，并新增 host 平台 UI port。

这个方案把三件事情分清楚：

- `lvgl-prebuilt-host-macos`：负责把 LVGL 9.1 + SDL2 driver 编成 host macOS `.a + .h + manifest`。
- `components/ui`：负责平台无关的 LVGL 生命周期。
- `platforms/host/posix/ui_port`：负责 host macOS 的 SDL2 display/input 创建。

这样主工程不会变成 LVGL 移植仓库，也不会把 host SDL2 代码污染到公共 UI 组件里。

## 组件边界

### 预编译包

`third_party/prebuilt/lvgl/host_macos` 必须从 `lvgl-prebuilt-host-macos` 的 `dist/lvgl/host_macos` 同步，包含：

- `include/lvgl.h`
- `include/lv_conf.h`
- `include/src/...`
- `lib/liblvgl.a`
- `LVGL_LICENCE.txt`
- `lvgl_package.txt`

manifest 至少需要包含：

```text
platform=host_macos
display_backend=sdl2
input_backend=sdl2
sdl2.version=...
sdl2.cflags=...
sdl2.libs=...
```

### CMake 依赖

`cmake/modules/ep_lvgl_prebuilt.cmake` 继续提供 `ep_thirdparty_lvgl` imported target。

当 manifest 包含 `display_backend=sdl2` 或 `input_backend=sdl2` 时：

- 查找 `sdl2-config`。
- 读取 `sdl2-config --cflags`。
- 读取 `sdl2-config --prefix` 并加入 `${prefix}/include`，兼容 `#include <SDL2/SDL.h>`。
- 读取 `sdl2-config --libs`。
- 把 SDL2 include、compile options、link options 绑定到 `ep_thirdparty_lvgl` 的 interface 属性上。

如果当前平台不是 Apple arm64，但仍尝试链接 `host_macos` 包，应该保持现有失败或跳过策略，不假装跨平台可用。

### host UI port

新增 host 平台专属接口，例如：

```text
platforms/host/posix/ui_port/ep_host_ui_port.h
platforms/host/posix/ui_port/ep_host_ui_port.c
```

第一版接口：

```c
int ep_host_ui_port_init(void);
int ep_host_ui_port_deinit(void);
```

实现职责：

- 包含 `lvgl.h` 和 LVGL SDL2 driver 头文件。
- 调用 `lv_sdl_window_create(480, 320)`。
- 调用 `lv_sdl_window_set_title()`。
- 调用 `lv_sdl_mouse_create()`。
- 调用 `lv_sdl_keyboard_create()`。
- 重复初始化返回成功。
- 未初始化时反初始化返回成功。

`ep_host_ui_port_deinit()` 不再额外调用 `lv_deinit()`，因为 LVGL 生命周期由 `components/ui` 管理。

### app demo

第一版 demo 只验证主工程能创建真实窗口和 LVGL 对象：

- `app_main()` 在 host macOS + SDL2 包可用时调用 `ep_ui_init()`。
- 调用 `ep_host_ui_port_init()` 创建窗口和输入。
- 用原生 LVGL API 创建 label，例如 `lv_label_create(lv_screen_active())`。
- 调用 `ep_ui_process()` 和 `ep_sleep_ms(16)` 跑约 30 帧。
- 调用 `ep_host_ui_port_deinit()`。
- 调用 `ep_ui_deinit()`。
- 保留原有 timer 自检和自动退出行为。

为了不影响非 host 平台，app 侧调用应通过 CMake 宏开关控制，例如：

```c
#if defined(EP_HAS_HOST_SDL2_UI)
...
#endif
```

`EP_HAS_HOST_SDL2_UI` 只在 host macOS 可执行目标上定义。

## 错误处理

- 找不到 `sdl2-config` 时，CMake 应给出明确错误，提示 `brew install sdl2`。
- `ep_host_ui_port_init()` 如果窗口创建失败，返回 `EP_ERR_UNSUPPORTED` 或已有合适错误码。
- app demo 任一步失败，返回错误码，让程序退出时能暴露问题。
- `ep_ui_deinit()` 仍负责 LVGL 反初始化。

## 测试策略

新增或更新测试覆盖以下内容：

- host macOS 包 manifest 包含 SDL2 后端字段。
- `lv_conf.h` 包含 `LV_USE_SDL 1` 和 `LV_USE_DRAW_SDL 0`。
- `ep_lvgl_prebuilt.cmake` 读取 SDL2 manifest 并接入 `sdl2-config`。
- host CMake 在 Apple arm64 下链接 `ep_components_ui` 和 host UI port。
- `platforms/host/posix/ui_port` 存在并包含 LVGL SDL2 driver 调用。
- `app/main.c` 通过 `EP_HAS_HOST_SDL2_UI` 包住 host demo，非 host 平台不受影响。
- macOS arm64 smoke 测试可以构建并运行 host binary。默认运行可以自动退出。

运行窗口 demo 依赖本机图形环境，CI 只要求构建和默认自动退出，不强制人工检查窗口画面。

## 验收标准

- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 通过。
- `cmake --build build` 通过。
- `./build/platforms/host/posix/ep_platform_host_posix` 在 macOS 上能自动退出。
- manifest 显示 `display_backend=sdl2` 和 `input_backend=sdl2`。
- `components/ui` 不包含 SDL2 或平台原生头文件。
- host SDL2 相关代码只出现在 `platforms/host/posix`、CMake SDL2 依赖接线、测试和文档中。

## 后续扩展

- 把 demo 从固定 30 帧改成可配置运行时长。
- 增加一个独立 UI demo app，不和当前 timer 自检混在一起。
- 增加键盘、鼠标输入行为验证。
- 为全志 Linux 增加自己的 LVGL prebuilt 包和 UI port。
- 为匠芯创 Luban-Lite 增加 SDK 侧 LVGL 包消费方式和 UI port。
