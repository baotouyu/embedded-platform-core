# Config 内存配置组件设计

## 背景

当前工程已经具备 `event`、`timer`、`log` 三个基础组件，并且 `framework` 已统一初始化
`log -> event -> timer`。下一步不急着适配真实芯片平台，也不急着做设备管理，可以先补一个平台无关的
`components/config`。

`config` 的作用是给 app、core 和 components 提供统一配置入口，避免业务代码到处写死参数。例如：

```text
log.level
device.timeout_ms
uart.baudrate
network.server
feature.some_flag
```

第一版只做 host 可测的内存 key/value 配置表，不落盘、不读取文件、不接 flash、不依赖 Luban-Lite 或
RT-Thread。

## 目标

- 新增 `components/config` 组件。
- 暴露平台无关公共头文件 `components/config/include/ep_config.h`。
- 提供最小初始化接口：

```c
int ep_config_init(void);
```

- 支持三类配置值：

```text
int
bool
string
```

- 支持 set/get：

```c
int ep_config_set_int(const char *key, int value);
int ep_config_get_int(const char *key, int default_value);

int ep_config_set_bool(const char *key, int value);
int ep_config_get_bool(const char *key, int default_value);

int ep_config_set_string(const char *key, const char *value);
const char *ep_config_get_string(const char *key, const char *default_value);
```

- `get` 接口在 key 不存在、类型不匹配或组件未初始化时返回调用方传入的默认值。
- `set` 接口在参数非法、组件未初始化、容量不足时返回明确错误码。
- 公共头文件不包含平台原生头文件，不包含 `pthread.h`、`unistd.h`、`rtthread.h` 或 SDK 头文件。
- 组件实现可在 Mac/Ubuntu host 上用单元测试验证。

## 非目标

- 不读取配置文件。
- 不写入配置文件。
- 不接 flash、NVRAM、EEPROM 或出厂参数区。
- 不解析 JSON、INI、YAML 或 TOML。
- 不支持数组、结构体、浮点数或二进制 blob。
- 不支持配置热加载。
- 不支持配置变更事件通知。
- 不把 `config` 接入 `ep_framework_init()`。
- 不适配匠芯创 Luban-Lite、RT-Thread 或真实板级 SDK。

## 方案比较

### 方案一：内存 key/value 配置表

`components/config` 内部维护固定容量表，key 和 value 都复制到组件内部存储。

优点：

- 最小、可测、平台无关。
- 不需要 file、flash 或平台 SDK。
- 以后可以在初始化阶段从文件/flash 加载配置，但上层 API 不变。
- 适合当前还在 Mac 上跑通公共组件的阶段。

缺点：

- 进程退出后配置丢失。
- 容量和字符串长度需要固定上限。

### 方案二：直接做文件配置

第一版直接从文件读取配置并落盘。

优点：

- 更接近 Linux/Ubuntu 上的实际使用。
- 配置可以跨进程保存。

缺点：

- 需要先定义文件格式和路径策略。
- 会过早绑定 `components/file` 或 POSIX 文件接口。
- 后续迁移到 Luban-Lite flash 时还要拆存储后端。

### 方案三：只做编译期宏配置

所有配置都通过 CMake 或头文件宏定义，运行时不允许修改。

优点：

- 实现最简单。
- 编译期可控。

缺点：

- 不适合运行时调参。
- 业务代码容易重新依赖编译宏。
- 后续加文件/flash 配置时 API 需要重做。

## 推荐方案

采用方案一：内存 key/value 配置表。

理由是当前目标是先建立稳定公共接口，而不是马上解决持久化。内存表足够验证：

- API 形状是否好用。
- key 命名是否清晰。
- 类型错误、默认值、容量限制等行为是否合理。
- 后续 file/flash 后端能否在不影响上层代码的情况下接入。

## 公共 API 设计

`components/config/include/ep_config.h`：

```c
#ifndef EP_CONFIG_H
#define EP_CONFIG_H

int ep_config_init(void);

int ep_config_set_int(const char *key, int value);
int ep_config_get_int(const char *key, int default_value);

int ep_config_set_bool(const char *key, int value);
int ep_config_get_bool(const char *key, int default_value);

int ep_config_set_string(const char *key, const char *value);
const char *ep_config_get_string(const char *key, const char *default_value);

#endif
```

API 设计说明：

- `set` 返回 `int`，使用 `EP_OK`、`EP_ERR_INVAL`、`EP_ERR_UNSUPPORTED`、`EP_ERR_BUSY` 等现有错误码。
- `get_int` 和 `get_bool` 直接返回值，找不到时返回默认值，调用方不需要额外判断错误码。
- `get_string` 返回内部只读字符串指针或调用方传入的默认字符串。
- `bool` 第一版使用 `int` 表示，`0` 为 false，非 `0` 写入时统一保存为 `1`。
- key 使用普通 C 字符串，第一版不做层级解析，`.` 只是命名约定。

