# 配置驱动日志等级设计

## 背景

当前工程已经完成：

- `components/log` 使用 EasyLogger 作为日志后端，并暴露平台无关 `ep_log` 接口。
- `components/config` 支持内存配置和文本配置文件加载。
- `ep_framework_init()` 会加载 `config/profiles/host.cfg`。
- `config/profiles/host.cfg` 已经包含：

```text
int log.level=3
```

现在的问题是：`log.level` 已经进入 config 内存表，但日志组件还没有使用这个值控制输出。也就是说配置文件里改
`log.level`，当前不会影响 `EP_LOGD()`、`EP_LOGV()` 等日志是否输出。

下一步建议把 `log.level` 接到日志组件，但只做运行时等级过滤，不做复杂日志系统。

## 目标

- `ep_log` 新增公共 API，用于设置当前日志输出等级。
- `ep_log_write()` 根据当前等级过滤日志。
- framework 在加载默认配置后读取 `log.level`，并设置日志等级。
- `log.level=3` 表示输出 `ASSERT`、`ERROR`、`WARN`、`INFO`，过滤 `DEBUG`、`VERBOSE`。
- `log.level` 缺失时使用默认等级 `INFO`。
- `log.level` 超出 `EP_LOG_LEVEL_ASSERT` 到 `EP_LOG_LEVEL_VERBOSE` 范围时，framework 初始化失败。
- 保持 `components/log` 不依赖 `components/config`。

## 非目标

- 不做按 tag 的日志等级过滤。
- 不做关键词过滤。
- 不做日志颜色配置。
- 不做日志输出目的地配置。
- 不做运行时命令行修改日志等级。
- 不做日志等级持久化保存。
- 不修改 EasyLogger 第三方源码。
- 不接 Luban-Lite、RT-Thread 或真实串口输出。

## 方案比较

### 方案一：log 组件提供等级 API，framework 从 config 读取后设置

新增：

```c
int ep_log_set_level(ep_log_level_e level);
ep_log_level_e ep_log_get_level(void);
```

`ep_log_write()` 在调用 EasyLogger 前先判断日志等级。framework 在默认配置加载后读取：

```c
ep_config_get_int("log.level", EP_LOG_LEVEL_INFO);
```

然后调用：

```c
ep_log_set_level((ep_log_level_e)level);
```

优点：

- `ep_log` 不依赖 `ep_config`，组件边界清楚。
- framework 已经负责启动顺序，适合做 config 到 log 的桥接。
- 后续如果要从 shell、网络或调试命令修改日志等级，也可以复用 `ep_log_set_level()`。
- 测试容易写：log 组件单测覆盖过滤行为，framework 测试覆盖配置应用行为。

缺点：

- framework 会知道 `log.level` 这个配置 key。
- 需要给 `ep_log` 增加两个公共 API。

### 方案二：log 组件自己读取 config

`ep_log_init()` 或 `ep_log_write()` 内部调用 `ep_config_get_int("log.level", ...)`。

优点：

- framework 代码少。
- 日志等级逻辑都在 log 组件内。

缺点：

- `components/log` 会依赖 `components/config`，边界变复杂。
- 当前启动顺序是 `log -> config -> load config`，log 初始化时 config 还没有准备好。
- 如果 `ep_log_write()` 每次都读 config，会引入不必要耦合和运行时开销。

### 方案三：直接使用 EasyLogger 的过滤 API，不扩展 ep_log API

framework include EasyLogger 头文件，加载配置后直接调用：

```c
elog_set_filter_lvl(level);
```

优点：

- 改动少。
- 能复用 EasyLogger 内部过滤能力。

缺点：

- framework 会直接依赖 EasyLogger，破坏 `ep_log` 对第三方库的封装。
- 以后替换日志后端时，core/framework 也要跟着改。
- 不符合当前 `ep_log.h` 隐藏 EasyLogger 的设计原则。

## 推荐方案

采用方案一：log 组件提供等级 API，framework 从 config 读取后设置。

理由：

- 这是最符合当前组件边界的方式。
- `log.level` 的配置读取属于 framework 启动编排，不应该放进 log 组件内部。
- `ep_log_set_level()` 是稳定且有复用价值的公共能力，不是临时接口。
- 第一版只做全局等级，避免 tag/filter/颜色等功能提前复杂化。

## 日志等级语义

沿用现有 `ep_log_level_e`：

```c
typedef enum {
    EP_LOG_LEVEL_ASSERT = 0,
    EP_LOG_LEVEL_ERROR = 1,
    EP_LOG_LEVEL_WARN = 2,
    EP_LOG_LEVEL_INFO = 3,
    EP_LOG_LEVEL_DEBUG = 4,
    EP_LOG_LEVEL_VERBOSE = 5
} ep_log_level_e;
```

等级数字越大，输出越详细。

过滤规则：

```text
message_level <= current_level -> 输出
message_level > current_level  -> 不输出，返回 EP_OK
```

示例：

```text
current_level = EP_LOG_LEVEL_INFO
ASSERT、ERROR、WARN、INFO 输出
DEBUG、VERBOSE 不输出
```

被过滤的日志返回 `EP_OK`。原因是调用方写日志不是业务失败，过滤只是日志策略。

