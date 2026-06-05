# OSAL API 参考

OSAL 是操作系统兼容层，用于隔离 POSIX、RT-Thread、Linux 用户态和后续其他系统之间的差异。应用层和公共组件只能包含 `osal/include/` 下的头文件，不直接调用 `pthread`、RT-Thread IPC 或厂商 SDK OS API。

## 通用返回值

OSAL 使用 `ep_err_e`，定义在 `osal/include/ep_osal_err.h`。

| 返回值 | 含义 |
| --- | --- |
| `EP_OK` | 成功。 |
| `EP_ERR_INVAL` | 参数非法，例如空指针、长度为 0、枚举值越界。 |
| `EP_ERR_TIMEOUT` | 等待超时。 |
| `EP_ERR_BUSY` | 资源忙、队列满、内存不足或对象数量达到上限。 |
| `EP_ERR_UNSUPPORTED` | 当前平台暂不支持该能力，或底层返回无法映射到更具体错误。 |

约定：

- 返回 `int` 的 OSAL 函数成功时返回 `EP_OK`。
- 创建类函数失败时不得留下可用句柄。
- 输出参数在失败时应保持为空或不可用状态。
- `timeout_ms == 0` 表示非阻塞尝试。
- 当前接口没有定义“无限等待”的统一常量；需要无限等待的接口应在后续扩展时显式补常量。

## 句柄和生命周期

OSAL 句柄是不透明类型：

```c
typedef struct ep_thread ep_thread_t;
typedef struct ep_mutex ep_mutex_t;
typedef struct ep_sem ep_sem_t;
typedef struct ep_queue ep_queue_t;
```

调用方不能访问结构体内部字段。当前公共 API 还没有统一的 destroy/delete 函数，长生命周期对象应优先在启动阶段创建并复用。后续如果需要动态创建和释放，应先补对应销毁接口并更新本文档。

## 内存

### `void *ep_malloc(size_t size)`

申请一块平台内存。

| 参数 | 含义 |
| --- | --- |
| `size` | 申请字节数。 |

返回值：

- 成功返回可写内存地址。
- 失败返回 `NULL`。

当前 RT-Thread 映射：

```text
ep_malloc -> rt_malloc
```

注意：

- `size == 0` 的行为由底层平台决定，业务代码不应依赖它。
- 返回内存由 `ep_free()` 释放。

### `void ep_free(void *ptr)`

释放 `ep_malloc()` 申请的内存。

| 参数 | 含义 |
| --- | --- |
| `ptr` | 待释放指针。 |

当前 RT-Thread 映射：

```text
ep_free -> rt_free
```

注意：

- 只能释放 OSAL 分配的内存。
- 不要重复释放同一指针。

## 时间

### `uint64_t ep_time_now_ms(void)`

返回系统启动后的毫秒计数。

返回值：

- 当前单调时间，单位毫秒。

当前 RT-Thread 映射：

```text
ep_time_now_ms -> rt_tick_get_millisecond
```

注意：

- 该时间用于超时、定时器和耗时统计。
- 不表示真实日历时间。
- 真实 RTC 时间后续应通过单独 RTC API 或设备兼容层提供。

### `void ep_sleep_ms(unsigned int timeout_ms)`

让当前线程休眠指定毫秒数。

| 参数 | 含义 |
| --- | --- |
| `timeout_ms` | 休眠时间，单位毫秒。 |

当前 RT-Thread 映射：

```text
ep_sleep_ms -> rt_thread_mdelay
```

注意：

- 休眠精度受系统 tick 和调度影响。
- 不应在中断上下文调用。

## 线程

### `typedef void *(*ep_thread_entry_t)(void *arg)`

线程入口函数类型。

| 参数 | 含义 |
| --- | --- |
| `arg` | 创建线程时传入的用户参数。 |

返回值：

- 当前 RT-Thread port 会忽略线程入口返回值。

### `int ep_thread_create(ep_thread_t **thread, const char *name, ep_thread_entry_t entry, void *arg)`

