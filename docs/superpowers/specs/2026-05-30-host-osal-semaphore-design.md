# Host OSAL semaphore 设计

## 概述

本设计为 `platforms/host/posix` 增加第三组真实 OSAL 实现：信号量。

当前 host POSIX 平台已经完成启动骨架、time/mem、thread/mutex。本阶段继续补齐
`ep_osal_sem.h` 中声明的最小信号量能力，让 Mac/Ubuntu host 可以验证等待、超时和
跨线程唤醒行为，为后续 queue、event、timer 等组件打基础。

本设计仍然只面向 host 验证平台，不涉及匠芯创 Luban-Lite、RT-Thread 或真实板级
SDK。

## 目标

- 在 host POSIX 平台实现 `ep_osal_sem.h` 中声明的信号量接口。
- 让 `ep_platform_host_posix` 链接真实 semaphore 实现文件。
- 增加 host 单元测试，证明信号量可以立即获取、超时等待和跨线程唤醒。
- 保持公共 OSAL 头文件平台无关，不暴露 `pthread.h` 或 POSIX semaphore 头文件。
- 保持 Mac 和 Ubuntu 都能走同一套 host 测试。

## 非目标

- 不实现 queue。
- 不实现 semaphore destroy/free 公共接口。
- 不修改 thread/mutex/time/mem 公共接口。
- 不实现中断上下文语义。
- 不实现优先级继承、公平调度或严格实时语义。
- 不适配匠芯创 Luban-Lite 或 RT-Thread。
- 不引入真实板级 SDK 或 vendor 依赖。

## 当前接口

现有公共头文件已经定义了最小接口：

```c
int ep_sem_create(ep_sem_t **sem, unsigned int initial_count);
int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms);
int ep_sem_post(ep_sem_t *sem);
```

这些声明继续保留在：

```text
osal/include/ep_osal_sem.h
osal/include/ep_osal_types.h
osal/include/ep_osal_err.h
```

本步骤不修改函数名、不增加参数、不改变返回类型。

## 文件结构

新增 host POSIX 实现文件：

```text
platforms/host/posix/osal_port/ep_host_osal_sem.c
```

更新 host POSIX 构建文件：

```text
platforms/host/posix/CMakeLists.txt
```

新增测试：

```text
tests/host_unit/test_host_osal_semaphore.py
```

## 实现方案选择

信号量在 host POSIX 下有三种可选实现：

1. 使用 POSIX `sem_t`
2. 使用 `pthread_mutex_t` 加 `pthread_cond_t`
3. 先只写 RT-Thread 映射文档，不做 host 实现

本阶段选择第 2 种：`pthread_mutex_t` 加 `pthread_cond_t`。

选择原因：

- macOS 对 unnamed POSIX semaphore 的支持不如 Linux 稳定，`sem_init()` 在一些环境下不可用。
- `pthread_mutex_t` 和 `pthread_cond_t` 在 macOS/Ubuntu 上都稳定可用。
- 后续 queue 也会需要 mutex/cond 这一类等待唤醒模型，先建立模式有利于复用设计经验。
- 当前目标是先把 host 验证平台跑稳，不急着贴近某一个 RTOS 的原生实现。

## 句柄结构

公共类型仍然保持 opaque handle：

```c
typedef struct ep_sem ep_sem_t;
```

host 实现文件内部定义真实结构：

```c
struct ep_sem {
    pthread_mutex_t lock;
    pthread_cond_t cond;
    unsigned int count;
};
```

`count` 表示当前可获取的信号量数量。

## 创建行为

`ep_sem_create()` 行为：

- 如果 `sem == NULL`，返回 `EP_ERR_INVAL`。
- 使用 `ep_malloc()` 分配 `struct ep_sem`。
- 初始化内部 `pthread_mutex_t`。
- 初始化内部 `pthread_cond_t`。
- 将 `count` 设置为 `initial_count`。
- 创建成功后把对象写入 `*sem`，返回 `EP_OK`。
- 任一步失败时释放已分配资源，返回 `EP_ERR_UNSUPPORTED`。

本阶段不限制 `initial_count` 的最大值。后续如果公共 API 增加最大计数参数，再单独设计。

## 等待行为

`ep_sem_wait()` 行为：

