# LVGL 最小运行组件设计

## 背景

当前工程已经接入 `host_macos` 的 LVGL 9.1.0 预编译包：

- `third_party/prebuilt/lvgl/host_macos/include` 提供 LVGL 头文件和 `lv_conf.h`。
- `third_party/prebuilt/lvgl/host_macos/lib/liblvgl.a` 提供 macOS arm64 静态库。
- `cmake/modules/ep_lvgl_prebuilt.cmake` 提供 `ep_thirdparty_lvgl` imported target。
- 现有测试已经验证 `lv_init()` 和 `lv_deinit()` 在 macOS arm64 上可以链接运行。

这一步只解决了“库和头文件怎么放进工程”的问题，还没有工程自己的 UI/LVGL 生命周期入口。下一步应该把 LVGL 的最小运行入口接成一个组件，让 app 和后续平台适配有统一调用点。

## 目标

- 新增 `components/ui` 组件，作为工程自己的 UI/LVGL 生命周期层。
- 组件内部调用 LVGL 9.1 API。
- 提供最小公共接口，用于初始化、处理 LVGL 定时任务、推进 tick、反初始化。
- 让上层可以继续直接使用 LVGL 原生控件 API，不在本组件里封装按钮、label、screen 等复杂接口。
- 让 host macOS 可以通过 CMake 链接 `ep_thirdparty_lvgl`。
- 保持公共头文件平台无关，不暴露 macOS、Linux、RT-Thread 或 vendor SDK 头文件。
- 为后续匠芯创 Luban-Lite、全志 Linux 等平台替换各自 LVGL 静态库预留结构。

## 非目标

- 不封装 LVGL 控件 API。
- 不设计工程自己的 UI widget 层。
- 不接 macOS 窗口。
- 不接 SDL、Wayland、Framebuffer、DRM、触摸、鼠标或键盘输入。
- 不实现 LVGL display driver、input driver 或 flush 回调。
- 不接 Luban-Lite、RT-Thread 或全志 SDK。
- 不改变 `app_main()` 当前自动退出的行为。
- 不把 LVGL 初始化强行塞进 `ep_framework_init()`。

## 方案比较

### 方案一：app 直接调用 LVGL

`app/main.c` 或后续业务代码直接调用 `lv_init()`、`lv_tick_inc()`、`lv_timer_handler()` 和 `lv_deinit()`。

优点：

- 改动最少。
- 不需要新增组件。

缺点：

- LVGL 生命周期会散落在 app 或平台代码里。
- 后续不同平台的 init、tick、display port 接入容易分叉。
- 不符合当前工程“组件统一暴露公共边界”的风格。

### 方案二：新增 `components/ui` 生命周期组件

新增 `components/ui/include/ep_ui.h` 和 `components/ui/src/ep_ui.c`，只提供非常薄的一层生命周期接口：

```c
int ep_ui_init(void);
int ep_ui_tick_inc(unsigned int elapsed_ms);
int ep_ui_process(void);
int ep_ui_deinit(void);
```

内部调用 LVGL：

- `ep_ui_init()` 调用 `lv_init()`。
- `ep_ui_tick_inc()` 调用 `lv_tick_inc(elapsed_ms)`。
- `ep_ui_process()` 调用 `lv_timer_handler()`。
- `ep_ui_deinit()` 调用 `lv_deinit()`。

优点：

- 上层有统一生命周期入口。
- 不封装 LVGL 控件 API，避免把 LVGL 复杂 API 复制一遍。
- 后续平台 port 可以接到同一个组件边界下。
- 和现有 `components/log`、`components/timer`、`components/config` 的工程结构一致。

缺点：

- 增加一个组件目录和少量公共 API。
- 第一版暂时还看不到真实窗口画面。

### 方案三：直接做 macOS 显示窗口和输入

在 host macOS 上直接接 SDL 或 LVGL macOS display/input port，让程序运行后可以看到窗口。

优点：

- 很快能看到可视化效果。
- 方便后续做 UI demo。

缺点：

- 会提前引入窗口库、显示刷新、输入事件和主循环问题。
- CI 和无图形环境适配成本更高。
- 当前还没有统一 UI 生命周期层，直接做窗口容易把平台细节写散。

## 推荐方案

采用方案二：新增 `components/ui` 生命周期组件。

理由：

- 当前阶段目标是先把 LVGL 从“能链接”推进到“工程有统一运行入口”。
- 这一步应该保持小范围，先不处理显示和输入。
- 组件只封生命周期，不封 LVGL 控件 API，符合“LVGL API 太多太复杂，不做二次封装”的判断。
- 后续接 macOS 窗口、匠芯创 Luban-Lite SDK 或全志 Linux LVGL port 时，都能挂在这个组件之后继续扩展。

## 公共接口

新增公共头文件：

```text
components/ui/include/ep_ui.h
```

第一版接口：

```c
#ifndef EP_UI_H
#define EP_UI_H

int ep_ui_init(void);
int ep_ui_tick_inc(unsigned int elapsed_ms);
int ep_ui_process(void);
int ep_ui_deinit(void);

#endif
```

接口语义：

