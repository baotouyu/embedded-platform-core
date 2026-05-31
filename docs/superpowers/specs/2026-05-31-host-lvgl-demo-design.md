# host LVGL 独立 demo 程序设计

## 背景

当前主工程已经能在 host macOS arm64 上消费 `host_macos` LVGL 9.1 预编译包，并通过 SDL2 创建最小窗口。现有入口是 `ep_platform_host_posix`，它在框架自检完成后跑 30 帧 LVGL demo，然后自动退出。

这个入口适合 CI 和冒烟测试，但不适合日常调试 UI。用户在 Mac 上验证 LVGL 页面、控件、输入事件时，需要一个可以长期运行、手动关闭的 demo 程序。

## 目标

- 新增独立可执行目标 `ep_host_lvgl_demo`。
- demo 只在 host macOS arm64 + SDL2 LVGL 包可用时构建。
- demo 启动后创建 SDL2 + LVGL 窗口，并一直运行到用户关闭窗口或按退出快捷键。
- 保留现有 `ep_platform_host_posix` 自动退出行为，用于框架自检和 CI。
- demo 使用原生 LVGL API 创建最小页面，不封装 LVGL 控件 API。
- 平台相关 SDL2 逻辑继续留在 `platforms/host/posix`。

## 非目标

- 不把主程序改成长期运行 UI 应用。
- 不在 `components/ui` 中加入 SDL2、macOS、Linux、RT-Thread 或厂商 SDK 头文件。
- 不引入 LVGL 控件二次封装。
- 不新增复杂页面系统、主题系统或资源系统。
- 不在这一 PR 适配匠芯创 Luban-Lite 或全志 Linux。

## 方案比较

### 方案一：把 `ep_platform_host_posix` 改成长运行

直接把当前 30 帧 demo 改成无限循环，关闭窗口后退出。

优点：

- 改动最少。
- 只有一个 host 可执行程序。

缺点：

- CI 和本地自检会被长期运行程序卡住。
- 框架自检入口和 UI 调试入口职责混在一起。
- 后续新增更多 UI demo 时不方便扩展。

### 方案二：保留主程序自检，新增独立 UI demo 目标

新增 `ep_host_lvgl_demo`，复用 `components/ui` 和 `platforms/host/posix/ui_port`，主程序仍然自动退出。

优点：

- 自检入口和 UI 调试入口分离。
- CI 继续运行自动退出的 `ep_platform_host_posix`。
- 用户可以单独运行 UI demo 长时间观察窗口。
- 后续可以在 demo 目标内扩展页面、输入、动画，不影响核心框架。

缺点：

- 多一个可执行目标和一个 demo 源文件。

### 方案三：把 demo 放到通用 `app/`

在 `app/` 中新增长期运行 LVGL demo，再由 host 目标调用。

优点：

- 业务代码目录能看到 UI demo。

缺点：

- demo 会天然带有 host SDL2 假设，放进通用 `app/` 容易污染平台边界。
- 匠芯创、全志等平台后续接入时容易被迫处理 host-only 逻辑。

## 推荐方案

采用方案二：保留 `ep_platform_host_posix` 的自动退出自检，再新增 `ep_host_lvgl_demo` 独立目标。

边界保持为：

- `components/ui`：只负责 LVGL 生命周期。
- `platforms/host/posix/ui_port`：负责 host macOS SDL2 display/input 创建。
- `platforms/host/posix/demos/lvgl_demo_main.c`：负责 demo 页面和主循环。

这样 Mac 上可以舒服地调 UI，CI 和主框架自检也不会被长期运行窗口影响。

## demo 行为

`ep_host_lvgl_demo` 启动流程：

1. 调用 `ep_ui_init()`。
2. 调用 `ep_host_ui_port_init()` 创建窗口、鼠标、键盘。
3. 使用原生 LVGL API 创建一个最小页面。
4. 循环调用 `ep_ui_process()`。
5. 每帧调用 `ep_sleep_ms(16)`，约等于 60 FPS。
6. 检测退出请求后调用 `ep_host_ui_port_deinit()` 和 `ep_ui_deinit()`。

第一版页面只放最小可见内容：

- 标题 label：`embedded-platform-core`
- 状态 label：`host macOS LVGL 9.1 + SDL2`
- 一个按钮：显示 `Exit`

按钮点击后请求退出。窗口关闭事件也应该能请求退出。

## host UI port 补充接口

当前 `ep_host_ui_port` 只有 init/deinit。为了让 demo 能感知窗口关闭，需要在 host 平台层增加最小查询接口：

```c
int ep_host_ui_port_should_quit(void);
```

接口语义：

- 返回 0 表示继续运行。
- 返回非 0 表示用户请求退出。
- 未初始化时返回非 0，避免 demo 在未创建窗口时死循环。

实现细节仍然只放在 `platforms/host/posix/ui_port`。如果 LVGL SDL2 driver 已经在 `ep_ui_process()` 内部处理 SDL 事件，port 层只需要读取 SDL quit 状态；如果需要补充事件轮询，也必须留在 host port 内。

## CMake 边界

`platforms/host/posix/CMakeLists.txt` 继续构建 `ep_platform_host_posix`。

当满足 `APPLE AND CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm64|aarch64)$"` 时，额外构建：

```text
ep_host_lvgl_demo
```

该目标链接：

- `ep_components_ui`
- `ep_components_log`
- `ep_thirdparty_lvgl`
- host OSAL 时间实现需要的源文件

如果 Linux CI 配置工程，不应该因为缺少 host macOS SDL2 demo 而失败。

## 错误处理

- `ep_ui_init()` 失败时直接返回错误码。
- `ep_host_ui_port_init()` 失败时释放 UI 生命周期后返回错误码。
- LVGL 对象创建失败时返回 `EP_ERR_UNSUPPORTED`。
- 主循环中 `ep_ui_process()` 失败时退出并返回错误码。
- 退出按钮和窗口关闭都按正常退出处理，返回 0。

## 测试策略

新增或更新 host 单元测试覆盖：

- `ep_host_lvgl_demo` 目标只在 Apple arm64 条件下出现。
- demo 源文件位于 `platforms/host/posix/demos`，不放入通用 `app/`。
- demo 调用 `ep_ui_init()`、`ep_host_ui_port_init()`、`ep_ui_process()`、`ep_sleep_ms(16)`。
- demo 使用原生 LVGL API 创建 label 和按钮。
- demo 通过 `ep_host_ui_port_should_quit()` 退出主循环。
- `components/ui` 仍然不包含 SDL2 或平台原生头文件。
- macOS arm64 上可以构建 `ep_host_lvgl_demo`。

人工验收命令：

```bash
cmake -S . -B build
cmake --build build --target ep_host_lvgl_demo
./build/platforms/host/posix/ep_host_lvgl_demo
```

## 验收标准

- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 通过。
- `cmake --build build` 通过。
- macOS arm64 上生成 `build/platforms/host/posix/ep_host_lvgl_demo`。
- 运行 demo 能看到窗口，并能通过按钮或关闭窗口退出。
- `ep_platform_host_posix` 仍然能自动退出。
- `app/` 和 `components/ui` 不出现 SDL2 或 host demo 代码。

## 后续扩展

- 增加更多 LVGL 原生控件示例。
- 增加鼠标、键盘输入 demo。
- 增加 demo 配置，例如窗口大小、帧率、主题。
- 后续全志 Linux 和匠芯创 Luban-Lite 分别新增自己的 demo 入口，不复用 host SDL2 目标。