创建并启动线程。

| 参数 | 含义 |
| --- | --- |
| `thread` | 输出线程句柄。成功后 `*thread` 指向新线程对象。 |
| `name` | 线程名。可为 `NULL`，平台实现会使用默认名。 |
| `entry` | 线程入口函数，不能为 `NULL`。 |
| `arg` | 传给线程入口的用户参数。 |

返回值：

- `EP_OK`：线程已创建并启动。
- `EP_ERR_INVAL`：`thread` 或 `entry` 为空。
- `EP_ERR_BUSY`：内存不足或底层线程创建失败。
- `EP_ERR_UNSUPPORTED`：底层线程启动失败且无法映射为其他错误。

当前 RT-Thread 映射：

```text
rt_thread_create(name, trampoline, arg, stack_size=4096, priority=20, tick=10)
rt_thread_startup()
```

当前限制：

- 栈大小、优先级和时间片暂时固定在实现中。
- 没有线程销毁接口。
- 线程入口返回值不会向调用方传播。

### `int ep_thread_join(ep_thread_t *thread)`

等待线程结束。

| 参数 | 含义 |
| --- | --- |
| `thread` | 线程句柄。 |

返回值：

- `EP_ERR_INVAL`：`thread` 为空。
- `EP_ERR_UNSUPPORTED`：当前 RT-Thread port 暂不支持 join。

使用建议：

- 当前公共组件不要依赖 RTOS 线程 join。
- 需要停止后台线程时，应设计显式 stop 标志、事件或队列消息。

## 互斥锁

### `int ep_mutex_create(ep_mutex_t **mutex)`

创建互斥锁。

| 参数 | 含义 |
| --- | --- |
| `mutex` | 输出互斥锁句柄。 |

返回值：

- `EP_OK`：创建成功。
- `EP_ERR_INVAL`：`mutex` 为空。
- `EP_ERR_BUSY`：内存不足或底层互斥锁创建失败。

当前 RT-Thread 映射：

```text
ep_mutex_create -> rt_mutex_create("epm", RT_IPC_FLAG_FIFO)
```

### `int ep_mutex_lock(ep_mutex_t *mutex)`

加锁。

| 参数 | 含义 |
| --- | --- |
| `mutex` | 互斥锁句柄。 |

返回值：

- `EP_OK`：加锁成功。
- `EP_ERR_INVAL`：`mutex` 为空。
- `EP_ERR_UNSUPPORTED`：底层加锁失败且无法映射为其他错误。

当前 RT-Thread 映射：

```text
rt_mutex_take(..., RT_WAITING_FOREVER)
```

注意：

- 当前接口没有超时参数，调用会一直等待。
- 不应在中断上下文调用。

### `int ep_mutex_unlock(ep_mutex_t *mutex)`

解锁。

| 参数 | 含义 |
| --- | --- |
| `mutex` | 互斥锁句柄。 |

返回值：

- `EP_OK`：解锁成功。
- `EP_ERR_INVAL`：`mutex` 为空。
- `EP_ERR_UNSUPPORTED`：底层解锁失败且无法映射为其他错误。

## 信号量

### `int ep_sem_create(ep_sem_t **sem, unsigned int initial_count)`

创建信号量。

| 参数 | 含义 |
| --- | --- |
| `sem` | 输出信号量句柄。 |
| `initial_count` | 初始计数。 |

预期返回值：

- `EP_OK`：创建成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：资源不足。
- `EP_ERR_UNSUPPORTED`：当前平台不支持。

当前状态：

- host POSIX 已有实现。
- RT-Thread port 已映射到 `rt_sem_create()`。

### `int ep_sem_wait(ep_sem_t *sem, unsigned int timeout_ms)`

等待信号量。

| 参数 | 含义 |
| --- | --- |
| `sem` | 信号量句柄。 |
| `timeout_ms` | 等待时间。`0` 表示非阻塞尝试。 |

预期返回值：

