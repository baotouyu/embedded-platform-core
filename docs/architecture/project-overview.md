# 项目总览

`embedded-platform-core` 是一个跨平台嵌入式应用框架工程。

这个工程的目标不是一开始就绑定某一个芯片 SDK，而是先把应用层、框架组件、操作系统抽象、硬件抽象、平台适配和第三方库管理分清楚。这样后续适配 host/macOS、匠芯创 Luban Lite、全志 Linux 或其他平台时，应用逻辑可以尽量保持稳定。

## 当前项目是什么

当前项目是一个框架雏形，已经具备 host/macOS 本机开发和验证能力。

它目前适合做这些事情：

- 在 Mac 上验证框架启动流程。
- 在 Mac 上验证通用组件行为。
- 在没有目标板的情况下提前开发平台无关代码。
- 为后续真实芯片适配建立目录边界和接口边界。
- 管理 EasyLogger、LVGL 这类第三方库的接入方式。

它目前还不是完整产品工程，也还没有开始真实芯片平台适配。

## 分层结构

项目按下面的层次组织：

```text
app
  ↓
core
  ↓
components
  ↓
osal / hal
  ↓
platforms
  ↓
third_party / vendor
```

各层职责如下：

| 层级 | 职责 |
| --- | --- |
| `app/` | 平台无关的应用入口和业务流程。 |
| `core/` | 框架启动、生命周期和公共编排逻辑。 |
| `components/` | 可复用组件，例如日志、配置、文件、事件、定时器、UI。 |
| `osal/` | 操作系统抽象接口，例如时间、线程、互斥锁、信号量、队列。 |
| `hal/` | 硬件抽象接口，例如 GPIO、I2C、SPI、UART、PWM、ADC。 |
| `platforms/` | 具体平台适配，例如 host/macOS、Linux、RTOS、厂商平台。 |
| `third_party/` | 第三方源码快照或预编译包。 |
| `vendor/` | 厂商 SDK 边界。主工程不提交大型 SDK。 |

## 当前已经完成什么

### 工程流程

- 建立 GitHub PR 开发流程。
- 建立中文提交和中文 PR 内容习惯。
- 建立主仓库 `docs/` 和 GitHub Wiki 的分工。
- 建立基础 CI 和测试习惯。

### 基础框架

- CMake 工程骨架。
- `app/core/components/osal/hal/platforms` 分层。
- host/macOS 可运行入口。
- Linux 和 RTOS 平台边界占位。

### 通用组件

- `log`：日志组件，底层接入 EasyLogger。
- `config`：配置组件，支持 host 配置文件加载。
- `file`：文件组件，支持基础文件读写。
- `event`：事件总线。
- `timer`：软件定时器。
- `ui`：LVGL 生命周期组件。

### host/macOS 平台

- POSIX 时间、内存、线程、互斥锁、信号量、队列实现。
- host 框架启动程序。
- SDL2 UI port。
- LVGL 基础 demo。
- LVGL widgets demo。

### 第三方库

- EasyLogger 作为日志后端。
- LVGL 9.1 host/macOS 预编译包。
- `lvgl-prebuilt-host-macos` 独立仓库负责 host LVGL 配置和产物。

## 文档分工

主仓库 `docs/` 是详细记录的源头。

GitHub Wiki 是阅读入口和阶段性总结。

两者分工如下：

| 位置 | 用途 |
| --- | --- |
| `docs/architecture/` | 架构、目录、边界说明。 |
| `docs/development/` | 开发流程、测试策略、路线图。 |
| `docs/superpowers/specs/` | 具体功能的设计记录。 |
| `docs/superpowers/plans/` | 具体功能的执行计划。 |
| GitHub Wiki | 中文总览、当前进度、快速入口。 |

## 当前不做什么

为了让工程稳步推进，当前阶段暂时不做这些事情：

- 不把大型厂商 SDK 提交进主仓库。
- 不在主仓库直接维护所有平台的 LVGL 源码配置。
- 不急着适配真实设备驱动。
- 不大规模移动目录。
- 不把业务逻辑和平台代码混在一起。

## 当前推荐方向

当前最适合继续补的是平台能力注册表。

原因是不同平台支持能力会不一样。host/macOS、匠芯创 Luban Lite、全志 Linux 以后可能分别支持不同的文件系统、显示、触摸、网络、GPIO、RTC。先把平台能力声明清楚，后续组件和应用就不用到处写平台判断。