## 公共 API 设计

修改：

```text
components/log/include/ep_log.h
```

新增：

```c
int ep_log_set_level(ep_log_level_e level);
ep_log_level_e ep_log_get_level(void);
```

接口语义：

- `ep_log_set_level()` 接受 `EP_LOG_LEVEL_ASSERT` 到 `EP_LOG_LEVEL_VERBOSE`。
- 非法等级返回 `EP_ERR_INVAL`，当前等级不变。
- 初始化前允许调用 `ep_log_set_level()`，这样 framework 或测试可以先设置策略再初始化输出后端。
- `ep_log_get_level()` 返回当前等级，不失败。
- 默认等级为 `EP_LOG_LEVEL_INFO`。

## log 组件内部行为

`components/log/src/ep_log.c` 增加：

```c
static ep_log_level_e g_ep_log_level = EP_LOG_LEVEL_INFO;
```

`ep_log_write()` 流程调整为：

```text
1. 未初始化时返回 EP_ERR_UNSUPPORTED。
2. tag 或 fmt 为空时返回 EP_ERR_INVAL。
3. 校验 level 是否为合法 ep_log_level_e。
4. 如果 level > g_ep_log_level，直接返回 EP_OK，不调用 EasyLogger。
5. 转换到 EasyLogger 等级。
6. 格式化并输出。
```

先校验 level，再过滤。这样非法等级仍然返回 `EP_ERR_INVAL`，不会因为当前过滤等级较低而被静默吞掉。

EasyLogger 自身可以继续保持 `ELOG_OUTPUT_LVL ELOG_LVL_VERBOSE`，因为编译期允许所有等级，运行期由 `ep_log` 过滤。

## framework 集成

`ep_framework_init()` 当前顺序是：

```text
ep_log_init()
ep_config_init()
ep_framework_load_default_config()
ep_event_init()
ep_timer_init()
```

新增一个 core 内部静态函数：

```c
static int ep_framework_apply_log_config(void)
```

调用位置：

```text
ep_log_init()
ep_config_init()
ep_framework_load_default_config()
ep_framework_apply_log_config()
ep_event_init()
ep_timer_init()
```

函数行为：

```text
level = ep_config_get_int("log.level", EP_LOG_LEVEL_INFO)
如果 level < EP_LOG_LEVEL_ASSERT 或 level > EP_LOG_LEVEL_VERBOSE，返回 EP_ERR_INVAL
否则 ep_log_set_level((ep_log_level_e)level)
```

`log.level` 缺失时使用默认 `INFO`。这是为了让没有配置文件的启动路径继续保持可用。

## 配置文件

保留当前默认配置：

```text
int log.level=3
```

第一版不新增其他日志配置 key。

未来如果需要，可以单独设计：

```text
bool log.color=true
string log.output=stdout
int log.tag.net=4
```

这些不进入本次范围。

## 错误处理

- `ep_log_set_level((ep_log_level_e)-1)` 返回 `EP_ERR_INVAL`。
- `ep_log_set_level((ep_log_level_e)6)` 返回 `EP_ERR_INVAL`。
- `ep_log_write()` 收到非法 level 返回 `EP_ERR_INVAL`。
- `ep_log_write()` 收到被过滤的合法 level 返回 `EP_OK`。
- framework 读取到非法 `log.level` 时，`ep_framework_init()` 返回 `EP_ERR_INVAL`。
- 默认配置文件缺失时，framework 已经会继续启动；此时日志等级使用 `INFO`。

## 测试策略

实现 PR 需要按 TDD 补测试：

- `tests/api_contract/test_log_headers.py`
  - 检查 `ep_log.h` 仍然不暴露 EasyLogger 或平台头。
  - 检查 `ep_log_set_level()`、`ep_log_get_level()` 在公共头中声明。

- `tests/host_unit/test_host_log.py`
  - 验证默认等级是 `INFO`。
  - 验证设置为 `WARN` 后，`INFO` 日志不输出但返回 `EP_OK`，`ERROR` 日志输出。
  - 验证设置为 `VERBOSE` 后，`DEBUG` 或 `VERBOSE` 日志输出。
  - 验证非法等级返回 `EP_ERR_INVAL`，当前等级不变。

- `tests/host_unit/test_framework_bootstrap.py`
  - 源码结构测试检查 framework 包含 `ep_framework_apply_log_config()`。
  - 检查调用顺序在 `ep_framework_load_default_config()` 后、`ep_event_init()` 前。
  - smoke 测试用 `config/profiles/host.cfg` 验证 framework 启动后 INFO 日志输出、DEBUG 日志被过滤。
  - 临时坏配置测试写入 `int log.level=99`，验证 `ep_framework_init()` 返回 `EP_ERR_INVAL`。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
git diff --check
```

## 验收标准

- `log.level=3` 能让 framework 启动后过滤 DEBUG/VERBOSE 日志。
- `ep_log_set_level()` 可以独立控制日志输出等级。
- `ep_log_get_level()` 能返回当前等级。
- 非法日志等级不会被接受。
- `components/log` 不依赖 `components/config`。
- framework 是 config 到 log 的唯一桥接点。
- 所有 host 单元测试和 API contract 测试通过。
