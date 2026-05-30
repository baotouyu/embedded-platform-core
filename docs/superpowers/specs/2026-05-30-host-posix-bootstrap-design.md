# Host POSIX 启动骨架设计

## 概述

本设计新增一个很小的 `Host POSIX` 平台包，让框架可以先在 macOS 和
Ubuntu 电脑上开发、构建和验证，再去适配真实 RTOS 板子。

这里的 host 平台不是产品目标平台，而是快速验证平台。它服务于 `app/`、
`core/`、公共 OSAL/HAL 契约测试，以及后续平台无关组件的本机验证。
真正的匠芯创 Luban-Lite 适配后面单独放到 `platforms/rtos/` 下面。

## 目标

- 提供一个清晰的 Mac/Ubuntu 本机验证目标。
- 保持 `app/`、`core/` 和后续 `components/` 不包含平台原生头文件。
- 让开发者可以用 CMake 在本机跑通框架启动链路。
- 给 POSIX 版 OSAL 实现和 HAL stub/mock 留出明确位置。
- 保留后续 Luban-Lite 适配路径，避免把 SDK 细节混进 host 代码。

## 非目标

- 本步骤不适配匠芯创 Luban-Lite。
- 本步骤不加入 RT-Thread、原厂 SDK 或板级代码。
- 本步骤不替换已有 RTOS/Linux demo 平台包。
- 第一个 host bootstrap 不实现完整 OSAL/HAL 行为。
- 不把 macOS 当成最终嵌入式产品平台。

## 平台角色

当前工程要区分三个环境：

```text
macOS host
  本地开发、pytest、CMake bootstrap、组件测试、POSIX 验证。

Ubuntu host
  本地开发，以及后续编译匠芯创 Luban-Lite SDK 的开发机。

ArtInChip Luban-Lite target
  真实 RTOS/RT-Thread 固件目标，后续放在 platforms/rtos/ 下适配。
```

当前计划里，Ubuntu 是开发电脑，不是板子上的目标操作系统。如果以后产品真的运行
目标 Linux 系统，应作为单独的 Linux 目标平台包处理。

## 仓库结构

新增 host 平台包：

```text
platforms/host/
├── common/
└── posix/
    ├── CMakeLists.txt
    ├── startup/
    │   └── main.c
    ├── osal_port/
    │   └── ep_host_osal_stub.c
    ├── hal_port/
    │   └── ep_host_hal_stub.c
    ├── component_port/
    │   └── ep_host_component_stub.c
    └── config/
        └── host_posix.cmake
```

第一步可以先保留 stub 文件。后续 PR 再按模块拆分并替换成真实 OSAL/HAL 实现。

## 构建模型

顶层 CMake 把 host POSIX 包作为普通构建目标加入。第一个目标命名为：

```text
ep_platform_host_posix
```

该目标链接：

```text
ep_core
ep_app
```

host 可执行程序启动路径：

```text
platforms/host/posix/startup/main.c
-> ep_framework_start()
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

第一个版本里的 `ep_platform_boot()` 只返回成功，不做平台副作用操作。

## 分层规则

Host POSIX 代码可以包含这些系统头文件：

```text
pthread.h
time.h
unistd.h
stdlib.h
stdio.h
```

这些头文件必须留在 `platforms/host/posix/` 或 host-only 测试里。

下面这些层不能包含 POSIX、Linux、RT-Thread 或原厂 SDK 头文件：

```text
app/
core/
components/
osal/include/
hal/include/
```

## 小 PR 推进顺序

host 路线按小块推进：

1. 新增 `platforms/host/posix` 启动骨架目标。
2. 增加 host OSAL time 和 memory 实现。
3. 增加 host OSAL mutex、semaphore、thread、queue 实现。
4. 增加一个能在 host 上工作的最小日志组件。
5. 基于 OSAL 增加事件和定时器组件。
6. 增加 host 侧 HAL mock 或 stub，服务本机测试。
7. 编写匠芯创 Luban-Lite 适配设计。
8. 新增 `platforms/rtos/artinchip_luban_lite` 骨架。

每个 PR 都要保持边界窄，并包含可以在 macOS 和 GitHub Actions 上运行的测试。

## 测试策略

第一个 host bootstrap PR 需要增加或更新测试，验证：

- `platforms/host/posix` 存在。
- 顶层 CMake 构建图包含 host 目标。
- CMake configure/build 可以在开发机通过。
- 生成的 host 可执行文件可以运行，并以状态码 `0` 退出。

已有验证仍然必须通过：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

后续 OSAL 实现要先补 API 契约测试和 host 单元测试，再写实现。

## Luban-Lite 边界

匠芯创 Luban-Lite 后续单独作为 RTOS 平台包适配：

```text
platforms/rtos/artinchip_luban_lite/
vendor/rtos/artinchip_luban_lite/
```

后续预期映射关系：

```text
ep_osal_thread -> rt_thread_*
ep_osal_mutex  -> rt_mutex_*
ep_osal_sem    -> rt_sem_*
ep_osal_queue  -> rt_mq_* 或 rt_mb_*
ep_osal_time   -> rt_tick / rt_timer
ep_osal_mem    -> rt_malloc / rt_free
ep_hal_gpio    -> RT-Thread PIN 设备或匠芯创 GPIO driver
ep_hal_uart    -> RT-Thread serial device
ep_hal_i2c     -> RT-Thread I2C device
ep_hal_spi     -> RT-Thread SPI device
```

Host POSIX 代码不能包含 Luban-Lite SDK 头文件。

## 成功标准

- 开发者可以在 macOS 上构建并运行明确命名的 host POSIX 可执行文件。
- host 包的位置和 RTOS、目标 Linux 包清楚分离。
- 公共框架层保持平台无关。
- 后续 OSAL 和组件 PR 有稳定的 host 目标用于快速反馈。
- 后续 Luban-Lite 适配路径明确且隔离。
