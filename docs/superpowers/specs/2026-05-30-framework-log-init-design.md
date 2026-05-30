# Framework 接入 log 初始化设计

## 背景

`components/log` 已经提供 `ep_log` 公共接口，并用 EasyLogger 作为当前内部后端。
现在 `ep_framework_init()` 仍然只初始化 `event` 和 `timer`：

```c
event -> timer
```

这会导致后续 framework、components 或 app 如果想在启动阶段写日志，必须自己先调用
`ep_log_init()`。这不符合当前工程“基础能力由 framework 统一拉起”的方向。

本设计只处理 framework 自动初始化 log，不做真实 Luban-Lite/RT-Thread port，也不增加业务日志输出。

## 目标

- 让 `ep_framework_init()` 在初始化 `event` 和 `timer` 前先初始化 `log`。
- 启动顺序固定为：

```text
log -> event -> timer
```

- `ep_log_init()` 失败时，`ep_framework_init()` 立即返回错误，不继续初始化后续组件。
- `ep_framework_start()` 保持现有行为：`ep_platform_boot()` 成功后调用 `ep_framework_init()`，初始化失败时不进入 `app_main()`。
- `core` 只依赖 `ep_log.h` 这个公共接口，不 include `elog.h`，不暴露 EasyLogger 到 core。
- host POSIX 和 linux demo 最终可执行目标需要链接 `ep_components_log`，保证 framework 引用 `ep_log_init()` 后可以完整链接。
- 所有新增说明、提交和 PR 内容继续使用中文。

## 非目标

- 不在 framework 启动过程中新增 `EP_LOGI()`、`EP_LOGE()` 等日志输出语句。
- 不调整 `ep_log` API。
- 不启用 EasyLogger 异步输出、文件插件或 Flash 插件。
- 不实现真实 Luban-Lite/RT-Thread 的日志输出 port。
- 不引入组件初始化表或自动注册机制。
- 不改变 `ep_platform_boot()`、`app_main()` 的职责。

## 方案比较

### 方案一：在 `ep_framework_init()` 中直接按顺序初始化

`ep_framework_init()` 直接调用：

```c
ep_log_init();
ep_event_init();
ep_timer_init();
```

每一步失败都立即返回错误。

优点：

- 改动最小，符合当前 `event`、`timer` 已经采用的显式初始化风格。
- 启动顺序非常直观，测试也容易约束。
- 适合当前组件数量还少的阶段。

缺点：

- 以后组件更多时，`ep_framework_init()` 会继续变长。

### 方案二：引入组件初始化表

定义一个 framework 组件初始化数组，按数组顺序逐个调用。

优点：

- 以后组件变多后扩展更统一。

缺点：

- 当前只有 `log`、`event`、`timer` 三个基础组件，抽象过早。
- 会引入新的初始化表结构、命名和测试边界，超过本小步需要。

### 方案三：仍由 app 手动初始化 log

app 或业务代码在需要日志前自己调用 `ep_log_init()`。

优点：

- framework 不需要变化。

缺点：

- 每个平台和 app 都要记住初始化日志，容易遗漏。
- framework 自己的启动阶段无法可靠写日志。
- 不符合“基础能力由 framework 统一拉起”的工程思想。

## 推荐方案

采用方案一：在 `ep_framework_init()` 中直接把 log 放到第一步初始化。

推荐原因是当前项目还处在平台骨架和基础组件阶段，显式顺序比抽象机制更清楚。
后续如果 device、config、network 等组件继续接入，再单独设计组件初始化表。

## 目标行为

`ep_framework_init()` 目标结构如下：

```c
int ep_framework_init(void)
{
    int rc = ep_log_init();
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
        -> ep_event_init()
        -> ep_timer_init()
     -> app_main()
```

如果 `ep_log_init()` 失败：

```text
ep_framework_init() 返回 log 错误码
ep_framework_start() 返回同一个错误码
app_main() 不会执行
```

## 构建影响

`core/src/ep_framework.c` 会 include `ep_log.h`，因此 `core/CMakeLists.txt` 需要把
`components/log/include` 加到 `ep_core` 的私有 include 路径中。

`ep_core` 仍然保持为静态库，不直接链接最终平台依赖。最终可执行目标负责链接需要的组件库：

- `platforms/host/posix` 已经链接 `ep_components_log`。
- `platforms/linux/demo_family` 当前还没有链接 `ep_components_log`，实现时需要补上。
- `platforms/rtos/demo_family` 当前是 demo 静态库，不在本小步做真实 RTOS 链接适配。

linux demo 的 OSAL stub 已经提供 `ep_time_now_ms()` 和 mutex 相关符号。mutex 创建当前返回
`EP_ERR_UNSUPPORTED`，EasyLogger port 会退化为无锁输出，所以第一版 linux demo 可以先完成链接闭环。

## 测试策略

实现 PR 需要先补测试，再改实现：

- 更新 `tests/host_unit/test_framework_bootstrap.py`
  - 检查 `ep_framework.c` include `ep_log.h`。
  - 检查 `ep_framework_init()` 调用 `ep_log_init()`。
  - 检查初始化顺序是 `ep_log_init()` 早于 `ep_event_init()`，`ep_event_init()` 早于 `ep_timer_init()`。
  - 检查 `core/CMakeLists.txt` 包含 `components/log/include`。
- 更新 `tests/api_contract/test_platform_bootstrap.py`
  - 检查 host POSIX 链接 `ep_components_log`。
  - 检查 linux demo 链接 `ep_components_log`。
  - 保持 demo 平台目标可以 configure 和 build。
- 保持已有 log 契约测试
  - `ep_log.h` 不暴露 `elog.h`。
  - 上层继续只依赖 `ep_log` 公共接口。

建议验证命令：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
./build/platforms/host/posix/ep_platform_host_posix
git diff --check
```

## 验收标准

- `ep_framework_init()` 初始化顺序为 `log -> event -> timer`。
- 任一初始化步骤失败时，framework 返回该错误码并停止后续启动。
- `core` 不直接依赖 EasyLogger 头文件。
- host POSIX 和 linux demo 均能链接包含 log 的 framework。
- 现有测试和新增测试全部通过。
- 本阶段不新增日志输出语句，不扩展 EasyLogger 能力，不接入真实 Luban-Lite/RT-Thread port。
