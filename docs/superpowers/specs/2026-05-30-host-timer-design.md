# Host timer 设计

## 概述

本设计为 `components/timer` 增加第一版平台无关定时器组件。

当前工程已经完成 host POSIX 启动骨架、OSAL time/mem、thread/mutex、semaphore、
queue，以及 `components/event` 事件总线。timer 是 event 之后的下一块基础组件，用来验证
“组件代码只依赖 OSAL 和其他平台无关组件”的工程思想，并为后续设备状态超时、应用状态机
延迟动作、周期性任务设计打基础。

本阶段只设计 host 可验证的最小定时器能力，不适配匠芯创 Luban-Lite、RT-Thread 或真实板级
SDK。

## 目标

- 在 `components/timer` 下建立平台无关 timer 组件。
- 暴露最小公共 timer 接口，供后续 core、components 和 app 使用。
- 使用全局 timer service，避免第一版引入多实例生命周期复杂度。
- 基于现有 OSAL time/thread/mutex 和 event bus 实现一次性定时器。
- 定时器到期后通过 `ep_event_publish()` 投递事件，不直接调用业务回调。
- 让 host 单元测试能验证初始化、启动、停止、到期事件和错误参数处理。
- 保持公共头文件平台无关，不暴露 `pthread.h`、RT-Thread 头文件或平台 SDK 头文件。
- 保持本 PR 范围小，不同时实现周期定时器、deinit、真实 Luban-Lite port 或 framework 自动初始化。

## 非目标

- 不实现周期定时器。
- 不实现多个 timer service 实例。
- 不实现定时器 destroy/deinit。
- 不实现动态分配 timer entry。
- 不实现高精度实时调度保证。
- 不在第一版接入 `ep_framework_init()` 自动启动。
- 不引入平台原生线程、锁、sleep 或 tick 接口到 `components/timer`。
- 不适配匠芯创 Luban-Lite、RT-Thread 或真实硬件。

## 推荐方案

timer 有三种可选方向：

1. 全局一次性 timer service，到期后投递 event。
2. 每个 timer 单独创建线程或平台原生 timer。
3. 先只做同步 `sleep` 封装，不做后台 timer service。

本阶段选择第 1 种：全局一次性 timer service。

选择原因：

- 当前工程已经有 event bus，timer 到期投递 event 能自然接到后续状态机。
- 全局实例最容易控制资源边界，也最容易映射到 RT-Thread 的一个 timer 管理任务。
- 一次性 timer 足够覆盖设备超时、延迟启动、状态切换等第一批场景。
- 相比每个 timer 一个线程，全局扫描线程资源更稳定。
- 相比同步 `sleep`，后台 timer service 不会阻塞调用方。

## 公共接口

新增公共头文件：

```text
components/timer/include/ep_timer.h
```

第一版接口：

```c
#ifndef EP_TIMER_H
#define EP_TIMER_H

#include "ep_event.h"

typedef int ep_timer_id_t;

int ep_timer_init(void);
int ep_timer_start(ep_timer_id_t timer_id, unsigned int timeout_ms, ep_event_id_t event_id);
int ep_timer_stop(ep_timer_id_t timer_id);

#endif
```

接口语义：

- `ep_timer_init()` 初始化全局 timer service。
- `ep_timer_start()` 启动或重启一个一次性 timer。
- `ep_timer_stop()` 停止一个尚未到期的 timer。

## 固定限制

第一版使用固定上限：

```text
最大 timer 数量：16
扫描周期：10ms
```

这些限制先放在 `components/timer/src/ep_timer.c` 内部，不作为公共配置接口暴露。

原因：

- 当前阶段目标是验证 timer 组件边界、OSAL 依赖和 event 投递模型。
- 固定上限便于 host 测试稳定覆盖。
- 10ms 扫描周期足够用于工程骨架验证，且不会在 host 测试里制造明显负担。
- 后续如果真实产品需要更高精度或更大容量，可以单独设计配置头或 CMake 配置项。

