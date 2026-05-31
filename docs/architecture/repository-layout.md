# 仓库目录说明

这份文档说明主工程目录边界。后续整理目录、适配新平台、接入第三方库时，优先按这里的职责放置文件。

## 顶层目录

| 目录 | 职责 |
| --- | --- |
| `app/` | 平台无关的应用入口和业务流程。这里不能直接包含 Linux、RTOS、macOS 或厂商 SDK 头文件。 |
| `core/` | 框架启动、生命周期和公共编排逻辑。这里负责把组件按顺序初始化起来。 |
| `components/` | 可复用框架组件，例如日志、配置、文件、事件、定时器、UI。组件公共头文件必须保持平台无关。 |
| `osal/` | OS 抽象层公共接口，例如时间、内存、线程、互斥锁、信号量、队列。 |
| `hal/` | 硬件抽象层公共接口，例如 GPIO、I2C、SPI、UART、PWM、ADC。 |
| `platforms/` | 平台公共接口和平台适配代码。真实平台、host 调试平台、Linux 平台、RTOS 平台都在这里实现公共接口。 |
| `config/` | 默认配置、功能开关配置和运行配置样例。 |
| `cmake/` | CMake 模块、工具链文件和构建选项。 |
| `tests/` | host 单元测试、API 契约测试、集成测试和目标板冒烟测试。 |
| `docs/` | 中文设计、流程、移植和测试文档。 |
| `tools/` | 辅助脚本和 CI 工具。 |
| `examples/` | 面向使用者的独立样例。当前可以为空，业务 demo 优先放在对应平台目录。 |
| `third_party/` | 第三方源码或预编译包。 |
| `vendor/` | 厂商 SDK 放置位置。主工程当前不提交大型 SDK，只保留目录边界。 |

## 第三方目录

`third_party/external/` 放第三方源码快照，例如 EasyLogger。这里可以包含少量为了主工程编译必须保留的本地 port 文件。

`third_party/prebuilt/` 放预编译包，例如：

```text
third_party/prebuilt/lvgl/host_macos
```

预编译包必须包含头文件、静态库和 manifest。主工程只消费这些产物，不在这里直接改第三方库配置。

不要直接修改预编译包里的 lv_conf.h。正式修改 LVGL 配置时，先去对应的 `lvgl-prebuilt-*` 仓库修改源头配置并重新产包，再同步回主工程。

## 平台目录

`platforms/include/` 放平台公共接口，例如平台能力注册表。组件和应用需要了解平台能力时，优先包含这里的公共头文件，不直接包含具体平台目录里的头文件。

`platforms/host/posix/` 是本机调试平台，目前负责 macOS host 程序和 SDL2/LVGL demo。

`platforms/linux/demo_family/` 和 `platforms/rtos/demo_family/` 是早期占位平台，用来验证 Linux/RTOS 平台边界和 CMake 接入方式。真实芯片适配时，应新增具体平台目录，例如：

```text
platforms/rtos/luban_lite/
platforms/linux/tina/
```

## 组件目录

已经实现的组件需要有：

```text
components/<name>/include
components/<name>/src
components/<name>/CMakeLists.txt
```

尚未实现的方向可以保留空目录和 `.gitkeep`，但不要在空目录里放临时文件。网络、菜谱解析、用户数据等后续功能可以按这个规则逐步补齐。

## 本地生成文件

以下内容是本地生成或工具缓存，不应该提交：

```text
build/
.worktrees/
.pytest_cache/
__pycache__/
.DS_Store
```

如果这些文件出现在工作区，优先清理本地文件或补充 `.gitignore`，不要把它们混进功能提交。
