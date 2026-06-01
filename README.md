# embedded-platform-core

一个面向 RTOS 和 Linux 的可移植嵌入式平台框架，保留原厂 SDK，并提供统一的 OS、驱动和组件抽象层。  
English: A portable embedded platform framework for RTOS and Linux, with unified OS, driver, and component abstractions.

## 工程定位

`embedded-platform-core` 的目标不是替换原厂 SDK，也不是把所有平台细节揉成一套“万能大一统”实现，而是建立一层稳定的公共框架边界：

- RTOS 侧保留原厂 SDK、原厂启动链路和原厂 BSP
- Linux 侧走标准用户态接口，不引入“伪 vendor SDK”
- 应用层只面对统一接口，不直接碰平台差异
- 新平台接入时，尽量通过新增平台包完成，而不是修改上层业务代码

当前仓库已经完成基础骨架，当前重点是保持目录简洁，用 host/macOS 继续验证平台无关组件和平台适配边界。

## 设计目标

- 支持 `RTOS` 和 `Linux` 两类平台
- 保留 RTOS 原厂 SDK，不重写底层启动模型
- 提供统一的 `OSAL` 和 `HAL` 公共接口
- 将平台差异收口到 `platforms/*`
- 让应用和公共组件层尽量不感知芯片、OS、原厂接口差异
- 为后续增加芯片、SoC、板级配置和产品功能保留清晰扩展路径

## 总体架构

框架当前采用分层组织：

`app -> core -> components -> osal/hal -> platforms/* -> vendor sdk 或 linux standard interfaces`

### 架构框图

```mermaid
flowchart TD
    A[app<br/>应用层 / 产品逻辑]
    B[core<br/>框架启动与生命周期编排]
    C[components<br/>日志 配置 文件 事件 定时器 设备 UI]
    D[osal / hal<br/>统一 OS 抽象 / 驱动抽象]
    E1[platforms/rtos/*<br/>RTOS 平台适配包]
    E2[platforms/linux/*<br/>Linux 平台适配包]
    F1[vendor/*<br/>原厂 SDK / BSP 边界]
    F2[Linux 用户态标准接口<br/>pthread / socket / ioctl / 文件系统]

    A --> B
    B --> C
    C --> D
    D --> E1
    D --> E2
    E1 --> F1
    E2 --> F2
```

### 启动路径

RTOS 侧：

```text
vendor startup / RTOS main
-> platforms/rtos/.../startup/app_start.c
-> ep_framework_start()
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

Linux 侧：

```text
platforms/linux/.../startup/main.c
-> ep_framework_start()
-> ep_platform_boot()
-> ep_framework_init()
-> app_main()
```

## 当前已落地内容

当前仓库已经完成了第一阶段骨架化工作：

- 顶层 CMake 构建入口
- `core/` 与 `app/` 的最小启动骨架
- `osal/` 公共头文件面
- `hal/` 公共头文件面
- host/macOS 可运行入口和 POSIX OSAL 实现
- 日志、配置、文件、事件、定时器、设备、UI 组件
- EasyLogger、cJSON、SQLite 和 LVGL 第三方库接入
- `platforms/rtos/demo_family` 平台样板
- `platforms/linux/demo_family` 平台样板
- GitHub `PR / Issue / CI / CODEOWNERS` 基础设施
- 对应的 host 单元测试和 API 契约测试

## 目录结构

当前仓库主结构如下：

```text
embedded-platform-core/
├── .github/
├── app/
│   └── include/
├── cmake/
│   ├── modules/
│   ├── presets/
│   └── toolchains/
├── components/
│   ├── config/
│   ├── device/
│   ├── event/
│   ├── file/
│   ├── log/
│   ├── timer/
│   └── ui/
├── config/
│   ├── common/
│   ├── feature/
│   └── profiles/
├── core/
│   ├── include/
│   └── src/
├── docs/
│   ├── architecture/
│   ├── decisions/
│   ├── porting/
│   ├── testing/
│   └── superpowers/
├── hal/
│   └── include/
├── osal/
│   └── include/
├── platforms/
│   ├── linux/
│   │   ├── common/
│   │   └── demo_family/
│   └── rtos/
│       ├── common/
│       └── demo_family/
├── tests/
│   ├── api_contract/
│   └── host_unit/
├── third_party/
│   ├── external/
│   └── prebuilt/
├── tools/
│   ├── ci/
│   └── scripts/
└── vendor/
```

## 关键目录说明

### `app/`

应用入口和产品逻辑。

约束：

- 不直接包含原厂 SDK 头文件
- 不直接包含 Linux 平台原生头文件
- 不写平台相关 `#ifdef`