## 内部数据结构

公共 API 不暴露内部结构。

实现文件内部定义 timer entry：

```c
struct ep_timer_entry {
    int active;
    ep_timer_id_t timer_id;
    ep_event_id_t event_id;
    uint64_t deadline_ms;
};
```

实现文件内部保存全局状态：

```c
static ep_thread_t *g_timer_thread;
static ep_mutex_t *g_timer_lock;
static struct ep_timer_entry g_timers[16];
static int g_timer_started;
```

`components/timer` 只能包含平台无关公共头文件：

```text
components/event/include/ep_event.h
osal/include/ep_osal_err.h
osal/include/ep_osal_mutex.h
osal/include/ep_osal_thread.h
osal/include/ep_osal_time.h
```

不得包含：

```text
pthread.h
rtthread.h
unistd.h
sys/*
platforms/*
```

## 初始化行为

`ep_timer_init()` 行为：

- 第一次调用时先调用 `ep_event_init()`，确保 timer 到期事件有可用 event bus。
- 创建 timer mutex。
- 创建 timer 后台扫描线程。
- 初始化成功后返回 `EP_OK`。
- 重复调用时直接返回 `EP_OK`，不重复创建线程和锁。
- 如果 event 或 OSAL 资源创建失败，返回对应错误；无法映射时返回 `EP_ERR_UNSUPPORTED`。

第一版不提供 `ep_timer_deinit()`。

原因：

- 现有 OSAL thread/mutex 还没有统一 destroy 接口。
- host 单元测试可以让进程退出回收资源。
- 后续需要长期运行资源管理时，再统一补 OSAL destroy 和 timer deinit。

## 启动行为

`ep_timer_start()` 行为：

- 如果 timer service 尚未初始化，返回 `EP_ERR_UNSUPPORTED`。
- 如果 `timer_id < 0`，返回 `EP_ERR_INVAL`。
- `timeout_ms == 0` 合法，表示尽快到期，但仍由后台扫描线程异步投递事件。
- 计算 `deadline_ms = ep_time_now_ms() + timeout_ms`。
- 加锁扫描 timer 表。
- 如果找到相同 `timer_id` 的 active timer，更新它的 `deadline_ms` 和 `event_id`，等价于重启。
- 如果没有找到相同 `timer_id`，写入第一个空槽。
- 成功返回 `EP_OK`。
- 如果 16 个槽都已使用，返回 `EP_ERR_BUSY`。

第一版 timer 都是一次性 timer。到期后 entry 会自动变为 inactive。

## 停止行为

`ep_timer_stop()` 行为：

- 如果 timer service 尚未初始化，返回 `EP_ERR_UNSUPPORTED`。
- 如果 `timer_id < 0`，返回 `EP_ERR_INVAL`。
- 加锁扫描 timer 表。
- 如果找到相同 `timer_id` 的 active timer，将其置为 inactive，并返回 `EP_OK`。
- 如果没有找到 active timer，返回 `EP_ERR_INVAL`。

停止已经到期并被后台线程取走的 timer，不保证能阻止对应事件投递。调用方如果需要区分过期事件，
后续可以在业务 payload 或状态机里增加版本号。本阶段不在 timer API 中增加 generation 字段。

## 扫描线程行为

后台扫描线程循环执行：

1. 调用 `ep_sleep_ms(10)` 等待下一个扫描周期。
2. 读取 `ep_time_now_ms()`。
3. 加锁扫描 timer 表。
4. 找到所有 `active == 1` 且 `deadline_ms <= now_ms` 的 timer。
5. 把到期 timer 的 `event_id` 复制到局部数组，并把 entry 置为 inactive。
6. 释放锁。
7. 对每个到期 timer 调用 `ep_event_publish(event_id, NULL, 0, 0)`。

event publish 必须在释放 timer lock 后执行。

原因：

- 避免 timer lock 和 event bus lock 产生锁顺序问题。
- 避免 event 队列满或 event 内部行为影响 timer 表操作。
- timer 线程不直接调用业务 handler，业务 handler 仍由 event bus 分发线程执行。

