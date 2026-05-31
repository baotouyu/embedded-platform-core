# Framework 启动加载配置文件设计

## 背景

当前工程已经具备：

- `components/config` 内存配置表。
- `ep_config_load_file(const char *path)` 从文本文件加载配置。
- `ep_framework_init()` 统一初始化 `log -> config -> event -> timer`。

现在的问题是：配置文件加载能力已经有了，但启动链路还没有使用它。也就是说 app 启动后，配置表仍然只靠代码手动
`set`，不会自动加载默认配置。

下一步建议把“启动时加载默认配置文件”接入 framework。第一版只做 host/Mac/Ubuntu 可验证的默认配置加载，不做真实板级平台适配。

## 目标

- framework 初始化时，在 `ep_config_init()` 后尝试加载默认配置文件。
- 默认配置文件路径先使用固定路径：

```text
config/profiles/host.cfg
```

- 文件存在且格式正确时，配置写入 config 内存表。
- 文件不存在时，不让 framework 启动失败，继续执行后续 `event`、`timer` 初始化。
- 文件存在但内容格式错误时，让 framework 初始化失败并返回错误码。
- host/Mac/Ubuntu 上通过测试验证启动链路能读取配置文件。

## 非目标

- 不做命令行参数配置路径。
- 不做环境变量配置路径。
- 不做 CMake profile 自动生成配置文件。
- 不做多配置文件叠加加载。
- 不做配置保存、热加载或 watch。
- 不适配 Luban-Lite、RT-Thread 或真实 flash/NVRAM。
- 不改变 `ep_config_load_file()` 的文件格式。
- 不改变 `app_main()` 的接口。

## 方案比较

### 方案一：framework 内部加载固定默认路径

`ep_framework_init()` 在 `ep_config_init()` 后调用：

```c
ep_config_load_file("config/profiles/host.cfg");
```

文件不存在时忽略，其他错误返回失败。

优点：

- 改动小，能马上让启动链路使用配置文件。
- 不影响 app/main 参数。
- Mac/Ubuntu 上容易跑通。
- 适合当前还没进入真实平台适配的阶段。

缺点：

- 路径是固定的，不够灵活。
- 后续不同产品/板子需要再引入 profile 选择机制。

### 方案二：framework 暴露带路径的初始化接口

新增：

```c
int ep_framework_init_with_config(const char *path);
```

或者：

```c
int ep_framework_start_with_config(const char *path);
```

优点：

- 调用方可以传不同配置文件。
- 后续平台或 app 可以自己决定路径。

缺点：

- 现在会扩展 framework 公共 API。
- host `main()`、linux demo、RTOS demo 都要考虑是否传路径。
- 第一版需求还不需要这么灵活。

### 方案三：平台层 `ep_platform_boot()` 负责加载配置

平台启动时调用 `ep_config_load_file()`。

优点：

- 不同平台可以有不同路径。
- 更接近真实板级差异。

缺点：

- 当前 `ep_platform_boot()` 在 `ep_framework_init()` 之前调用，而 config 还没初始化。
- 要么平台层自己调用 `ep_config_init()`，要么调整启动顺序，都会让边界变乱。
- 容易让平台层直接依赖 config 组件细节。

## 推荐方案

采用方案一：framework 内部加载固定默认路径。

理由：

- 当前目标是小步跑通“启动 -> config init -> load file -> app 使用配置”的链路。
- 固定路径能先把行为验证清楚，后续再单独设计 profile 选择。
- 不改 app/main 接口，不扩大 framework 公共 API。
- 文件缺失时不失败，保证现有 demo 和测试不会因为没有配置文件而不能启动。

## 启动顺序

第一版启动顺序：

```text
ep_framework_start()
  -> ep_platform_boot()
  -> ep_framework_init()
       -> ep_log_init()
       -> ep_config_init()
       -> ep_framework_load_default_config()
       -> ep_event_init()
       -> ep_timer_init()
  -> app_main()
```

其中 `ep_framework_load_default_config()` 是 core 内部静态函数，不进入公共头文件。

## 默认路径

默认路径定义在 `core/src/ep_framework.c` 内部：

```c
#define EP_FRAMEWORK_DEFAULT_CONFIG_PATH "config/profiles/host.cfg"
```

第一版不放到公共头文件，不做 CMake option。

原因：

- 目前只有 host/Mac/Ubuntu 跑通需求。
- 后续 profile 选择可能需要更完整设计，比如 `config/profiles/<board>.cfg`、CMake 生成宏或平台返回路径。
- 现在先避免把不稳定路径策略暴露成公共 API。

## 错误处理

`ep_framework_load_default_config()` 行为：

```text
EP_OK                  -> 加载成功，继续启动。
EP_ERR_UNSUPPORTED     -> 认为默认配置文件不存在或当前 file 后端不可用，继续启动。
EP_ERR_INVAL           -> 配置文件存在但内容不合法，framework 初始化失败。
EP_ERR_BUSY            -> 配置过大、容量不足或资源不足，framework 初始化失败。
其他非 0 错误码        -> framework 初始化失败。
```

这个策略的核心是：

- “没配置文件”是可接受状态。
- “有配置文件但写错了”是启动错误，不能静默忽略。

当前 `ep_config_load_file()` 对缺失文件返回 `EP_ERR_UNSUPPORTED`，所以 framework 第一版只能把 `EP_ERR_UNSUPPORTED` 统一当作“可忽略”。如果后续要区分“文件不存在”和“后端不可用”，需要扩展 file/config 错误码或增加更细的状态接口。

## 默认配置文件

新增：

```text
config/profiles/host.cfg
```

内容建议：

```text
int log.level=3
bool feature.enabled=true
string device.name=host
```

这个文件用于 host/Mac/Ubuntu 的默认 profile 示例，也用于测试确认 framework 能加载配置。

## 测试策略

实现 PR 需要先补测试，再写代码：

- `tests/host_unit/test_framework_bootstrap.py`
  - 检查 `ep_framework.c` 包含 `ep_config_load_file()` 调用。
  - 检查调用顺序为 `ep_config_init()` 后、`ep_event_init()` 前。
  - 检查缺失默认配置文件时 framework 仍能启动。因为仓库会提交默认 `host.cfg`，测试可以通过临时把工作目录切到没有该文件的目录，或用编译时覆盖默认路径的方式验证。
  - 检查默认配置文件存在时，framework 启动后 config 表包含文件中的值。

- `tests/host_unit/test_repository_layout.py`
  - 检查 `config/profiles/host.cfg` 存在。

- CMake build：
  - 确认 core 仍然能链接 config 和 file 依赖链。
  - 确认 host posix demo 仍能运行。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
git diff --check
```

## 验收标准

- framework 初始化会尝试加载 `config/profiles/host.cfg`。
- `host.cfg` 存在且合法时，配置进入 config 内存表。
- `host.cfg` 缺失时，framework 启动不失败。
- `host.cfg` 格式错误时，framework 初始化失败并返回错误码。
- 不新增 framework 公共 API。
- 不修改 app/main 接口。
- 不接 Luban-Lite、RT-Thread 或真实 flash/NVRAM。