## 内部数据模型

内部条目包含：

```c
typedef enum {
    EP_CONFIG_VALUE_INT = 0,
    EP_CONFIG_VALUE_BOOL = 1,
    EP_CONFIG_VALUE_STRING = 2
} ep_config_value_type_e;

typedef struct {
    int used;
    char key[EP_CONFIG_KEY_MAX_LEN];
    ep_config_value_type_e type;
    union {
        int int_value;
        int bool_value;
        char string_value[EP_CONFIG_STRING_MAX_LEN];
    } value;
} ep_config_entry_t;
```

建议第一版固定上限：

```text
EP_CONFIG_MAX_ITEMS       32
EP_CONFIG_KEY_MAX_LEN     48
EP_CONFIG_STRING_MAX_LEN  96
```

边界策略：

- key 长度必须小于 `EP_CONFIG_KEY_MAX_LEN`，否则 `set` 返回 `EP_ERR_INVAL`。
- string value 长度必须小于 `EP_CONFIG_STRING_MAX_LEN`，否则 `set_string` 返回 `EP_ERR_INVAL`。
- 空 key、空 value 指针返回 `EP_ERR_INVAL`。
- key 已存在时，`set` 覆盖旧值和类型。
- key 不存在且表未满时，`set` 新增条目。
- key 不存在且表已满时，`set` 返回 `EP_ERR_BUSY`。

## 初始化行为

`ep_config_init()` 行为：

1. 第一次调用时清空内部表。
2. 标记 config 已初始化。
3. 重复调用返回 `EP_OK`，不清空已有配置。

重复调用不清空已有配置的原因：

- 与 `ep_log_init()`、`ep_event_init()`、`ep_timer_init()` 的幂等方向一致。
- 避免某个模块重复初始化 config 时意外丢失运行时配置。

## 错误处理

`set` 接口：

- 未初始化返回 `EP_ERR_UNSUPPORTED`。
- key 为 `0` 或空字符串返回 `EP_ERR_INVAL`。
- value 指针为 `0` 时，`set_string` 返回 `EP_ERR_INVAL`。
- key 或 string value 超过上限返回 `EP_ERR_INVAL`。
- 容量满返回 `EP_ERR_BUSY`。
- 成功返回 `EP_OK`。

`get` 接口：

- 未初始化返回默认值。
- key 为 `0` 或空字符串返回默认值。
- key 不存在返回默认值。
- key 存在但类型不匹配返回默认值。

## 构建接入

新增：

```text
components/config/
├── CMakeLists.txt
├── include/
│   └── ep_config.h
└── src/
    └── ep_config.c
```

根 `CMakeLists.txt` 需要添加：

```cmake
add_subdirectory(components/config)
```

`components/config/CMakeLists.txt` 定义：

```cmake
add_library(ep_components_config STATIC
  src/ep_config.c
)

target_include_directories(ep_components_config
  PUBLIC
    ${CMAKE_CURRENT_SOURCE_DIR}/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/osal/include
)
```

第一版只依赖 `osal/include/ep_osal_err.h` 的错误码，不依赖 OSAL mutex。当前 framework 启动仍然不自动初始化
config，所以平台可执行目标不需要立即链接 `ep_components_config`。

## 测试策略

实现 PR 需要先补测试，再写代码：

- `tests/api_contract/test_config_headers.py`
  - `ep_config.h` 存在。
  - `ep_config.h` 可独立编译。
  - `ep_config.h` 不包含平台原生头文件。
  - `ep_config.h` 不包含 file、flash、EasyLogger 或 RT-Thread 头文件。
- `tests/host_unit/test_host_config.py`
  - config 组件接入 CMake。
  - `ep_config_init()` 可重复调用且不清空已有配置。
  - 未初始化 `set` 返回 `EP_ERR_UNSUPPORTED`。
  - 未初始化 `get` 返回默认值。
  - int/bool/string set/get 正常。
  - key 不存在返回默认值。
  - 类型不匹配返回默认值。
  - 空 key、空 string value、超长 key、超长 string value 返回 `EP_ERR_INVAL`。
  - 容量满返回 `EP_ERR_BUSY`。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
git diff --check
```

## 后续扩展

本阶段只建立 `ep_config` API 和内存后端。后续可以单独设计：

- `components/file` 提供统一文件访问。
- config 从文件加载默认配置。
- config 保存到文件。
- Luban-Lite/RT-Thread 平台映射到 flash、NVRAM 或出厂参数区。
- 配置变更发布 event。
- `ep_framework_init()` 自动初始化 config。

## 验收标准

- 新增 `ep_config` 公共接口设计清晰，平台无关。
- 第一版实现范围限定为内存 key/value 表。
- get 接口默认值行为明确。
- set 接口错误码行为明确。
- 不引入文件、flash、JSON、Luban-Lite、RT-Thread 或平台 SDK 依赖。
- 后续可以在不改变上层 API 的情况下接入持久化后端。