- `ep_ui_init()` 初始化 UI/LVGL 生命周期。重复调用返回成功，不重复执行 `lv_init()`。
- `ep_ui_tick_inc(elapsed_ms)` 推进 LVGL tick。必须在初始化后调用。
- `ep_ui_process()` 执行一次 LVGL timer handler。必须在初始化后调用。
- `ep_ui_deinit()` 反初始化 LVGL。未初始化时返回成功。

第一版不暴露 LVGL 类型。原因是这个头文件是工程公共生命周期入口，不是控件 API 包装层。业务代码如果需要创建对象，可以直接包含 `lvgl.h` 调用原生 LVGL API。

## 错误处理

第一版错误语义：

- `ep_ui_init()` 成功返回 `EP_OK`。
- `ep_ui_tick_inc()` 未初始化时返回 `EP_ERR_UNSUPPORTED`。
- `ep_ui_process()` 未初始化时返回 `EP_ERR_UNSUPPORTED`。
- `ep_ui_deinit()` 未初始化时返回 `EP_OK`。
- `elapsed_ms == 0` 合法，仍调用 `lv_tick_inc(0)` 或直接返回 `EP_OK` 均可，第一版建议调用 LVGL 原生接口以保持行为简单。

如果 LVGL API 本身没有返回错误码，组件内部按成功处理。

## CMake 结构

新增目录：

```text
components/ui/
├── CMakeLists.txt
├── include/
│   └── ep_ui.h
└── src/
    └── ep_ui.c
```

新增 target：

```text
ep_components_ui
```

链接关系：

```text
ep_components_ui
  PRIVATE ep_thirdparty_lvgl
```

`ep_components_ui` 的 public include 只暴露 `components/ui/include`。

是否把 LVGL include 作为 public 传播需要谨慎。第一版推荐不通过 `ep_components_ui` 暴露 `lvgl.h`，业务代码如果需要直接使用 LVGL API，可以显式链接或包含 `ep_thirdparty_lvgl` 所提供的 include。这样可以避免把 `ep_ui.h` 和 LVGL 类型绑定得太死。

## Framework 和 app 接入策略

第一版不自动把 `ep_ui_init()` 加进 `ep_framework_init()`。

原因：

- 目前 host app 是自动退出的生命周期自检，不是图形应用主循环。
- 还没有 display driver 时，自动初始化 UI 对当前 app 没有必要。
- 后续可以在真正需要 UI 的 app 或平台启动流程中显式调用 `ep_ui_init()`。
- 等 macOS display/input port 成熟后，再单独设计“framework 是否自动启动 UI”的配置项。

第一版只保证组件能编译、链接和最小运行，不改变当前 host bin 输出行为。

## 平台适配边界

`components/ui` 只依赖：

- `components/ui/include/ep_ui.h`
- `osal/include/ep_osal_err.h`
- `lvgl.h`

不得包含：

- `pthread.h`
- `unistd.h`
- `signal.h`
- `rtthread.h`
- Linux/macOS 平台原生 UI 头文件
- 匠芯创或全志 SDK 头文件
- `platforms/*` 下的私有头文件

后续平台显示和输入适配应单独进入平台目录或平台专属组件 port，例如：

```text
platforms/host/macos/ui_port/
platforms/linux/allwinner/ui_port/
platforms/rtos/luban_lite/ui_port/
```

这些 port 再与 `components/ui` 组合，而不是把平台代码写进 `components/ui`。

## 测试策略

新增 host 单元测试，覆盖：

- `components/ui` 目录结构存在。
- `ep_ui.h` 定义最小公共接口。
- `ep_ui.h` 不包含 `lvgl.h` 或平台原生头文件。
- `ep_ui.c` 调用 `lv_init()`、`lv_tick_inc()`、`lv_timer_handler()`、`lv_deinit()`。
- `ep_components_ui` 在 CMake 中链接 `ep_thirdparty_lvgl`。
- 一个 CMake smoke 测试可以链接 `ep_components_ui` 并调用 `ep_ui_init()`、`ep_ui_tick_inc()`、`ep_ui_process()`、`ep_ui_deinit()`。

macOS arm64 环境可以执行真实链接运行；Ubuntu CI 只能验证源码结构、CMake 结构，以及不触发 macOS 静态库链接的测试。涉及 `liblvgl.a` 的可执行 smoke 测试需要和当前 LVGL prebuilt 测试一样跳过非 Darwin arm64。

## 验收标准

- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 通过。
- `cmake --build build` 通过。
- `./build/platforms/host/posix/ep_platform_host_posix` 行为不变，仍能自动退出。
- `components/ui/include/ep_ui.h` 不暴露 LVGL 类型和平台原生类型。
- `components/ui/src/ep_ui.c` 不包含平台原生头文件。
- `ep_components_ui` 能在 macOS arm64 上链接并运行最小 LVGL 生命周期 smoke。

## 后续扩展

本设计完成后，后续可以继续按小步推进：

- 在 host macOS 上新增最小 display/window port。
- 增加一个 LVGL demo app，直接使用原生 `lvgl.h` 创建 label 或按钮。
- 设计 UI 主循环和退出控制。
- 接入输入设备。
- 为匠芯创 Luban-Lite 增加自己的 LVGL prebuilt 包选择。
- 为全志 Linux 增加自己的 LVGL prebuilt 包选择。
