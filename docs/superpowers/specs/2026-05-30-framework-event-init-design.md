# Framework 接入 event 初始化设计

## 概述

本设计把已经实现的 `components/event` 接入框架启动链路。

当前 `ep_framework_start()` 的顺序是：

```text
ep_platform_boot() -> ep_framework_init() -> app_main()
```

其中 `ep_framework_init()` 仍然只是返回 0。event bus 已经作为平台无关组件存在，但还需要
由 core 层统一初始化，才能让后续 timer、log、device 状态和应用状态机默认拥有事件基础。

本阶段只接入 event 初始化，不引入新的组件初始化框架。

## 目标

- 让 `ep_framework_init()` 调用 `ep_event_init()`。
- 保持初始化失败传播：如果 event 初始化失败，`ep_framework_start()` 不进入 `app_main()`。
- 让 `ep_core` 能 include `ep_event.h`。
- 保持 `components/event` 平台无关，不引入平台原生头文件。
- 增加 host 单元测试覆盖 core 到 event 的接入关系。

## 非目标

- 不实现 `ep_event_deinit()`。
- 不接入 timer、log、device 或其他组件。
- 不新增组件初始化表或注册机制。
- 不改变 `ep_event_init()` 的内部行为。
- 不改变 `ep_framework_start()` 的启动顺序。
- 不适配匠芯创 Luban-Lite、RT-Thread 或真实板级 SDK。

## 方案选择

有三种可选接入方式：

1. 在 `ep_framework_init()` 里直接调用 `ep_event_init()`。
2. 新增一个组件初始化表，例如 `ep_components_init()`，再由 core 调用。
3. 继续让应用或测试显式调用 `ep_event_init()`。

本阶段选择第 1 种：`ep_framework_init()` 直接调用 `ep_event_init()`。

选择原因：

- 改动最小，适合单独 PR。
- 当前只有 event 一个真实组件，不需要提前设计初始化表。
- 符合 core 层职责：core 负责组件初始化编排，app 不负责基础组件启动。
- `ep_framework_start()` 已经具备失败传播逻辑，不需要额外控制流。

## 代码行为

修改 `core/src/ep_framework.c`：

```c
#include "ep_framework.h"
#include "app_main.h"
#include "ep_event.h"

int ep_framework_init(void)
{
    return ep_event_init();
}
```

保持 `ep_framework_start()` 原有逻辑：

```text
ep_platform_boot() 失败 -> 直接返回错误
ep_framework_init() 失败 -> 直接返回错误
app_main() -> 只在前两步成功后调用
```

## 构建模型

`ep_core` 需要能看到 event 公共头文件。

修改 `core/CMakeLists.txt`：

```cmake
target_include_directories(ep_core
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/event/include
)
```

`ep_core` 不直接链接 `ep_components_event`，避免 core 静态库自身强行携带组件库。

最终 host 可执行文件已经链接：

```text
ep_core
ep_app
ep_components_event
```

因此 `ep_framework_init()` 引用的 `ep_event_init()` 会在最终链接阶段解析。

如果未来 RTOS/Linux demo target 也链接可执行文件并使用 `ep_core`，需要同时链接
`ep_components_event`。当前 demo RTOS 是静态库，Linux demo 可执行文件如果触发链接问题，
本实现 PR 应补上对应链接关系，而不是移除 core 对 event 的依赖。

## 错误处理

`ep_framework_init()` 不转换错误码，直接返回 `ep_event_init()` 的返回值。

原因：

- 现有框架错误模型是整数返回值。
- event 已经使用 `EP_OK`、`EP_ERR_INVAL`、`EP_ERR_BUSY`、`EP_ERR_UNSUPPORTED` 等错误码。
- 上层只需要知道 framework init 是否成功，具体错误码可原样传递。

## 测试策略

新增或更新 host 单元测试：

- `core/src/ep_framework.c` include `ep_event.h`。
- `ep_framework_init()` 调用 `ep_event_init()`。
- `core/CMakeLists.txt` 包含 `components/event/include`。
- CMake 能构建 `ep_core`、`ep_components_event` 和 host POSIX 可执行文件。
- `ep_platform_host_posix` 仍能正常运行并返回 0。

后续如果需要精确验证“event init 失败会阻止 app_main”，可以在集成测试层引入可替换 stub。
本阶段先用源码契约和 host 构建运行验证接入关系。

## 验收标准

- 中文设计和实现计划提交到仓库。
- 后续实现 PR 中 `ep_framework_init()` 调用 `ep_event_init()`。
- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 和 `cmake --build build` 通过。
- `./build/platforms/host/posix/ep_platform_host_posix` 返回 0。

