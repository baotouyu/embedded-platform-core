# Host OSAL queue 设计

## 概述

本设计为 `platforms/host/posix` 增加第四组真实 OSAL 实现：队列。

当前 host POSIX 平台已经完成启动骨架、time/mem、thread/mutex/semaphore。queue 是
OSAL 并发基础里的最后一块核心能力，用于在线程之间传递固定大小消息，为后续 event、
timer、log 和组件测试提供基础。

本设计仍然只面向 host 验证平台，不涉及匠芯创 Luban-Lite、RT-Thread 或真实板级
SDK。

## 目标

- 在 host POSIX 平台实现 `ep_osal_queue.h` 中声明的队列接口。
- 让 `ep_platform_host_posix` 链接真实 queue 实现文件。
- 支持固定大小 item 的 FIFO 发送和接收。
- 支持队列满时发送等待、队列空时接收等待。
- 支持 `timeout_ms == 0` 的立即返回语义。
- 增加 host 单元测试，证明 queue 可以编译、链接、运行，并能跨线程传递数据。
- 保持公共 OSAL 头文件平台无关，不暴露 `pthread.h`。

## 非目标

- 不修改 `ep_osal_queue.h` 的公共函数签名。
- 不新增 queue destroy/free 公共接口。
- 不支持变长消息。
- 不支持消息优先级。
- 不实现中断上下文语义。
- 不实现严格实时调度、公平唤醒或优先级继承。
- 不适配匠芯创 Luban-Lite 或 RT-Thread。
- 不引入真实板级 SDK 或 vendor 依赖。

## 当前接口

现有公共头文件已经定义了最小接口：

```c
int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth);
int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms);
int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms);
```

这些声明继续保留在：

```text
osal/include/ep_osal_queue.h
osal/include/ep_osal_types.h
osal/include/ep_osal_err.h
```

本步骤不修改函数名、不增加参数、不改变返回类型。

## 文件结构

新增 host POSIX 实现文件：

```text
platforms/host/posix/osal_port/ep_host_osal_queue.c
```

更新 host POSIX 构建文件：

```text
platforms/host/posix/CMakeLists.txt
```

新增测试：

```text
tests/host_unit/test_host_osal_queue.py
```

## 实现方案选择

队列在 host POSIX 下有三种可选实现：

1. 使用 `pthread_mutex_t` 加两个 `pthread_cond_t` 自己实现环形缓冲区。
2. 使用 semaphore 加 mutex 拼出生产者/消费者队列。
3. 直接使用 Linux/POSIX 消息队列，例如 `mq_*`。

本阶段选择第 1 种：`pthread_mutex_t` 加两个 `pthread_cond_t`。

选择原因：

- Mac/Ubuntu 都稳定支持 pthread mutex/cond。
- 不依赖 Linux-only 消息队列接口，host 测试更容易跨平台。
- 队列内部需要同时等待“非空”和“非满”，两个条件变量表达更直接。
- 不依赖当前 semaphore 的公共 destroy 缺口，queue 内部资源生命周期更清晰。
- 该结构和后续 RT-Thread `rt_mq_*` 的 FIFO 消息语义更容易对照。

## 句柄结构

公共类型仍然保持 opaque handle：

```c
typedef struct ep_queue ep_queue_t;
```

host 实现文件内部定义真实结构：

```c
struct ep_queue {
    pthread_mutex_t lock;
    pthread_cond_t not_empty;
    pthread_cond_t not_full;
    unsigned char *buffer;
    size_t item_size;
    size_t depth;
    size_t head;
    size_t tail;
    size_t count;
};
```

字段含义：

- `buffer` 保存连续的 `depth * item_size` 字节。
- `head` 指向下一次接收读取的位置。
- `tail` 指向下一次发送写入的位置。
- `count` 表示当前队列内已有 item 数量。

队列采用 FIFO 环形缓冲区。

## 创建行为

`ep_queue_create()` 行为：

- 如果 `queue == NULL`，返回 `EP_ERR_INVAL`。
- 如果 `item_size == 0` 或 `depth == 0`，返回 `EP_ERR_INVAL`。
- 检查 `depth * item_size` 是否会发生 `size_t` 溢出，溢出时返回 `EP_ERR_INVAL`。
- 使用 `ep_malloc()` 分配 `struct ep_queue`。
- 使用 `ep_malloc()` 分配消息 buffer。
- 初始化内部 `pthread_mutex_t`。
- 初始化 `not_empty` 和 `not_full` 两个条件变量。
- 将 `head/tail/count` 初始化为 0。
- 创建成功后把对象写入 `*queue`，返回 `EP_OK`。
- 任一步失败时释放已分配资源，返回 `EP_ERR_UNSUPPORTED`。

本阶段不提供公共 destroy 接口。测试里创建的 queue 随进程退出释放，后续如果需要长期资源管理，再单独设计 `ep_queue_destroy()`。

## 发送行为

`ep_queue_send()` 行为：

