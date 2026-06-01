# 平台差异整理

本文说明不同平台的差异应该放在哪里，避免业务代码、平台代码、厂商 SDK 和第三方库互相混在一起。

## 总原则

- 应用层和公共组件尽量保持平台无关。
- 平台差异收口到 `platforms/`、`osal/`、`hal/`、`config/`、`resources/` 和 `third_party/prebuilt/`。
- 厂商 SDK 保持自己的构建和目录习惯，主工程只保留边界和适配代码。
- 能用公共接口表达的差异，不在业务代码里写平台判断。

## 差异归属表

| 差异类型 | 放置位置 | 说明 |
| --- | --- | --- |
| OS 差异 | `osal/include` 和 `platforms/<family>/<platform>/osal_port` | 线程、互斥锁、信号量、队列、时间、内存等系统能力。 |
| 硬件差异 | `hal/include` 和 `platforms/<family>/<platform>/hal_port` | GPIO、I2C、SPI、UART、PWM、ADC 等硬件能力。 |
| 启动差异 | `platforms/<family>/<platform>/startup` | main、RTOS app entry、SDK 启动挂接。 |
| LVGL 差异 | `third_party/prebuilt/lvgl/<platform>` 和平台 UI port | 每个平台可以使用不同显示、输入、文件系统和图片解码配置。 |
| 资源路径差异 | `platforms/include/ep_platform_paths.h` 和平台 paths 实现 | 当前平台配置文件、资源根目录、图片、字体、主题路径。 |
| 能力差异 | `platforms/include/ep_platform_capability.h` 和平台能力表 | 用统一接口表达平台是否支持文件系统、LVGL、显示、触摸、网络等能力。 |
| 配置差异 | `config/profiles/<platform>.cfg` | 平台启动参数、功能开关和少量运行配置。 |
| 厂商 SDK | `vendor/` 边界和外部 SDK 工作区 | 主工程不提交大型厂商 SDK。 |

## OS 差异

OS 差异包括：

- 时间。
- 内存。
- 线程。
- 互斥锁。
- 信号量。
- 队列。

公共头文件放在：

```text
osal/include/
```

具体平台实现放在：

```text
platforms/host/posix/osal_port/
platforms/rtos/luban_lite/osal_port/
platforms/linux/tina/osal_port/
```

应用和组件只包含 OSAL 公共头文件，不直接包含 `pthread.h`、RT-Thread 或厂商 SDK 头文件。

## 硬件差异

硬件差异包括：

- GPIO。
- I2C。
- SPI。
- UART。
- PWM。
- ADC。

公共头文件放在：

```text
hal/include/
```

具体平台实现放在：

```text
platforms/<family>/<platform>/hal_port/
```

当前阶段可以先保留 stub。真实平台适配时，再逐步替换成真实驱动实现。

## 启动差异

不同平台的启动方式不同：

- host/macOS 走普通 `main()`。
- Linux 平台走 Linux 用户态 `main()`。
- RTOS 平台可能由 SDK、任务入口或 RTOS app entry 调起。

启动入口放在：

```text
platforms/<family>/<platform>/startup/
```

启动入口负责进入框架生命周期，不应该把业务逻辑写在平台启动文件里。

## LVGL 差异

LVGL 差异主要来自：

- 显示驱动。
- 输入驱动。
- 文件系统接口。
- 图片解码能力。
- 字体能力。
- SDK 自带 LVGL 或独立预编译 LVGL。

主工程当前采用规则：

```text
third_party/prebuilt/lvgl/<platform>
```

每个平台维护自己的 LVGL 产物。主工程消费头文件、静态库和 manifest，不直接维护所有平台的 `lv_conf.h`。

## 资源路径差异

资源路径通过平台路径接口统一：

```text
platforms/include/ep_platform_paths.h
```

平台实现放在：

```text
platforms/<family>/<platform>/paths/
```

规则：

- host 可以返回 `resources/host`。
- Luban Lite 后续可以返回 SDK 文件系统、flash 分区或打包资源路径。
- 全志 Linux 后续可以返回应用安装目录或系统资源目录。
- 上层 UI 和组件不直接写死具体平台路径。

## 能力差异

能力差异通过平台能力注册表统一：

```text
platforms/include/ep_platform_capability.h
```

平台能力表放在：

```text
platforms/<family>/<platform>/capability/
```

例如：

- host/macOS 支持文件系统、配置持久化、日志、线程。
- 启用 LVGL 时，host/macOS 支持 LVGL、显示和触摸。
- 真实目标平台后续按实际硬件和 SDK 能力补表。

## 配置差异

配置差异放在：

```text
config/profiles/<platform>.cfg
```

配置文件解决“这个平台启动时用什么参数”的问题，不解决“平台代码在哪里”或“大型 SDK 怎么管理”的问题。

## 厂商 SDK

厂商 SDK 的规则：

- 主工程不提交大型厂商 SDK。
- `vendor/` 只保留边界。
- SDK 可以在外部目录、独立仓库或构建机环境中管理。
- 主工程只提交必要的适配代码、说明文档和小型配置样例。

这样做的目的是保持主工程轻量，也避免把不同平台的 SDK 习惯强行揉成一套目录。

