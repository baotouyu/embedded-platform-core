# 应用运行骨架设计

## 背景

当前工程已经具备一组可在 Mac host 环境运行的基础能力：

- `ep_framework_start()` 负责平台启动、framework 初始化和进入 `app_main()`。
- framework 初始化时会启动日志、配置、事件和定时器组件。
- `components/log` 已接入 EasyLogger，并支持配置驱动的日志等级。
- `components/event` 提供异步事件发布和订阅。
- `components/timer` 可以在定时器到期后发布事件。
- `app/main.c` 当前仍是空实现，只返回 `0`。

这意味着工程底层积木已经能运行，但应用层还没有一条可观察、可测试的业务启动链路。下一步不急着接真实芯片或设备抽象，先让 `app/` 层形成一个最小运行骨架，方便在 Mac 上验证 framework 到 app 的完整路径。

## 目标

- `app_main()` 不再空返回，而是执行一个最小应用生命周期流程。
- 程序启动后输出应用启动日志。
- 应用订阅一个自身事件。
- 应用启动一个短定时器。
- 定时器到期后通过事件总线触发回调。
- 应用主流程等待该事件，收到事件后输出完成日志并自动退出。
- 如果等待超时，`app_main()` 返回错误码。
- 默认 host bin 行为是短暂运行后自动退出，适合本地测试和 CI。
- 应用层继续保持平台无关，不包含 Linux、macOS、RTOS 或 vendor SDK 头文件。

## 非目标

- 不做真实设备抽象。
- 不接 Luban-Lite、RT-Thread 或具体芯片 SDK。
- 不做常驻主循环。
- 不做 `Ctrl+C` 信号处理。
- 不做周期定时器。
- 不做应用任务系统。
- 不做复杂状态机框架。
- 不引入新的第三方库。

## 方案比较

### 方案一：`app_main()` 内实现最小生命周期流程

在 `app/main.c` 内完成：

- 订阅应用事件。
- 启动一个短定时器。
- 等待事件回调设置完成标志。
- 成功后返回 `0`，超时返回错误码。

优点：

- 改动小，能最快形成可运行应用行为。
- 不提前抽象应用框架，避免设计过度。
- 能直接验证 log、event、timer、framework 的串联。
- 适合当前“先在 Mac 上跑通，再慢慢适配平台”的节奏。

缺点：

- `app/main.c` 会暂时承担示例业务逻辑。
- 后续真实业务变复杂时，需要再拆分应用模块。

### 方案二：新增 `app_lifecycle` 模块

新增 `app/src/app_lifecycle.c` 和 `app/include/app_lifecycle.h`，`app_main()` 只调用 `app_lifecycle_run()`。

优点：

- 结构更像正式应用。
- 后续扩展状态机、任务、业务模块时更好拆分。

缺点：

- 当前业务逻辑很小，新增模块会让第一步显得偏重。
- 需要调整 app 目录和 CMake，实施成本略高。

### 方案三：直接做常驻主循环

`app_main()` 初始化后进入无限循环，模拟真实嵌入式应用常驻运行。

优点：

- 更接近真实 RTOS/嵌入式程序。

缺点：

- Mac host bin 运行后不会自动退出，不利于 CI 和本地快速验证。
- 现在还没有退出控制、信号处理或生命周期管理。
- 容易在基础骨架还没稳定时引入调试不便。

## 推荐方案

采用方案一：`app_main()` 内实现最小生命周期流程。

理由：

- 当前目标是先把应用入口变成“可观察、可测试、可自动退出”的运行链路。
- 这一步应该尽量小，验证 framework 到 app 的完整路径即可。
- 后续如果应用逻辑增加，再按真实需求拆出 `app_lifecycle` 或业务模块。
- 默认自动退出更适合 Mac 本地开发和 GitHub Actions。

## 应用事件设计

新增应用事件 ID 头文件：

```text
app/include/app_events.h
```

第一版只定义一个应用内部事件：

```c
#define APP_EVENT_TIMER_DONE 1000
```

事件 ID 先使用普通宏，不引入枚举或事件命名空间系统。原因是当前事件数量很少，过早设计事件注册表没有必要。

`APP_EVENT_TIMER_DONE` 只表示本次应用启动自检定时器到期，不代表业务周期 tick。

## 运行流程

`app_main()` 的目标流程：

```text
输出 app 启动日志
订阅 APP_EVENT_TIMER_DONE
启动一个 50ms 定时器
循环等待事件完成标志
  每次 sleep 10ms
  最多等待 500ms
收到事件：
  输出 app 完成日志
  返回 0
超时：
  输出错误日志
  返回 EP_ERR_TIMEOUT
```

事件回调只做轻量工作：

- 校验事件 ID。
- 设置 `done` 标志。
- 不阻塞。
- 不调用复杂业务。

等待使用 OSAL 时间接口，不使用 `unistd.h`、`pthread.h` 或平台原生 sleep。

## 依赖边界

`app/main.c` 允许包含：

- `app_events.h`
- `app_main.h`
- `ep_event.h`
- `ep_log.h`
- `ep_osal_err.h`
- `ep_osal_time.h`
- `ep_timer.h`

`app/main.c` 不允许包含：

- `pthread.h`
- `unistd.h`
- `signal.h`
- Linux/macOS 系统头文件
- RTOS 头文件
- vendor SDK 头文件

`app/` 仍然只依赖 framework 暴露出来的公共组件接口和 OSAL 接口。

## 错误处理

- `ep_event_subscribe()` 失败时，`app_main()` 立即返回该错误码。
- `ep_timer_start()` 失败时，`app_main()` 立即返回该错误码。
- 等待超时返回 `EP_ERR_TIMEOUT`。
- 收到事件后返回 `0`。

第一版不做资源释放。原因是当前 event 和 timer 组件本身也是 framework 生命周期内常驻资源，host bin 会在流程结束后退出。

## 测试策略

新增或调整 host 测试，覆盖：

- `app/include/app_events.h` 存在并定义 `APP_EVENT_TIMER_DONE`。
- `app/main.c` 不包含平台原生头文件。
- `app/main.c` 使用 `ep_event_subscribe()`、`ep_timer_start()`、`ep_sleep_ms()` 和日志接口。
- CMake 构建 host bin 成功。
- 运行 `ep_platform_host_posix` 返回 `0`。
- 运行输出包含应用启动和完成日志。

测试重点是验证完整链路：

```text
framework start -> app_main -> timer -> event -> callback -> app exits
```

## 验收标准

- `pytest tests/host_unit tests/api_contract -v` 通过。
- `cmake -S . -B build` 通过。
- `cmake --build build` 通过。
- `./build/platforms/host/posix/ep_platform_host_posix` 自动退出并返回 `0`。
- host bin 输出能看到应用启动和应用完成日志。
- `app/` 层没有平台原生头文件依赖。

## 后续扩展

这次完成后，可以再按小步继续：

- 增加配置项控制 app 超时时间。
- 增加常驻模式配置。
- 把 app lifecycle 从 `app/main.c` 拆成独立模块。
- 接入设备抽象。
- 再开始 Luban-Lite / RT-Thread 平台适配。
