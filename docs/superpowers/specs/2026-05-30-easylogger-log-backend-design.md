# EasyLogger 作为 ep_log 后端设计

## 概述

本设计为 `components/log` 引入第一版日志组件，并选择
[EasyLogger](https://github.com/armink/EasyLogger) 作为底层日志后端。

当前工程已经完成 host POSIX 启动、OSAL 基础接口、event、timer，以及 framework 自动初始化 timer。
下一步接入真实平台前，需要先有稳定日志能力。日志是后续适配匠芯创 Luban-Lite、RT-Thread 和真实板级
SDK 时定位启动、线程、定时器和驱动问题的基础设施。

本阶段只设计日志组件边界，不直接适配 Luban-Lite、不接 RT-Thread SDK、不启用 EasyLogger 的文件、
Flash 或异步插件。

## EasyLogger 仓库分析

EasyLogger 是一个 MIT 许可证的 C/C++ 日志库，适合资源受限的嵌入式项目。它支持 RT-Thread、
Linux、Windows、Nuttx 和裸机等环境，提供日志级别、标签、过滤、颜色、hexdump、同步输出、异步输出、
缓冲输出和插件扩展能力。

本设计只使用 EasyLogger 的核心同步输出能力：

```text
easylogger/inc/elog.h
easylogger/inc/elog_cfg.h
easylogger/src/elog.c
easylogger/src/elog_utils.c
easylogger/port/elog_port.c
```

第一版不使用：

```text
easylogger/src/elog_async.c
easylogger/src/elog_buf.c
easylogger/plugins/file
easylogger/plugins/flash
```

原因：

- 异步输出会引入额外线程、信号量或 pthread 细节，第一版会扩大适配面。
- 文件日志依赖文件系统，不适合作为所有 RTOS/裸机目标的默认能力。
- Flash 日志依赖 EasyFlash 或具体 Flash port，应该在真实板级存储策略明确后再设计。
- 当前目标是先建立 `ep_log` 公共边界和 host 可验证输出闭环。

## 目标

- 新增 `components/log`，暴露平台无关 `ep_log` 公共接口。
- 使用 EasyLogger 作为第一版日志后端，但不让上层 include `elog.h`。
- 将第三方源码放在 `third_party/external/EasyLogger` 下，保留 MIT 许可证文本。
- 为 EasyLogger 提供 host POSIX port，让日志输出到 `stdout` 或 `stderr`。
- 让 `components/log` 可以在 host 上初始化并输出一条日志。
- 为后续 Luban-Lite/RT-Thread port 预留清晰的 `elog_port_*` 适配点。
- 保持 `components/log/include/ep_log.h` 平台无关，不暴露 `pthread.h`、`unistd.h`、`rtthread.h` 或 SDK 头文件。

## 非目标

- 不让业务代码直接 include `elog.h`。
- 不把 EasyLogger API 当成工程公共 API。
- 不启用 EasyLogger 异步输出。
- 不启用 EasyLogger 文件插件。
- 不启用 EasyLogger Flash 插件。
- 不实现日志持久化。
- 不实现动态日志配置命令行。
- 不接入真实 Luban-Lite、RT-Thread 或匠芯创 SDK。
- 不改造 EasyLogger 源码风格。

## 方案选择

有三种可选方案：

1. `components/log` 包一层 `ep_log`，内部调用 EasyLogger。
2. 上层代码直接 include `elog.h` 并调用 `elog_i()`、`elog_e()` 等宏。
3. 先自研极简日志组件，不引入第三方库。

本阶段选择第 1 种：`ep_log` 包装 EasyLogger。

选择原因：

- 保持工程公共 API 稳定。以后如果换成 RT-Thread 原生日志或其他库，只改 `components/log` 和 port。
- 避免 EasyLogger 的宏、全局配置和单例状态泄漏到 app、core 和其他 components。
- EasyLogger 已经有 RT-Thread 示例，后续适配 Luban-Lite 基于 RT-Thread 的环境会更顺。
- 自研日志会重复造基础能力，不利于快速进入真实平台适配。
- 直接暴露 `elog.h` 会让上层依赖第三方接口，后续替换成本高。

## 目录设计

新增或使用以下目录：

```text
components/log/
├── include/
│   └── ep_log.h
├── src/
│   └── ep_log.c
└── CMakeLists.txt

third_party/external/EasyLogger/
├── LICENSE
└── easylogger/
    ├── inc/
    │   ├── elog.h
    │   └── elog_cfg.h
    ├── src/
    │   ├── elog.c
    │   └── elog_utils.c
    └── port/
        └── elog_port.c
```

`third_party/external/EasyLogger/easylogger/port/elog_port.c` 先实现 host POSIX 输出。后续真实平台可以拆成
平台专属 port 文件，例如：

```text
platforms/host/posix/component_port/ep_host_easylogger_port.c
platforms/rtos/luban_lite/component_port/ep_luban_easylogger_port.c
```

第一版实现时可以先选择简单路径：把 host port 放在第三方副本的 `port/elog_port.c` 中。后续接入真实
RTOS 时，再把 port 从 third_party 中移到平台包，减少第三方目录里的本地修改。

## 公共接口

新增公共头文件：

```text
components/log/include/ep_log.h
```

第一版接口：

```c
#ifndef EP_LOG_H
#define EP_LOG_H

typedef enum {
    EP_LOG_LEVEL_ASSERT = 0,
    EP_LOG_LEVEL_ERROR = 1,
    EP_LOG_LEVEL_WARN = 2,
    EP_LOG_LEVEL_INFO = 3,
    EP_LOG_LEVEL_DEBUG = 4,
    EP_LOG_LEVEL_VERBOSE = 5
} ep_log_level_e;

int ep_log_init(void);
int ep_log_write(ep_log_level_e level, const char *tag, const char *fmt, ...);

#define EP_LOGA(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ASSERT, tag, fmt, ##__VA_ARGS__)
#define EP_LOGE(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_ERROR, tag, fmt, ##__VA_ARGS__)
#define EP_LOGW(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_WARN, tag, fmt, ##__VA_ARGS__)
#define EP_LOGI(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_INFO, tag, fmt, ##__VA_ARGS__)
#define EP_LOGD(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_DEBUG, tag, fmt, ##__VA_ARGS__)
#define EP_LOGV(tag, fmt, ...) ep_log_write(EP_LOG_LEVEL_VERBOSE, tag, fmt, ##__VA_ARGS__)

#endif
```

接口语义：

- `ep_log_init()` 初始化日志后端，重复调用返回成功。
- `ep_log_write()` 按级别、tag 和格式化字符串输出日志。
- `tag == 0` 或 `fmt == 0` 返回 `EP_ERR_INVAL`。
- 未初始化时调用 `ep_log_write()` 返回 `EP_ERR_UNSUPPORTED`。
- 日志实际输出格式由 EasyLogger 配置决定，上层只依赖 `ep_log` 接口。

## EasyLogger 配置策略

第一版 `elog_cfg.h` 使用同步输出，控制范围尽量小：

```c
#define ELOG_OUTPUT_ENABLE
#define ELOG_OUTPUT_LVL ELOG_LVL_VERBOSE
#define ELOG_LINE_BUF_SIZE 256
#define ELOG_LINE_NUM_MAX_LEN 5
#define ELOG_FILTER_TAG_MAX_LEN 24
#define ELOG_FILTER_KW_MAX_LEN 16
#define ELOG_FILTER_TAG_LVL_MAX_NUM 5
#define ELOG_NEWLINE_SIGN "\n"
#define ELOG_FMT_USING_FUNC
#define ELOG_FMT_USING_DIR
#define ELOG_FMT_USING_LINE
```

第一版不定义：

```c
ELOG_ASYNC_OUTPUT_ENABLE
ELOG_BUF_OUTPUT_ENABLE
ELOG_FILE_ENABLE
ELOG_FLASH_ENABLE
```

颜色默认关闭。原因是 CI 和日志断言更稳定，后续如果 host 调试需要颜色可以单独设计配置项。

## 初始化行为

`ep_log_init()` 行为：

1. 如果已经初始化，直接返回 `EP_OK`。
2. 调用 EasyLogger 的 `elog_init()`。
3. 设置每个级别的输出格式。
4. 调用 `elog_start()`。
5. 标记 `ep_log` 已初始化。

建议第一版格式：

```c
elog_set_fmt(ELOG_LVL_ASSERT, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
elog_set_fmt(ELOG_LVL_ERROR, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
elog_set_fmt(ELOG_LVL_WARN, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
elog_set_fmt(ELOG_LVL_INFO, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
elog_set_fmt(ELOG_LVL_DEBUG, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME | ELOG_FMT_DIR | ELOG_FMT_LINE);
elog_set_fmt(ELOG_LVL_VERBOSE, ELOG_FMT_LVL | ELOG_FMT_TAG | ELOG_FMT_TIME);
```

EasyLogger 的 `ElogErrCode` 当前只有 `ELOG_NO_ERR`。如果初始化不是 `ELOG_NO_ERR`，`ep_log_init()` 返回
`EP_ERR_UNSUPPORTED`。

## 输出行为

`ep_log_write()` 把 `ep_log_level_e` 映射到 EasyLogger 级别：

```text
EP_LOG_LEVEL_ASSERT  -> ELOG_LVL_ASSERT
EP_LOG_LEVEL_ERROR   -> ELOG_LVL_ERROR
EP_LOG_LEVEL_WARN    -> ELOG_LVL_WARN
EP_LOG_LEVEL_INFO    -> ELOG_LVL_INFO
EP_LOG_LEVEL_DEBUG   -> ELOG_LVL_DEBUG
EP_LOG_LEVEL_VERBOSE -> ELOG_LVL_VERBOSE
```

因为 EasyLogger 的 `elog_output()` 支持 `va_list` 之外的可变参数接口，`ep_log_write()` 需要先把用户日志格式化到
内部缓冲区，再用 `elog_output()` 输出固定字符串。

第一版内部缓冲区建议：

```text
ep_log_write() 内部格式化缓冲区：256 bytes
超长日志：截断输出
```

截断日志仍返回 `EP_OK`。原因是日志输出不是业务控制流，第一版不把截断作为错误传播。

## Host POSIX port 行为

host POSIX 的 `elog_port_*` 第一版行为：

- `elog_port_init()` 创建输出 mutex。
- `elog_port_deinit()` 销毁输出 mutex。
- `elog_port_output()` 输出到 `stdout`。
- `elog_port_output_lock()` 加 mutex。
- `elog_port_output_unlock()` 解 mutex。
- `elog_port_get_time()` 基于 `ep_time_now_ms()` 返回毫秒字符串，例如 `ms:0000012345`。
- `elog_port_get_p_info()` 返回空字符串。
- `elog_port_get_t_info()` 返回空字符串。

host port 不直接使用 `time()`、`getpid()` 或 `syscall()`。原因：

- 我们已经有 OSAL time。
- 第一版不需要进程和线程信息。
- 这样能让后续 RTOS port 的行为更接近 host。

## Framework 接入策略

第一版实现 PR 建议分两步：

1. 先实现 `components/log` + EasyLogger + host 可验证输出。
2. 再单独设计/实现 `ep_framework_init()` 接入 `ep_log_init()`。

原因：

- 第一步只验证日志组件本身，PR 小。
- 第二步再调整启动顺序，避免把第三方引入、port、framework 初始化混在一个 PR。
- 如果 EasyLogger 接入构建有问题，影响范围不会扩散到 framework 启动链路。

第二步 framework 推荐顺序：

```text
ep_log_init()
ep_event_init()
ep_timer_init()
```

这样 event 和 timer 初始化失败时可以直接输出日志。

## 测试策略

第一版实现 PR 需要增加以下测试：

- `tests/api_contract/test_log_headers.py`
  - `ep_log.h` 存在。
  - `ep_log.h` 可独立编译。
  - `ep_log.h` 不包含 `elog.h`。
  - `ep_log.h` 不包含平台原生头文件。
- `tests/host_unit/test_host_log.py`
  - `components/log` CMake 接入。
  - `third_party/external/EasyLogger` 许可证文件存在。
  - `ep_log_init()` 可重复调用。
  - `ep_log_write()` 未初始化、空 tag、空 fmt、非法 level 的行为符合预期。
  - host 程序能输出一条 info 日志，输出中包含 tag 和内容。

完整验证：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
git diff --check
```

## 风险和控制

### 第三方源码进入仓库

EasyLogger 是 MIT 许可证，可以放入仓库，但必须保留 `LICENSE` 和源码头部版权声明。

控制方式：

- 不修改 EasyLogger 核心源码。
- 如果必须改配置，只改 `elog_cfg.h`。
- 如果必须改平台输出，只改 port 文件。

### API 泄漏风险

如果上层直接 include `elog.h`，后续替换日志后端会变困难。

控制方式：

- `ep_log.h` 不 include `elog.h`。
- `components/log/include` 是上层唯一可见接口。
- 契约测试显式检查 `ep_log.h` 不包含 `elog.h`。

### RTOS 适配风险

Luban-Lite 基于 RT-Thread，但具体版本、构建系统和日志输出 API 还未接入。

控制方式：

- 当前不写真实 RTOS port。
- 文档只约束未来 port 点。
- 真实平台接入时再选择 `rt_kprintf`、串口、RT-Thread device 或 Luban-Lite 自带日志接口。

### 异步输出风险

EasyLogger 支持异步输出，但会引入线程和额外同步机制。

控制方式：

- 第一版禁用异步输出。
- 需要异步时单独设计，明确缓冲区、丢日志策略、flush 时机和退出行为。

## 验收标准

- 中文设计文档提交到仓库。
- 后续实现 PR 中新增 `components/log` 和 `ep_log.h`。
- 后续实现 PR 中 EasyLogger 作为内部后端存在，但 `ep_log.h` 不暴露 EasyLogger。
- host POSIX 可构建并能验证日志输出。
- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 和 `cmake --build build` 通过。
- 本阶段不接入 Luban-Lite、RT-Thread 或真实板级 SDK。
