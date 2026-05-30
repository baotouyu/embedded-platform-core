# Host OSAL thread/mutex 设计

## 概述

本设计为 `platforms/host/posix` 增加第二组真实 OSAL 实现：线程和互斥锁。

前一阶段已经完成 host POSIX 启动骨架以及 time/mem 实现。本阶段继续在 Mac/Ubuntu
host 上补齐最基础的并发能力，为后续日志、事件、定时器、队列和组件测试打基础。

本设计仍然只面向 host 验证平台，不涉及匠芯创 Luban-Lite、RT-Thread 或真实板级
SDK。

## 目标

- 在 host POSIX 平台实现 `ep_osal_thread.h` 中声明的线程接口。
- 在 host POSIX 平台实现 `ep_osal_mutex.h` 中声明的互斥锁接口。
- 让 `ep_platform_host_posix` 链接真实 thread/mutex 实现文件。
- 增加 host 单元测试，证明线程可以启动、共享状态可以用 mutex 保护。
- 保持公共 OSAL 头文件平台无关，不暴露 `pthread.h`。

## 非目标

- 不实现 semaphore。
- 不实现 queue。
- 不实现线程优先级、栈大小、CPU 亲和性或真实系统线程命名。
- 不新增 destroy/free 公共接口。
- 不适配匠芯创 Luban-Lite 或 RT-Thread。
- 不修改 `app/`、`core/` 的启动职责。

## 当前接口

现有公共头文件已经定义了最小接口：

```c
typedef void *(*ep_thread_entry_t)(void *arg);

int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg);
int ep_thread_join(ep_thread_t *thread);

int ep_mutex_create(ep_mutex_t **mutex);
int ep_mutex_lock(ep_mutex_t *mutex);
int ep_mutex_unlock(ep_mutex_t *mutex);
```

这些声明继续保留在：

```text
osal/include/ep_osal_thread.h
osal/include/ep_osal_mutex.h
osal/include/ep_osal_types.h
```

本步骤不修改函数名、不增加参数、不改变返回类型。

## 文件结构

新增 host POSIX 实现文件：

```text
platforms/host/posix/osal_port/ep_host_osal_thread.c
platforms/host/posix/osal_port/ep_host_osal_mutex.c
```

更新 host POSIX 构建文件：

```text
platforms/host/posix/CMakeLists.txt
```

新增测试：

```text
tests/host_unit/test_host_osal_thread_mutex.py
```

## 线程实现

host POSIX 线程映射到 `pthread`：

```text
ep_thread_create() -> pthread_create()
ep_thread_join()   -> pthread_join()
```

由于公共类型是 opaque handle：

```c
typedef struct ep_thread ep_thread_t;
```

host 实现文件内部定义真实结构：

```c
struct ep_thread {
    pthread_t handle;
};
```

`ep_thread_create()` 行为：

- 如果 `thread == NULL` 或 `entry == NULL`，返回 `EP_ERR_INVAL`。
- 使用 `ep_malloc()` 分配 `struct ep_thread`。
- 调用 `pthread_create()` 启动线程。
- 创建成功后把对象写入 `*thread`，返回 `EP_OK`。
- 创建失败时释放已分配内存，返回 `EP_ERR_UNSUPPORTED` 或 `EP_ERR_BUSY`。
- `name` 参数第一阶段只接收但不映射到系统线程名，避免 macOS/Linux 命名差异扩大范围。

`ep_thread_join()` 行为：

- 如果 `thread == NULL`，返回 `EP_ERR_INVAL`。
- 调用 `pthread_join()` 等待线程结束。
- join 成功后释放 `ep_thread_t` 对象。
- join 成功返回 `EP_OK`，失败返回 `EP_ERR_INVAL`。

## 互斥锁实现

host POSIX mutex 映射到 `pthread_mutex_t`：

```text
ep_mutex_create() -> pthread_mutex_init()
ep_mutex_lock()   -> pthread_mutex_lock()
ep_mutex_unlock() -> pthread_mutex_unlock()
```

host 实现文件内部定义真实结构：

```c
struct ep_mutex {
    pthread_mutex_t handle;
};
```

`ep_mutex_create()` 行为：

- 如果 `mutex == NULL`，返回 `EP_ERR_INVAL`。
- 使用 `ep_malloc()` 分配 `struct ep_mutex`。
- 调用 `pthread_mutex_init()` 初始化。
- 初始化成功后写入 `*mutex`，返回 `EP_OK`。
- 初始化失败时释放已分配内存，返回 `EP_ERR_UNSUPPORTED`。

`ep_mutex_lock()` 和 `ep_mutex_unlock()` 行为：

- 如果入参为 `NULL`，返回 `EP_ERR_INVAL`。
- `pthread_mutex_lock()` / `pthread_mutex_unlock()` 成功返回 `EP_OK`。
- 失败返回 `EP_ERR_BUSY` 或 `EP_ERR_INVAL`。

本阶段不提供公共 destroy 接口。测试里创建的 mutex 可以随进程退出释放，后续如果需要长期资源管理，再单独设计 `ep_mutex_destroy()`。

## 内存依赖

thread/mutex 实现需要分配 opaque handle，因此依赖上一阶段已实现的：

```text
ep_malloc()
ep_free()
```

host POSIX target 已经链接 time/mem 实现，本阶段继续在同一 target 内链接 thread/mutex
实现。

## 构建模型

`ep_platform_host_posix` 需要新增源文件：

```text
osal_port/ep_host_osal_thread.c
osal_port/ep_host_osal_mutex.c
```

host 平台实现文件可以包含：

```text
pthread.h
stdlib.h
```

公共头文件仍不能包含 `pthread.h`。

## 测试策略

新增 host 单元测试覆盖以下内容：

1. `platforms/host/posix/CMakeLists.txt` 包含 thread/mutex 实现文件。
2. 一个小 C 程序可以包含 `ep_osal_thread.h` 和 `ep_osal_mutex.h`。
3. 小 C 程序可以链接 host thread/mutex/time/mem 实现。
4. 创建 mutex 后可以 lock/unlock。
5. 创建线程后可以 join。
6. 线程中通过 mutex 修改共享计数，主线程 join 后能看到结果。
7. `NULL` 入参返回非成功值。

已有验证仍然需要通过：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
```

## 后续边界

本步骤完成后，下一个小块可以继续做：

```text
host OSAL semaphore
```

再之后做：

```text
host OSAL queue
```

匠芯创 Luban-Lite 后续会单独映射：

```text
ep_thread_create() -> rt_thread_create() / rt_thread_startup()
ep_thread_join()   -> 根据 RT-Thread 能力设计等价等待或限制
ep_mutex_create()  -> rt_mutex_create()
ep_mutex_lock()    -> rt_mutex_take()
ep_mutex_unlock()  -> rt_mutex_release()
```

这些 RT-Thread 映射不进入本次 host PR。

## 成功标准

- host POSIX 平台有真实 thread/mutex OSAL 实现文件。
- `ep_platform_host_posix` 构建时包含这些实现文件。
- host 单元测试能编译、链接并运行 thread/mutex 接口。
- 公共 OSAL 头文件保持平台无关。
- 本 PR 不引入 semaphore、queue、Luban-Lite、RT-Thread 或板级 SDK 依赖。