- 如果 `queue == NULL` 或 `item == NULL`，返回 `EP_ERR_INVAL`。
- 进入内部 mutex 临界区。
- 如果 `count < depth`，把 `item_size` 字节复制到 `tail` 指向的位置。
- 写入后更新 `tail = (tail + 1) % depth`，`count += 1`。
- 调用 `pthread_cond_signal(&not_empty)` 唤醒一个接收等待者。
- 返回 `EP_OK`。
- 如果队列已满且 `timeout_ms == 0`，立即返回 `EP_ERR_TIMEOUT`。
- 如果队列已满且 `timeout_ms > 0`，等待 `not_full`，直到有空间或超时。
- 等待期间必须用循环重新检查 `count < depth`，避免虚假唤醒。
- 等待到期仍无空间，返回 `EP_ERR_TIMEOUT`。

## 接收行为

`ep_queue_recv()` 行为：

- 如果 `queue == NULL` 或 `item == NULL`，返回 `EP_ERR_INVAL`。
- 进入内部 mutex 临界区。
- 如果 `count > 0`，从 `head` 指向的位置复制 `item_size` 字节到 `item`。
- 读取后更新 `head = (head + 1) % depth`，`count -= 1`。
- 调用 `pthread_cond_signal(&not_full)` 唤醒一个发送等待者。
- 返回 `EP_OK`。
- 如果队列为空且 `timeout_ms == 0`，立即返回 `EP_ERR_TIMEOUT`。
- 如果队列为空且 `timeout_ms > 0`，等待 `not_empty`，直到有数据或超时。
- 等待期间必须用循环重新检查 `count > 0`，避免虚假唤醒。
- 等待到期仍无数据，返回 `EP_ERR_TIMEOUT`。

## 超时模型

`ep_queue_send()` 和 `ep_queue_recv()` 的 `timeout_ms` 都解释为“最多等待多少毫秒”。

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

## 内存与复制规则

queue 存储固定大小 item。

发送时：

```text
memcpy(queue_slot, item, item_size)
```

接收时：

```text
memcpy(item, queue_slot, item_size)
```

因此：

- 调用方可以发送栈上结构体，queue 会复制一份数据。
- 接收方必须提供至少 `item_size` 字节的输出空间。
- queue 不保存调用方传入指针本身，除非调用方把指针作为 item 内容发送。

## 构建模型

`ep_platform_host_posix` 需要新增源文件：

```text
osal_port/ep_host_osal_queue.c
```

host 平台实现文件可以包含：

```text
pthread.h
errno.h
stddef.h
string.h
sys/time.h
time.h
```

公共头文件仍不能包含这些平台原生头文件。

## 测试策略

新增 host 单元测试覆盖以下内容：

1. `platforms/host/posix/CMakeLists.txt` 包含 queue 实现文件。
2. 一个小 C 程序可以包含 `ep_osal_queue.h`。
3. 小 C 程序可以链接 host queue/time/mem/thread 实现。
4. `ep_queue_create(NULL, ...)` 返回非成功值。
5. `item_size == 0` 或 `depth == 0` 返回非成功值。
6. 空队列 `ep_queue_recv(..., 0)` 返回 `EP_ERR_TIMEOUT`。
7. 正常 send 后 recv 能得到相同结构体内容。
8. 队列满后 `ep_queue_send(..., 0)` 返回 `EP_ERR_TIMEOUT`。
9. 子线程延迟 send，主线程 `recv(timeout)` 可以被唤醒并成功拿到数据。
10. 子线程延迟 recv，主线程在满队列上 `send(timeout)` 可以被唤醒并成功写入。
11. `ep_queue_send(NULL, ...)`、`ep_queue_send(queue, NULL, ...)`、`ep_queue_recv(NULL, ...)`、`ep_queue_recv(queue, NULL, ...)` 返回非成功值。

已有验证仍然需要通过：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
```

## 后续边界

本步骤完成后，host OSAL 的基础能力将覆盖：

```text
time / mem / thread / mutex / semaphore / queue
```

后续可以开始设计组件层能力，例如：

```text
event / timer / log
```

匠芯创 Luban-Lite 后续会单独映射：

```text
ep_queue_create() -> rt_mq_create()
ep_queue_send()   -> rt_mq_send() 或 rt_mq_send_wait()
ep_queue_recv()   -> rt_mq_recv()
```

RT-Thread 的等待时间单位、队列对象释放策略、固定消息大小限制和错误码映射需要单独设计，不进入本次 host PR。

## 成功标准

- host POSIX 平台有真实 queue OSAL 实现文件。
- `ep_platform_host_posix` 构建时包含该实现文件。
- host 单元测试能编译、链接并运行 queue 接口。
- `ep_queue_send()` 和 `ep_queue_recv()` 覆盖立即成功、立即超时、定时等待和跨线程唤醒。
- 公共 OSAL 头文件保持平台无关。
- 本 PR 不引入 event、timer、log、Luban-Lite、RT-Thread 或板级 SDK 依赖。
