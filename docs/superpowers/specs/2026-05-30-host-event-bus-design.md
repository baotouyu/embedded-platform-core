# Host event bus 设计

## 概述

本设计为 `components/event` 增加第一版平台无关事件总线。

当前工程已经完成 host POSIX 启动骨架，以及 OSAL time/mem、thread/mutex、semaphore、
queue。event bus 是进入 component 层的第一小步，用来验证“组件代码只依赖 OSAL，
不依赖平台原生接口”的工程思想，并为后续 timer、log、设备状态和应用状态机打基础。

本阶段只设计 host 可验证的最小事件能力，不适配匠芯创 Luban-Lite、RT-Thread 或真实板级
SDK。

## 目标

- 在 `components/event` 下建立平台无关事件组件。
- 暴露最小公共事件接口，供后续 core、components 和 app 使用。
- 使用全局 event bus，避免第一版引入多实例生命周期复杂度。
- 基于现有 OSAL queue/thread/mutex 实现异步事件投递和后台分发。
- 让 host 单元测试能验证注册、投递、分发和错误参数处理。
- 保持公共头文件平台无关，不暴露 `pthread.h`、RT-Thread 头文件或平台 SDK 头文件。
- 保持本 PR 范围小，不同时实现 timer、log 或真实 Luban-Lite port。

## 非目标

- 不实现多个 event loop 实例。
- 不实现取消订阅。
- 不实现事件优先级。
- 不实现动态扩容 handler 表或队列深度。
- 不实现 payload 动态内存分配。
- 不实现事件同步等待返回值。
- 不在第一版接入 `ep_framework_init()` 自动启动。
- 不引入平台原生线程、锁或消息队列接口到 `components/event`。
- 不适配匠芯创 Luban-Lite、RT-Thread 或真实硬件。

## 推荐方案

event bus 有三种可选方向：

1. 全局事件总线。
2. 可创建多个 event loop。
3. 只做同步 dispatch，不启后台线程。

本阶段选择第 1 种：全局事件总线。

选择原因：

- 当前工程还在搭组件基础，全局实例最容易测试和维护。
- 后续 timer、log、device 状态变化都可以先复用一个系统事件线程。
- 该模型容易映射到 RT-Thread 里的一个消息队列加一个事件线程。
- 相比多实例接口，第一版不需要设计 destroy、join、资源归属等复杂问题。
- 相比同步 dispatch，异步队列更接近嵌入式事件系统的真实使用方式。

## 公共接口

新增公共头文件：

```text
components/event/include/ep_event.h
```

第一版接口：

```c
#ifndef EP_EVENT_H
#define EP_EVENT_H

#include <stddef.h>

typedef int ep_event_id_t;

typedef void (*ep_event_handler_t)(
    ep_event_id_t event_id,
    const void *payload,
    size_t payload_size,
    void *user_data
);

int ep_event_init(void);
int ep_event_subscribe(ep_event_id_t event_id, ep_event_handler_t handler, void *user_data);
int ep_event_publish(ep_event_id_t event_id, const void *payload, size_t payload_size, unsigned int timeout_ms);

#endif
```

接口语义：

- `ep_event_init()` 初始化全局 event bus。
- `ep_event_subscribe()` 为一个事件 ID 注册一个 handler。
- `ep_event_publish()` 把事件复制到内部队列，由后台线程异步分发。

## 固定限制

第一版使用固定上限：

```text
最大 handler 数量：16
最大 payload 字节数：64
内部队列深度：16
```

这些限制先放在 `components/event/src/ep_event.c` 内部，不作为公共配置接口暴露。

原因：

- 当前阶段目标是验证 component 层、OSAL 依赖和事件分发模型。
- 固定上限便于 host 测试稳定覆盖。
- 后续如果真实产品需要更大容量，可以单独设计配置头或 CMake 配置项。

## 内部数据结构

公共 API 不暴露内部结构。

实现文件内部定义事件消息：

```c
struct ep_event_message {
    ep_event_id_t event_id;
    size_t payload_size;
    unsigned char payload[64];
};
```

实现文件内部定义 handler 记录：

```c
struct ep_event_subscription {
    int used;
    ep_event_id_t event_id;
    ep_event_handler_t handler;
    void *user_data;
};
```

实现文件内部保存全局状态：

```c
static ep_queue_t *g_event_queue;
static ep_thread_t *g_event_thread;
static ep_mutex_t *g_event_lock;
static struct ep_event_subscription g_subscriptions[16];
static int g_event_started;
```

`components/event` 只能包含 OSAL 公共头文件：

