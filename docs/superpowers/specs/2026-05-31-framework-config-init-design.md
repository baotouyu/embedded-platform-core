# Framework 接入 config 初始化设计

## 背景

`components/config` 已经提供第一版内存配置表，公共接口是 `ep_config.h`，支持
`int`、`bool`、`string` 三类配置读写。

当前 `ep_framework_init()` 已经统一初始化基础组件：

```text
log -> event -> timer
```

但 config 还需要应用或业务代码手动调用 `ep_config_init()`。这会带来两个问题：

- 业务代码使用 `ep_config_get_*()` 前需要记住初始化 config。
- 后续如果日志等级、timer 参数、设备参数想从 config 读取，framework 启动链路里没有统一入口。

本设计只处理 framework 自动初始化 config，不增加文件配置、flash 配置，也不接入 Luban-Lite 或
RT-Thread。

## 目标

- 让 `ep_framework_init()` 在启动链路中自动调用 `ep_config_init()`。
- 初始化顺序固定为：

```text
log -> config -> event -> timer
```

- `ep_config_init()` 失败时，`ep_framework_init()` 立即返回错误，不继续初始化 event 和 timer。
- `ep_framework_start()` 保持现有行为：`ep_platform_boot()` 成功后调用 `ep_framework_init()`，初始化失败时不进入 `app_main()`。
- `core` 只依赖 `ep_config.h` 这个公共接口，不访问 config 内部存储结构。
- host POSIX 和 linux demo 最终可执行目标链接 `ep_components_config`，保证 framework 引用 `ep_config_init()` 后可以完整链接。
- 所有新增说明、提交和 PR 内容继续使用中文。

## 非目标

- 不改变 `ep_config` 公共 API。
- 不让 config 读取文件、环境变量、JSON、INI、YAML 或 TOML。
- 不实现配置保存、热更新、监听事件或默认配置注册表。
- 不把日志等级真正绑定到 config。
- 不引入组件初始化表或自动注册机制。
- 不实现真实 Luban-Lite、RT-Thread 或 flash/NVRAM 后端。
- 不改变 `ep_platform_boot()`、`app_main()` 的职责。

## 方案比较

### 方案一：在 `ep_framework_init()` 中直接按顺序初始化

`ep_framework_init()` 直接调用：

```c
ep_log_init();
ep_config_init();
ep_event_init();
ep_timer_init();
```

每一步失败都立即返回错误。

优点：

- 改动最小，符合当前 log、event、timer 的显式初始化风格。
- 启动顺序清楚，测试容易约束。
- 适合当前组件数量还少的阶段。

缺点：

- 后续基础组件继续增加时，`ep_framework_init()` 会继续变长。

### 方案二：引入组件初始化表

定义一个 framework 组件初始化数组，按数组顺序逐个调用。

优点：

- 后续组件增多后扩展更统一。

缺点：

- 当前只有 log、config、event、timer 四个基础组件，抽象仍然偏早。
- 会引入新的初始化表结构、命名和测试边界，超过本小步需要。

### 方案三：继续由 app 手动初始化 config

app 或业务代码在需要配置前自己调用 `ep_config_init()`。

优点：

- framework 不需要变化。

缺点：

- 每个平台和 app 都要记住初始化 config，容易遗漏。
- 后续基础组件无法稳定依赖 config。
- 不符合“基础能力由 framework 统一拉起”的工程方向。

## 推荐方案

采用方案一：在 `ep_framework_init()` 中直接把 config 放到 log 后、event 前初始化。

推荐原因：

- log 已经最早初始化，后续 framework 可以先具备日志能力。
- config 放在 event 和 timer 前，后续这些组件如果需要读取配置，启动顺序已经预留好位置。
- 当前 config 是内存表，`ep_config_init()` 幂等且不依赖 OSAL、文件系统或平台 port，适合放在早期。
- 暂时不引入初始化表，保持小步推进。

## 目标行为

`ep_framework_init()` 目标结构如下：

```c
int ep_framework_init(void)
{
    int rc = ep_log_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_config_init();
    if (rc != 0) {
        return rc;
    }

    rc = ep_event_init();
    if (rc != 0) {
        return rc;
    }

    return ep_timer_init();
}
```

调用链保持：

```text
main / app_start
  -> ep_framework_start()
     -> ep_platform_boot()
     -> ep_framework_init()
        -> ep_log_init()
        -> ep_config_init()
        -> ep_event_init()
        -> ep_timer_init()
     -> app_main()
```

如果 `ep_config_init()` 失败：

```text
ep_framework_init() 返回 config 错误码
ep_framework_start() 返回同一个错误码
event、timer、app_main() 不会执行
```

## 构建影响

`core/src/ep_framework.c` 会 include `ep_config.h`，因此 `core/CMakeLists.txt` 需要把
`components/config/include` 加到 `ep_core` 的私有 include 路径中。

`ep_core` 仍然保持为静态库，不直接链接最终平台依赖。最终可执行目标负责链接需要的组件库：

- `platforms/host/posix` 链接 `ep_components_config`。
- `platforms/linux/demo_family` 链接 `ep_components_config`。
- `platforms/rtos/demo_family` 当前是 demo 静态库，不在本小步做真实 RTOS 链接适配。

config 当前只依赖 `ep_osal_err.h` 和 C 标准库，不需要新增 OSAL port。

## 错误处理

`ep_framework_init()` 不转换错误码，直接返回下层初始化返回值。

行为约定：

- `ep_log_init()` 失败，直接返回 log 的错误码。
- `ep_log_init()` 成功后调用 `ep_config_init()`。
- `ep_config_init()` 失败，直接返回 config 的错误码，不继续初始化 event 和 timer。
- `ep_config_init()` 成功后继续初始化 event 和 timer。
- 全部成功时返回 `EP_OK`。

虽然当前 `ep_config_init()` 基本只会返回 `EP_OK`，framework 仍按失败传播方式编排。这样后续
config 换成文件、flash 或平台后端时，framework 行为不用重新设计。

## 测试策略

实现 PR 需要先补测试，再改实现：

- 更新 `tests/host_unit/test_framework_bootstrap.py`
  - 检查 `ep_framework.c` include `ep_config.h`。
  - 检查 `ep_framework_init()` 调用 `ep_config_init()`。
  - 检查初始化顺序是 `ep_log_init()` 早于 `ep_config_init()`，`ep_config_init()` 早于
    `ep_event_init()`，`ep_event_init()` 早于 `ep_timer_init()`。
  - 检查 `core/CMakeLists.txt` 包含 `components/config/include`。
- 更新 `tests/api_contract/test_platform_bootstrap.py`
  - 检查 host POSIX 链接 `ep_components_config`。
  - 检查 linux demo 链接 `ep_components_config`。
  - 保持 demo 平台目标可以 configure 和 build。
- 更新或新增 host 运行测试
  - `ep_platform_host_posix` 启动后可以不手动调用 `ep_config_init()`，直接使用 config get 默认值。
  - 这条可以通过源码契约加构建运行先覆盖，后续如需更精确验证，可引入可替换测试 stub。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
git diff --check
```

## 验收标准

- `ep_framework_init()` 初始化顺序为 `log -> config -> event -> timer`。
- 任一初始化步骤失败时，framework 返回该错误码并停止后续启动。
- `core` 不访问 config 内部结构，只 include `ep_config.h`。
- host POSIX 和 linux demo 均能链接包含 config 的 framework。
- 现有测试和新增测试全部通过。
- 本阶段不新增文件配置、flash 配置、真实 Luban-Lite/RT-Thread port，也不把日志等级绑定到 config。
