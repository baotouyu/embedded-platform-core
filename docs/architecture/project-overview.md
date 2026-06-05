# 项目总览

`embedded-platform-core` 是一个跨平台嵌入式应用框架工程。

这个工程的目标不是一开始就绑定某一个芯片 SDK，而是先把应用层、框架组件、操作系统抽象、硬件抽象、平台适配和第三方库管理分清楚。这样后续适配 host/macOS、匠芯创 Luban Lite、全志 Linux 或其他平台时，应用逻辑可以尽量保持稳定。

## 当前项目是什么

当前项目是一个跨平台嵌入式框架雏形，已经具备 host/macOS 本机开发验证能力，并且已经跑通匠芯创 D12x + Luban-Lite + KI-141103-480p 真实板级基础适配。

它目前适合做这些事情：

- 在 Mac 上验证框架启动流程。
- 在 Mac 上验证通用组件行为。
- 在真实 KI-141103-480p 板上验证 RT-Thread OSAL、HAL 和业务入口。
- 在平台边界稳定后继续开发平台无关业务代码。
- 管理 EasyLogger、LVGL 这类第三方库的接入方式。

它目前还不是完整产品工程，但平台层已经具备进入业务开发的基础条件。

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
third_party / 外部 SDK 仓库
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
| 外部 SDK 仓库 | 厂商 SDK 单独管理；RTOS 平台由主工程导出静态库给 SDK 链接。 |

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
- D12x/Luban-Lite target 描述和真实 SDK 构建链路。
- KI-141103-480p 板级基础适配。

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

### D12x/Luban-Lite 平台

- 主工程 target：`targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml`。
- SDK adapter：`third_party/sdk/sdk-artinchip-luban-lite/`。
- 业务入口：`app/main.c`。
- framework 生命周期：`core/src/ep_framework.c`。
- RT-Thread OSAL：`platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c`。
- RT-Thread HAL：`platforms/rtos/demo_family/hal_port/`。
- 默认逻辑设备：`platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c`。
- 固件输出：`out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/`。

当前 KI 板已经完成镜像构建、烧录启动、`app/main.c` 链接、UART/PWM/GPIO/I2C/RTC 真实 port 和主要板级冒烟。display/touch 归每个芯片自己的 LVGL display/input port；SD 卡文件系统使用 SDK 已有能力；SPI/ADC 业务暂时不用，按需再补。

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
| `docs/porting/` | 平台移植、兼容层 API、SDK 接入和板级冒烟测试。 |
| `docs/superpowers/specs/` | 具体功能的设计记录。 |
| `docs/superpowers/plans/` | 具体功能的执行计划。 |
| GitHub Wiki | 中文总览、当前进度、快速入口。 |

## 当前不做什么

为了让工程稳步推进，当前阶段暂时不做这些事情：

- 不把大型厂商 SDK 提交进主仓库。
- 不在主仓库直接维护所有平台的 LVGL 源码配置。
- 不为了“完整”补当前业务不用的 SPI、ADC。
- 不在 EP HAL 中二次封装 display/touch。
- 不为 SD 卡文件系统另封一套 EP SD HAL。
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

当前已经确定并跑通 RTOS 平台接入方向：主工程编译成 `libep_app_core.a` 静态库包，芯片 SDK 仓库负责链接、打包和输出最终固件。不同芯片和板子通过 target 描述文件管理，不把大型 SDK 或板级 BSP 直接放进主工程。

RTOS SDK 静态库接入模型见：

- `docs/porting/rtos-sdk-library-model.md`

原因是平台能力注册表已经能表达“平台支持什么”，设备管理组件已经能表达“系统里有哪些设备”，平台路径接口已经能表达“资源和配置在哪里”，RTOS SDK 静态库模型已经验证 `app/main.c` 可以进入最终镜像。下一步应优先整理业务应用结构，而不是继续补当前业务不用的底层外设。