```text
osal/include/ep_osal_err.h
osal/include/ep_osal_mem.h
osal/include/ep_osal_mutex.h
osal/include/ep_osal_queue.h
osal/include/ep_osal_thread.h
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

`ep_event_init()` 行为：

- 第一次调用时创建 mutex、queue 和后台线程。
- queue item 大小为 `sizeof(struct ep_event_message)`。
- queue depth 为 16。
- 后台线程入口为 event dispatch loop。
- 初始化成功后返回 `EP_OK`。
- 重复调用时直接返回 `EP_OK`，不重复创建线程和队列。
- 如果 OSAL 资源创建失败，返回对应错误；无法映射时返回 `EP_ERR_UNSUPPORTED`。

第一版不提供 `ep_event_deinit()`。

原因：

- 现有 OSAL queue/mutex/thread 还没有统一 destroy 接口。
- host 单元测试可以让进程退出回收资源。
- 后续需要长期运行资源管理时，再统一补 OSAL destroy 和 event deinit。

## 订阅行为

`ep_event_subscribe()` 行为：

- 如果 `handler == NULL`，返回 `EP_ERR_INVAL`。
- 如果 event bus 尚未初始化，返回 `EP_ERR_UNSUPPORTED`。
- 加锁扫描固定 handler 表。
- 找到空槽后写入 `event_id`、`handler` 和 `user_data`。
- 成功返回 `EP_OK`。
- 如果 16 个槽都已使用，返回 `EP_ERR_BUSY`。

第一版允许同一个 `event_id` 注册多个 handler。

分发时，所有 `event_id` 匹配的 handler 都会被调用，调用顺序按注册顺序。

## 投递行为

`ep_event_publish()` 行为：

- 如果 event bus 尚未初始化，返回 `EP_ERR_UNSUPPORTED`。
- 如果 `payload_size > 64`，返回 `EP_ERR_INVAL`。
- 如果 `payload_size > 0` 且 `payload == NULL`，返回 `EP_ERR_INVAL`。
- 将 `event_id`、`payload_size` 和 payload 内容复制到内部消息结构。
- 调用 `ep_queue_send()` 投递消息。
- `timeout_ms` 原样传给 `ep_queue_send()`。
- 队列满并超时时，返回 `EP_ERR_TIMEOUT`。
- 投递成功后返回 `EP_OK`。

payload 采用值复制：

- 调用方可以传栈上结构体或临时 buffer。
- handler 收到的是 event bus 内部消息副本。
- handler 不应该保存 `payload` 指针到异步上下文。

## 分发线程行为

后台线程循环执行：

1. 调用 `ep_queue_recv()` 等待下一条事件消息。
2. 收到消息后加锁读取订阅表。
3. 找到所有 `event_id` 匹配的 handler。
4. 逐个调用 handler。
5. 如果没有 handler 匹配，丢弃该事件并继续循环。

第一版 dispatch loop 不退出。

handler 调用期间的锁策略采用“复制匹配 handler 快照后释放锁再调用”：

- 分发线程先在锁内把匹配的 handler 和 `user_data` 复制到局部数组。
- 释放锁后再调用 handler。

这样可以避免 handler 内部再次订阅事件时发生死锁，也避免一个慢 handler 阻塞订阅表操作。

## 错误处理

使用现有 OSAL 错误码：

```text
EP_OK
EP_ERR_INVAL
EP_ERR_TIMEOUT
EP_ERR_BUSY
EP_ERR_UNSUPPORTED
```

映射规则：

- 参数错误返回 `EP_ERR_INVAL`。
- 未初始化返回 `EP_ERR_UNSUPPORTED`。
- handler 表满返回 `EP_ERR_BUSY`。
- queue 投递超时返回 `EP_ERR_TIMEOUT`。
- 底层 OSAL 创建失败且没有更明确错误时返回 `EP_ERR_UNSUPPORTED`。

## 构建模型

新增组件目录：

```text
components/event/include/ep_event.h
components/event/src/ep_event.c
components/event/CMakeLists.txt
```

顶层构建新增：

```text
add_subdirectory(components/event)
```

`components/event/CMakeLists.txt` 生成静态库：

```text
ep_components_event
```

该库对外暴露 `components/event/include`，并依赖 OSAL 公共头文件。

host POSIX 可执行文件链接：

```text
ep_components_event
```

这样可以证明 component 层能被 host 平台链接，同时 event 实现仍然不依赖 host 平台私有代码。

## 测试策略

新增 host 单元测试：

```text
tests/host_unit/test_host_event_bus.py
```

测试重点：

- `ep_event.h` 存在且不包含平台原生头文件。
- CMake 能编译并链接 `ep_components_event`。
- `ep_event_init()` 返回 `EP_OK`。
- 注册 handler 后 publish 事件，handler 能收到正确 `event_id`、payload 内容和
  `user_data`。
- publish 未注册事件返回 `EP_OK`，不会崩溃。
- payload 超过 64 字节返回 `EP_ERR_INVAL`。
- handler 表超过 16 个订阅返回 `EP_ERR_BUSY`。

测试方式：

- Python 测试生成一个小型 C 测试程序。
- C 测试程序链接 event 组件、core/app 所需对象和 host POSIX OSAL 实现。
- 使用条件等待或短轮询等待异步 handler 完成，不使用固定长 sleep 作为唯一判定。

## 后续扩展

本设计完成后，下一步可以按小 PR 继续：

1. 实现 Host event bus。
2. 将 `ep_framework_init()` 接入 `ep_event_init()`。
3. 基于 event bus 设计 timer 组件。
4. 基于 event bus 设计 log 组件。
5. 在 Luban-Lite/RT-Thread 上映射 OSAL queue/thread/mutex 后复用 event 组件。

## 验收标准

- 中文设计文档提交到仓库。
- 后续实现 PR 中 event 公共接口保持平台无关。
- host 单元测试覆盖初始化、订阅、投递、未注册事件和错误参数。
- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 和 `cmake --build build` 通过。

