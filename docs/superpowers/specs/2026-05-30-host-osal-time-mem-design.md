# Host OSAL time/mem 设计

## 概述

本设计为 `platforms/host/posix` 增加第一组真实 OSAL 实现：时间和内存。

这一步的目标是在 macOS/Ubuntu host 上先跑通最基础的 OSAL 能力，为后续日志、
事件、定时器和组件测试提供稳定基础。它仍然是 host 验证平台的一部分，不涉及
匠芯创 Luban-Lite、RT-Thread 或任何真实板级 SDK。

## 目标

- 在 host POSIX 平台实现 `ep_osal_time.h` 中声明的时间接口。
- 在 host POSIX 平台实现 `ep_osal_mem.h` 中声明的内存接口。
- 让 `ep_platform_host_posix` 链接真实 time/mem 实现，而不是只链接 OSAL stub。
- 增加 host 单元测试，证明接口可以在 Mac 上编译、链接并运行。
- 保持公共 OSAL 头文件平台无关，不引入 POSIX 头文件。

## 非目标

- 不实现 thread、mutex、semaphore、queue。
- 不实现日志、事件、定时器组件。
- 不适配匠芯创 Luban-Lite。
- 不引入 RT-Thread 或原厂 SDK 头文件。
- 不设计复杂内存池、内存追踪或调试分配器。
- 不改变 `app/`、`core/` 的启动职责。

## 当前接口

现有公共头文件已经定义了最小接口：

```c
uint64_t ep_time_now_ms(void);
void ep_sleep_ms(unsigned int timeout_ms);

void *ep_malloc(size_t size);
void ep_free(void *ptr);
```

这些声明继续保留在：

```text
osal/include/ep_osal_time.h
osal/include/ep_osal_mem.h
```

本步骤不修改函数名、不增加参数、不改变返回类型。

## 文件结构

新增 host POSIX 实现文件：

```text
platforms/host/posix/osal_port/ep_host_osal_time.c
platforms/host/posix/osal_port/ep_host_osal_mem.c
```

更新 host POSIX 构建文件：

```text
platforms/host/posix/CMakeLists.txt
```

新增测试：

```text
tests/host_unit/test_host_osal_time_mem.py
```

## 时间实现

`ep_time_now_ms()` 使用单调时间，不使用系统墙上时间。

host POSIX 实现优先使用：

```c
clock_gettime(CLOCK_MONOTONIC, ...)
```

返回值单位是毫秒：

```text
seconds * 1000 + nanoseconds / 1000000
```

选择单调时间的原因：

- 不受系统时间手动调整影响。
- 适合计算超时、间隔、定时器。
- 与后续 RTOS tick/time 映射更接近。

`ep_sleep_ms()` 使用：

```c
nanosleep()
```

如果 `nanosleep()` 被信号中断并返回 `EINTR`，继续使用剩余时间重试。这样可以保证
sleep 行为尽量接近“至少等待指定时长”。

## 内存实现

host POSIX 实现直接映射 C 标准库：

```text
ep_malloc(size) -> malloc(size)
ep_free(ptr)    -> free(ptr)
```

本阶段不对 `size == 0` 做特殊处理，保持跟宿主 C 标准库一致。

`ep_free(NULL)` 也保持标准 C 行为：安全无操作。

## 构建模型

`ep_platform_host_posix` 需要链接新增文件：

```text
osal_port/ep_host_osal_time.c
osal_port/ep_host_osal_mem.c
```

host 平台实现文件可以包含 POSIX/C 标准库头文件，例如：

```text
errno.h
stdint.h
stdlib.h
time.h
```

公共头文件仍不能包含平台原生头文件。

## 测试策略

新增 host 单元测试覆盖以下内容：

1. `platforms/host/posix/CMakeLists.txt` 包含 time/mem 实现文件。
2. 一个小 C 程序可以包含 `ep_osal_time.h` 和 `ep_osal_mem.h`。
3. 小 C 程序可以链接 `ep_host_osal_time.c` 和 `ep_host_osal_mem.c`。
4. `ep_malloc()` 返回可写内存，`ep_free()` 可释放。
5. `ep_time_now_ms()` 多次调用不倒退。
6. `ep_sleep_ms(1)` 返回后，时间不小于 sleep 前。

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
host OSAL mutex / semaphore / thread / queue
```

匠芯创 Luban-Lite 后续会单独映射：

```text
ep_time_now_ms() -> rt_tick / rt_timer 相关接口
ep_sleep_ms()    -> rt_thread_mdelay()
ep_malloc()      -> rt_malloc()
ep_free()        -> rt_free()
```

这些 RT-Thread 映射不进入本次 host PR。

## 成功标准

- host POSIX 平台有真实 time/mem OSAL 实现文件。
- `ep_platform_host_posix` 构建时包含这些实现文件。
- host 单元测试能编译、链接并运行 time/mem 接口。
- 公共 OSAL 头文件保持平台无关。
- 本 PR 不引入 Luban-Lite、RT-Thread 或板级 SDK 依赖。
