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
- 平台能力注册表第一版。
- 平台路径接口第一版。
- host/macOS 可运行入口。
- Linux 和 RTOS 平台边界占位。

### 通用组件

- `log`：日志组件，底层接入 EasyLogger。
- `config`：配置组件，支持 host 配置文件加载。
- `device`：设备管理组件，支持设备注册、按名字查询、按类型查询和状态读取。
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
- host 资源冒烟示例。

### 第三方库

- EasyLogger 作为日志后端。
- cJSON v1.7.19 源码快照。
- SQLite 3.53.1 amalgamation 源码快照。
- LVGL 9.1 host/macOS 预编译包。
- `lvgl-prebuilt-host-macos` 独立仓库负责 host LVGL 配置和产物。
- host 资源目录约定为 `resources/host`，图片、字体、主题分别放在对应子目录。

cJSON 和 SQLite 当前只作为第三方库目标接入，后续业务组件可以按需链接。

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

## 平台能力注册表

第一版平台能力注册表已经放在：

```text
platforms/include/ep_platform_capability.h
```

每个平台可以通过自己的静态能力表声明支持情况。当前 host/macOS 已经声明基础文件系统、配置持久化、日志和线程能力；如果构建时启用 SDL2/LVGL UI，则同时声明 LVGL、显示和触摸能力。

组件和应用可以通过 `ep_platform_has_capability()` 查询能力，避免后续到处写平台判断。

## 平台路径接口

第一版平台路径接口已经放在：

```text
platforms/include/ep_platform_paths.h
```

当前接口提供：

- 当前平台配置文件路径。
- 当前平台资源根目录。
- 资源相对路径拼接。
- 图片、字体、主题路径拼接。

host/macOS 当前使用：

| 类型 | 路径 |
| --- | --- |
| 配置文件 | `config/profiles/host.cfg` |
| 资源根目录 | `resources/host` |
| 图片目录 | `resources/host/images` |
| 字体目录 | `resources/host/fonts` |
| 主题目录 | `resources/host/themes` |

这个接口只解决“当前平台资源在哪里”的问题，不直接负责加载图片、字体、主题，也不封装 LVGL API。

host/macOS 已经有独立的 `ep_host_resource_smoke` 冒烟程序，用来验证图片、字体、主题路径可以被程序打开并读取。

## 当前推荐方向

当前最适合继续补的是真实资源加载示例、资源工具脚本，或真实平台适配前的公共检查。

原因是平台能力注册表已经能表达“平台支持什么”，设备管理组件已经能表达“系统里有哪些设备”，平台路径接口已经能表达“资源和配置在哪里”，host 资源冒烟程序已经验证这些路径能被程序打开并读取。下一步如果要推进 UI，可以在 LVGL demo 里加载真实图片或字体；如果要推进工程化，可以做资源检查、拷贝或打包脚本。
