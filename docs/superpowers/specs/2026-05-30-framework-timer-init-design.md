# Framework 接入 timer 初始化设计

## 概述

本设计把已经实现的 `components/timer` 接入框架启动链路。

当前 `ep_framework_start()` 的顺序是：

```text
ep_platform_boot() -> ep_framework_init() -> app_main()
```

其中 `ep_framework_init()` 已经调用 `ep_event_init()`。`components/timer` 已经作为平台无关组件存在，
但应用如果要使用 timer 仍需要手动调用 `ep_timer_init()`。下一步应由 core 层统一初始化 timer，
让后续 device、log、应用状态机和业务代码默认拥有定时器基础能力。

本阶段只接入 timer 初始化，不引入新的组件初始化框架。

## 目标

- 让 `ep_framework_init()` 按顺序调用 `ep_event_init()` 和 `ep_timer_init()`。
- 保持初始化失败传播：如果 event 或 timer 初始化失败，`ep_framework_start()` 不进入 `app_main()`。
- 让 `ep_core` 能 include `ep_timer.h`。
- 保持 `components/timer` 平台无关，不引入平台原生头文件。
- 更新 host 和 linux demo 的最终链接关系，保证引用 `ep_timer_init()` 后仍可构建。
- 增加 host 单元测试覆盖 core 到 timer 的接入关系。

## 非目标

- 不实现 `ep_timer_deinit()`。
- 不实现周期 timer。
- 不新增组件初始化表或注册机制。
- 不改变 `ep_timer_init()` 的内部行为。
- 不改变 `ep_framework_start()` 的启动顺序。
- 不接入 log、device 或其他组件。
- 不适配匠芯创 Luban-Lite、RT-Thread 或真实板级 SDK。

## 方案选择

有三种可选接入方式：

1. 在 `ep_framework_init()` 里直接顺序调用 `ep_event_init()` 和 `ep_timer_init()`。
2. 新增一个组件初始化表，例如 `ep_components_init()`，由 core 统一遍历。
3. 继续让应用或测试显式调用 `ep_timer_init()`。

本阶段选择第 1 种：`ep_framework_init()` 直接调用 timer 初始化。

选择原因：

- 改动最小，适合单独 PR。
- 当前只有 event 和 timer 两个真实组件，还不需要提前设计初始化表。
- `ep_timer_init()` 内部已经会调用 `ep_event_init()`，但 core 显式先初始化 event 能让启动顺序更清晰。
- 符合 core 层职责：core 负责编排基础组件，app 不负责基础组件启动。
- `ep_framework_start()` 已经具备失败传播逻辑，不需要额外控制流。

## 代码行为

修改 `core/src/ep_framework.c`：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_event.h"
#include "ep_timer.h"

int ep_framework_init(void)
{
    int rc = ep_event_init();
    if (rc != 0) {
        return rc;
    }

    return ep_timer_init();
}
```

保持 `ep_framework_start()` 原有逻辑：

```text
ep_platform_boot() 失败 -> 直接返回错误
ep_framework_init() 失败 -> 直接返回错误
app_main() -> 只在前两步成功后调用
```

虽然 `ep_timer_init()` 当前也会调用 `ep_event_init()`，core 仍保留显式 `ep_event_init()`：

- 保持 framework 初始化顺序清楚。
- 保持 event 初始化失败能在 timer 之前返回。
- 未来如果 timer 依赖更多组件，core 仍是依赖顺序的编排位置。

## 构建模型

`ep_core` 需要能看到 timer 公共头文件。

修改 `core/CMakeLists.txt`：

```cmake
target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
)
```

`ep_core` 不直接链接 `ep_components_timer`，避免 core 静态库自身强行携带组件库。

最终 host 可执行文件已经链接：

```text
ep_core
ep_app
ep_components_timer
```

因此 `ep_framework_init()` 引用的 `ep_timer_init()` 会在最终链接阶段解析。
`ep_components_timer` public 依赖 `ep_components_event`，所以 host 不需要重复直接链接 event。

Linux demo 当前是可执行文件，并且使用 `ep_core`。本实现 PR 需要让它链接：

```text
ep_components_timer
```

Linux demo 目前使用 `ep_linux_osal_stub.c`。因为 `ep_timer_init()` 会使用 thread、mutex、time 等 OSAL
接口，Linux demo 如果没有真实实现，需要继续在 stub 中提供对应符号并返回 `EP_ERR_UNSUPPORTED` 或
简单可链接实现，保证 demo skeleton 的链接闭环。

RTOS demo 当前是静态库，不会在本阶段触发最终链接问题。本阶段不改 RTOS demo。

## 错误处理

`ep_framework_init()` 不转换错误码，直接返回下层初始化返回值。

行为约定：

- `ep_event_init()` 失败，直接返回 event 的错误码。
- `ep_event_init()` 成功后调用 `ep_timer_init()`。
- `ep_timer_init()` 失败，返回 timer 的错误码。
- 两者都成功，返回 `EP_OK`。

原因：

- 现有 framework 错误模型是整数返回值。
- event 和 timer 已经使用 `EP_OK`、`EP_ERR_INVAL`、`EP_ERR_BUSY`、`EP_ERR_UNSUPPORTED` 等错误码。
- 上层只需要知道 framework init 是否成功，具体错误码可原样传递。

## 测试策略

新增或更新 host 单元测试：

- `core/src/ep_framework.c` include `ep_timer.h`。
- `ep_framework_init()` 调用 `ep_event_init()` 后再调用 `ep_timer_init()`。
- `core/CMakeLists.txt` 包含 `components/timer/include`。
- host POSIX 可执行文件链接 `ep_components_timer`。
- Linux demo 可执行文件链接 `ep_components_timer`。
- CMake 能构建 `ep_core`、`ep_components_timer`、host POSIX 可执行文件和 Linux demo 可执行文件。
- `ep_platform_host_posix` 仍能正常运行并返回 0。

后续如果需要精确验证“timer init 失败会阻止 app_main”，可以在集成测试层引入可替换 stub。
本阶段先用源码契约和 host 构建运行验证接入关系。

## 验收标准

- 中文设计和实现计划提交到仓库。
- 后续实现 PR 中 `ep_framework_init()` 顺序调用 `ep_event_init()` 和 `ep_timer_init()`。
- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 和 `cmake --build build` 通过。
- `./build/platforms/host/posix/ep_platform_host_posix` 返回 0。
- 本 PR 不引入 Luban-Lite、RT-Thread 或板级 SDK 依赖。