### `core/`

框架启动和生命周期编排。

当前关键接口：

- `ep_framework_init()`
- `ep_framework_start()`

### `components/`

跨平台公共组件层。当前只保留已有实现或近期明确维护的组件；网络、菜谱解析、用户数据这类远期方向需要时再新建目录。

### `osal/`

公共 OS 抽象层，当前已建立以下头文件：

- `ep_osal_types.h`
- `ep_osal_err.h`
- `ep_osal_thread.h`
- `ep_osal_mutex.h`
- `ep_osal_sem.h`
- `ep_osal_queue.h`
- `ep_osal_time.h`
- `ep_osal_mem.h`

### `hal/`

公共硬件抽象层，当前已建立以下头文件：

- `ep_hal_types.h`
- `ep_hal_err.h`
- `ep_hal_gpio.h`
- `ep_hal_uart.h`
- `ep_hal_i2c.h`
- `ep_hal_spi.h`
- `ep_hal_pwm.h`
- `ep_hal_adc.h`

### `platforms/`

平台差异收口层。

当前样板包：

- `platforms/rtos/demo_family`
- `platforms/linux/demo_family`

每个平台包包含：

- `startup/`
- `osal_port/`
- `hal_port/`
- `component_port/`
- `board/`
- `config/`

### `vendor/`

厂商 SDK 边界。主工程当前不提交大型 SDK，也不为暂未接入的 SDK 预留空子目录。

### `third_party/`

外部依赖位置，当前已有：

- `EasyLogger`
- `cJSON`
- `SQLite`
- `LVGL`

## 当前构建状态

当前骨架已经支持：

- 顶层 `cmake configure`
- `ep_core`
- `ep_app`
- host/macOS 可执行程序
- host 资源冒烟程序
- LVGL demo 和 widgets demo
- cJSON 和 SQLite 第三方库目标

说明：

- host/macOS 是当前主要运行平台
- RTOS 和 Linux 的 `demo_family` 当前用于保留平台边界，不代表真实芯片适配已经完成

## 当前测试覆盖

目前仓库中的测试主要覆盖“骨架正确性”和“公共头文件契约”：

- 仓库目录边界
- 顶层 CMake 构建骨架
- 框架启动骨架
- OSAL 公共头文件
- HAL 公共头文件
- host/macOS 平台实现
- 第三方库接入
- GitHub 工作流文件存在性

其中：

- OSAL / HAL 头文件测试已经强化到“可独立双重 include 并单独编译”的级别
- host 侧测试已经覆盖 `cmake configure + build` smoke 流程

## GitHub 工作流

当前仓库已包含：

- `CODEOWNERS`
- Pull Request 模板
- Issue 模板
- GitHub Actions CI 骨架

当前 CI 运行：

```bash
pytest tests/host_unit tests/api_contract -v
```

## 当前约束

- 语言为标准 C
- Linux 仅做用户态框架
- RTOS 侧保留原厂 SDK / BSP / startup
- 当前仍不是完整产品级适配
- `demo_family` 只是占位平台包，后续要替换成真实平台
- 不为远期想法预留空目录；需要实现网络、菜谱解析、用户数据、真实目标冒烟测试时，再新增对应目录

## 后续建议

下一阶段最实际的推进顺序：

1. 继续用 host/macOS 做小范围验证。
2. 在真实需求明确后，再新增网络、菜谱解析或用户数据组件。
3. 板子和 SDK 环境明确后，再新增真实平台目录。
4. 真实平台起来后，再补目标机 smoke 覆盖。

## 设计与计划文档

设计和实施计划保存在：

- `docs/superpowers/specs/`
- `docs/superpowers/plans/`

这些文档记录了当前仓库的架构思路、边界约束和骨架实现顺序。

常用规范入口：

- `docs/architecture/project-overview.md`：项目总览。
- `docs/architecture/repository-layout.md`：仓库目录边界。
- `docs/development/release-and-packaging.md`：发布和打包流程。
- `docs/porting/platform-differences.md`：平台差异整理。
- `docs/porting/platform-bringup-checklist.md`：平台移植检查清单。
