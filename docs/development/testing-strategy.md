# 测试策略

本文档定义 `embedded-platform-core` 的自动化测试和模块化测试策略。目标是让公共接口、
平台无关逻辑、平台适配和真实目标环境都有清晰的测试边界。

## 测试分层

仓库测试按以下目录分层：

```text
tests/host_unit/
tests/api_contract/
```

当前主仓库只保留已经实际使用的测试目录。集成测试和目标板冒烟测试作为测试分层保留在文档里，但不提前保留空目录。

### `tests/host_unit`

`tests/host_unit` 放主机侧单元测试，运行在开发机或 CI 的普通 Linux/macOS 环境。

适合覆盖：

- 平台无关的 C 逻辑
- 解析器、配置、状态机等纯逻辑模块
- CMake、仓库结构、文档和工程规则
- 不依赖真实 RTOS SDK、真实设备节点或板级资源的行为

要求：

- 测试应该快速、稳定、无外部设备依赖。
- 新增公共组件时，优先在这里补模块化测试。
- 失败信息要指出具体缺失的文件、符号、配置或行为。

### `tests/api_contract`

`tests/api_contract` 放公共 API 契约测试，用来保护 `core`、`osal`、`hal` 和平台启动边界。

适合覆盖：

- 公共头文件能否独立编译
- `ep_` 前缀、类型命名和函数签名是否稳定
- OSAL/HAL 是否暴露平台无关接口
- RTOS 和 Linux 平台包是否都提供启动入口

要求：

- 任何公共头文件变更都应该先更新契约测试。
- 契约测试不应该依赖某个具体芯片 SDK。
- 如果接口不兼容，PR 必须说明原因和迁移方式。

### `tests/integration`

`tests/integration` 后续用于放集成测试，用来验证多个框架层之间的协作。当前还没有真实集成测试，所以不保留空目录。

适合覆盖：

- `ep_framework_start()` 的启动顺序
- `ep_platform_boot()` 失败时是否停止启动
- `ep_framework_init()` 失败时是否阻止进入 `app_main()`
- core、components、OSAL/HAL、platform skeleton 的链接关系

集成测试可以比单元测试慢，但仍应能在 CI 中稳定运行。

### `tests/target_smoke`

`tests/target_smoke` 后续用于放目标环境冒烟测试，用于真实板子、RTOS SDK 或目标 Linux 环境。当前还没有目标板 runner，所以不保留空目录。

适合覆盖：

- 固件或目标程序能否启动
- 日志是否可用
- 基础 GPIO、UART、I2C、SPI 等驱动访问
- 最小 `app_main()` 路径是否能跑通

这类测试可能依赖硬件、串口、烧录器或专用 runner。等真实目标环境稳定后，再新增目录并接入 CI 的手动或专用 job。

## 模块化测试规则

每新增一个模块，都按以下顺序补测试：

1. 定义或更新公共头文件。
2. 在 `tests/api_contract` 中锁住接口契约。
3. 在 `tests/host_unit` 中覆盖平台无关逻辑。
4. 为 Linux port 增加最小可运行验证。
5. 为 RTOS port 保留 stub 或接入真实 SDK 验证。
6. 更新 CMake，使模块能被 CI 构建。

示例：新增 Linux `osal/time` 实现时，推荐文件边界为：

```text
osal/include/ep_osal_time.h
platforms/linux/demo_family/osal_port/ep_linux_time.c
tests/api_contract/test_osal_headers.py
tests/host_unit/test_linux_osal_time.py
```

## CI 最低验证

当前 PR 的最低自动化验证为：

```bash
pytest tests/host_unit tests/api_contract -v
cmake -S . -B build
cmake --build build
```

后续可以逐步增加：

- `clang-format --dry-run`
- `clang-tidy`
- sanitizer 构建
- Linux 平台集成测试
- 真实目标环境 smoke test

## 测试提交习惯

功能开发优先使用测试先行：

1. 先写失败的测试。
2. 确认失败原因符合预期。
3. 写最小实现让测试通过。
4. 跑完整相关测试。
5. 提交小而清晰的 commit。

对于纯文档或 CI 配置，也应该尽量有结构检查或命令检查，避免文件缺失、命令遗漏和流程漂移。