- `EP_OK`：获得信号量。
- `EP_ERR_TIMEOUT`：等待超时。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：当前平台不支持。

当前 RT-Thread 映射：

```text
timeout_ms == 0 -> rt_sem_take(..., RT_WAITING_NO)
timeout_ms > 0  -> rt_sem_take(..., rt_tick_from_millisecond(timeout_ms))
```

### `int ep_sem_post(ep_sem_t *sem)`

释放信号量。

| 参数 | 含义 |
| --- | --- |
| `sem` | 信号量句柄。 |

预期返回值：

- `EP_OK`：释放成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：计数达到上限或底层资源忙。
- `EP_ERR_UNSUPPORTED`：当前平台不支持。

当前 RT-Thread 映射：

```text
ep_sem_post -> rt_sem_release
```

## 队列

### `int ep_queue_create(ep_queue_t **queue, size_t item_size, size_t depth)`

创建定长消息队列。

| 参数 | 含义 |
| --- | --- |
| `queue` | 输出队列句柄。 |
| `item_size` | 单个消息大小，单位字节。必须大于 0。 |
| `depth` | 队列最多缓存的消息数量。必须大于 0。 |

返回值：

- `EP_OK`：创建成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：内存不足或底层消息队列创建失败。

当前 RT-Thread 映射：

```text
ep_queue_create -> rt_mq_create("epq", item_size, depth, RT_IPC_FLAG_FIFO)
```

### `int ep_queue_send(ep_queue_t *queue, const void *item, unsigned int timeout_ms)`

发送一条消息。

| 参数 | 含义 |
| --- | --- |
| `queue` | 队列句柄。 |
| `item` | 指向待发送消息内容的指针。函数会按 `item_size` 拷贝数据。 |
| `timeout_ms` | 队列满时的等待时间。`0` 表示非阻塞发送。 |

返回值：

- `EP_OK`：发送成功。
- `EP_ERR_INVAL`：`queue` 或 `item` 为空。
- `EP_ERR_TIMEOUT`：等待超时。
- `EP_ERR_BUSY`：队列满或资源不足。
- `EP_ERR_UNSUPPORTED`：底层错误无法映射。

当前 RT-Thread 映射：

```text
timeout_ms == 0 -> rt_mq_send
timeout_ms > 0  -> rt_mq_send_wait
```

### `int ep_queue_recv(ep_queue_t *queue, void *item, unsigned int timeout_ms)`

接收一条消息。

| 参数 | 含义 |
| --- | --- |
| `queue` | 队列句柄。 |
| `item` | 输出缓冲区，至少能容纳 `item_size` 字节。 |
| `timeout_ms` | 队列为空时的等待时间。`0` 表示非阻塞接收。 |

返回值：

- `EP_OK`：接收成功。
- `EP_ERR_INVAL`：`queue` 或 `item` 为空。
- `EP_ERR_TIMEOUT`：等待超时。
- `EP_ERR_UNSUPPORTED`：底层错误无法映射。

当前 RT-Thread 映射：

```text
timeout_ms == 0 -> rt_mq_recv(..., RT_WAITING_NO)
timeout_ms > 0  -> rt_mq_recv(..., rt_tick_from_millisecond(timeout_ms))
```

## 当前 RT-Thread OSAL 状态

| 能力 | 当前状态 | 说明 |
| --- | --- | --- |
| 内存 | 已实现 | `rt_malloc` / `rt_free`。 |
| 时间 | 已实现 | `rt_tick_get_millisecond`。 |
| sleep | 已实现 | `rt_thread_mdelay`。 |
| 线程创建 | 已实现 | 栈、优先级、时间片暂时固定。 |
| 线程 join | 未支持 | 返回 `EP_ERR_UNSUPPORTED`。 |
| mutex | 已实现 | FIFO RT-Thread mutex。 |
| queue | 已实现 | RT-Thread message queue。 |
| sem | 已实现 | RT-Thread semaphore，`rt_sem_create/take/release`。 |