- 如果 `sem == NULL`，返回 `EP_ERR_INVAL`。
- 进入内部 mutex 临界区。
- 如果 `count > 0`，立即把 `count` 减 1 并返回 `EP_OK`。
- 如果 `count == 0` 且 `timeout_ms == 0`，立即返回 `EP_ERR_TIMEOUT`。
- 如果 `count == 0` 且 `timeout_ms > 0`，使用条件变量等待。
- 等待期间如果被 `ep_sem_post()` 唤醒并看到 `count > 0`，减 1 后返回 `EP_OK`。
- 等待到期仍然没有可用计数，返回 `EP_ERR_TIMEOUT`。
- mutex/cond 调用出现无法恢复的错误时，返回 `EP_ERR_UNSUPPORTED` 或 `EP_ERR_INVAL`。

由于条件变量允许虚假唤醒，等待逻辑必须用循环重新检查 `count`，不能把一次唤醒直接当作成功。

## 超时模型

`ep_sem_wait()` 的 `timeout_ms` 解释为“最多等待多少毫秒”。

host POSIX 实现使用绝对时间超时：

```text
当前时间 + timeout_ms -> pthread_cond_timedwait()
```

为了避免系统墙上时间被修改影响等待行为，优先让条件变量使用单调时钟：

```c
pthread_condattr_setclock(..., CLOCK_MONOTONIC)
clock_gettime(CLOCK_MONOTONIC, ...)
```

macOS 不支持 `pthread_condattr_setclock()` 时，host 实现可以退回到默认条件变量时钟，并使用
`gettimeofday()` 或兼容方式计算绝对超时时间。这个兼容分支只允许留在
`platforms/host/posix` 内部，不能污染公共 OSAL 头文件。

## 释放行为

`ep_sem_post()` 行为：

- 如果 `sem == NULL`，返回 `EP_ERR_INVAL`。
- 进入内部 mutex 临界区。
- 将 `count` 加 1。
- 调用 `pthread_cond_signal()` 唤醒一个等待者。
- 成功返回 `EP_OK`。
- mutex/cond 调用失败时返回 `EP_ERR_UNSUPPORTED` 或 `EP_ERR_INVAL`。

本阶段不处理 `count` 溢出保护。后续如需上限，应扩展公共 API 或增加内部最大值设计。

## 内存依赖

semaphore 实现需要分配 opaque handle，因此依赖已实现的：

```text
ep_malloc()
ep_free()
```

host POSIX target 已经链接 time/mem/thread/mutex 实现，本阶段继续在同一 target 内链接
semaphore 实现。

## 构建模型

`ep_platform_host_posix` 需要新增源文件：

```text
osal_port/ep_host_osal_sem.c
```

host 平台实现文件可以包含：

```text
pthread.h
errno.h
time.h
sys/time.h
```

公共头文件仍不能包含这些平台原生头文件。

## 测试策略

新增 host 单元测试覆盖以下内容：

1. `platforms/host/posix/CMakeLists.txt` 包含 semaphore 实现文件。
2. 一个小 C 程序可以包含 `ep_osal_sem.h`。
3. 小 C 程序可以链接 host semaphore/time/mem/thread 实现。
4. `ep_sem_create(NULL, ...)` 返回非成功值。
5. 初始计数为 1 时，第一次 `ep_sem_wait(..., 0)` 立即成功。
6. 计数耗尽后，`ep_sem_wait(..., 0)` 立即返回超时。
7. 计数耗尽后，短超时等待返回 `EP_ERR_TIMEOUT`。
8. 子线程延迟后调用 `ep_sem_post()`，主线程 `ep_sem_wait()` 可以被唤醒并成功返回。
9. `ep_sem_wait(NULL, ...)` 和 `ep_sem_post(NULL)` 返回非成功值。

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
host OSAL queue
```

匠芯创 Luban-Lite 后续会单独映射：

```text
ep_sem_create() -> rt_sem_create()
ep_sem_wait()   -> rt_sem_take()
ep_sem_post()   -> rt_sem_release()
```

RT-Thread 的等待时间单位、永久等待语义、对象释放策略和错误码映射需要单独设计，不进入本次
host PR。

## 成功标准

- host POSIX 平台有真实 semaphore OSAL 实现文件。
- `ep_platform_host_posix` 构建时包含该实现文件。
- host 单元测试能编译、链接并运行 semaphore 接口。
- `ep_sem_wait()` 覆盖立即成功、立即超时、定时超时和跨线程唤醒。
- 公共 OSAL 头文件保持平台无关。
- 本 PR 不引入 queue、Luban-Lite、RT-Thread 或板级 SDK 依赖。