如果 `ep_event_publish()` 失败，第一版 timer 线程忽略返回值并继续运行。

原因：

- 异步后台线程无法把单次投递失败直接返回给 `ep_timer_start()` 调用方。
- 当前 event queue 深度固定，失败主要代表队列满或 event bus 异常。
- 后续引入 log 组件后，可以在这里记录错误。

## 错误处理

使用现有 OSAL 错误码：

```text
EP_OK
EP_ERR_INVAL
EP_ERR_BUSY
EP_ERR_UNSUPPORTED
```

错误码约定：

- 参数非法返回 `EP_ERR_INVAL`。
- timer service 尚未初始化返回 `EP_ERR_UNSUPPORTED`。
- timer 表满返回 `EP_ERR_BUSY`。
- 资源创建失败时优先透传下层返回值。

## 构建模型

新增组件构建文件：

```text
components/timer/CMakeLists.txt
```

新增组件目标：

```text
ep_components_timer
```

顶层 `CMakeLists.txt` 增加：

```cmake
add_subdirectory(components/timer)
```

`ep_components_timer` 需要：

- public include：`components/timer/include`
- public link 依赖：`ep_components_event`
- private include：`osal/include`

`ep_timer.h` 会包含 `ep_event.h`，因此 `ep_components_event` 需要作为 public link 依赖传递给
timer 的消费者，避免业务代码 include `ep_timer.h` 时找不到 event 公共头文件。

本阶段不把 timer 接入 `ep_framework_init()`，因此现有 framework 启动流程不变化。
后续如果把 framework init 扩展为同时初始化 event 和 timer，需要单独 PR 处理 core 链接关系和 demo
target 链接关系。

## 测试策略

新增 host 单元测试覆盖以下内容：

1. `components/timer/include/ep_timer.h` 存在并能被 C 程序包含。
2. timer 公共头文件不包含平台原生头文件。
3. CMake 顶层包含 `components/timer`。
4. `ep_components_timer` 能与 host POSIX OSAL、event bus 一起编译链接。
5. `ep_timer_init()` 可重复调用并返回 `EP_OK`。
6. `ep_timer_start()` 到期后会通过 event bus 投递一次事件。
7. `ep_timer_stop()` 能阻止尚未到期的 timer 投递事件。
8. 相同 `timer_id` 再次 `start` 会重启 timer，而不是占用新槽。
9. 未初始化调用 `start/stop` 返回 `EP_ERR_UNSUPPORTED`。
10. `timer_id < 0` 返回 `EP_ERR_INVAL`。
11. 超过 16 个 active timer 返回 `EP_ERR_BUSY`。

已有验证仍然需要通过：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
```

## 后续边界

本步骤完成后，后续可以继续做：

```text
framework 接入 timer 初始化
周期 timer
timer payload 或 generation 机制
log 组件
Luban-Lite / RT-Thread OSAL 适配
```

匠芯创 Luban-Lite 后续会优先复用相同公共 API，再把底层 OSAL 映射到 RT-Thread：

```text
ep_time_now_ms() -> rt_tick / rt_timer 相关接口
ep_sleep_ms()    -> rt_thread_mdelay()
ep_thread_create -> rt_thread_create / rt_thread_startup
ep_mutex_create  -> rt_mutex_create
ep_event_publish -> 继续使用平台无关 event bus
```

这些 RT-Thread 映射不进入本次 host timer PR。

## 验收标准

- 中文设计和实现计划提交到仓库。
- 后续实现 PR 中新增 `components/timer` 组件和 `ep_timer.h` 公共 API。
- timer 组件只依赖 OSAL、event bus 和 C 标准头文件。
- host 单元测试覆盖启动、停止、到期投递、重启和错误路径。
- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 和 `cmake --build build` 通过。
- 本 PR 不引入 Luban-Lite、RT-Thread 或板级 SDK 依赖。
