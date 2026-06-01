# 项目路线图

这份路线图用来说明项目接下来按什么顺序推进。它不是一次性做完的计划，而是帮助每次只选一个小块继续完善。

## 推进原则

- 先把 host/macOS 跑稳，再适配真实平台。
- 先做平台无关能力，再做厂商 SDK 对接。
- 先建立清楚的接口边界，再补具体实现。
- 每次只做一个小 PR，合并后同步文档和 Wiki。
- 主工程保留公共框架和预编译产物，不提交大型厂商 SDK。
- 不为远期想法预留空目录；需求明确并开始实现时再新增目录。

## 阶段 1：host 框架跑通

目标：让项目可以在 Mac 上持续编译、运行和测试。

当前状态：基本完成。

已完成内容：

- CMake 工程骨架。
- host/macOS 启动入口。
- 基础 OSAL POSIX 实现。
- 日志、配置、文件、事件、定时器、UI 组件。
- EasyLogger 接入。
- LVGL 9.1 host/macOS 静态库接入。
- LVGL demo 和 widgets demo。

后续只做小修小补，不作为当前主线。

## 阶段 2：平台能力注册表

目标：让每个平台能明确声明自己支持什么能力。

当前状态：第一版完成。

建议能力包括：

- 文件系统
- 配置持久化
- 日志输出
- LVGL
- 显示
- 触摸
- GPIO
- I2C
- SPI
- UART
- PWM
- ADC
- RTC
- 网络

完成后，应用层和组件层可以通过统一接口查询平台能力，而不是到处写平台判断。

第一版已经完成：

- 公共头文件 `platforms/include/ep_platform_capability.h`。
- 查询接口 `ep_platform_has_capability()`。
- 名称接口 `ep_platform_capability_name()`。
- host/macOS 静态能力表。

后续新增平台时，需要补对应平台自己的静态能力表。

## 阶段 3：设备管理组件

目标：建立统一设备管理入口，为后续真实硬件适配做准备。

当前状态：第一版完成。

第一版已经完成：

- 设备类型定义。
- 设备注册。
- 设备查找。
- 设备能力查询。
- 设备状态记录。

当前仍然不做真实驱动，不提供 open/read/write/ioctl。

## 阶段 4：平台配置和资源管理

目标：让不同平台可以更清楚地管理自己的配置、资源路径和第三方库。

当前状态：第一版完成。

第一版已经完成：

- 平台配置文件规范。
- 本地资源目录规范。
- 图片、字体、主题资源路径规范。
- host 和目标板的配置差异说明。
- 平台路径公共接口 `platforms/include/ep_platform_paths.h`。
- host/macOS 路径实现。
- `resources/common` 和 `resources/host` 目录边界。
- host 资源使用冒烟示例。

当前只定义路径、目录和最小读取冒烟，不做资源扫描、图片解码、字体加载或 LVGL 对象封装。

后续可以继续补：

- 真实资源加载示例。
- 真实平台资源目录命名规则。
- 资源检查、打包或拷贝脚本。
- 发布和打包流程。
- 平台差异整理。

这个阶段可以和 UI 业务开发交替进行。

## 阶段 5：真实平台适配

目标：开始接入具体芯片平台。

建议顺序：

1. 匠芯创 Luban Lite：
   - 使用独立 SDK 仓库 `sdk-artinchip-luban-lite` 维护官方 Luban-Lite 和本项目入口。
   - 新增 `platforms/rtos/artinchip/luban_lite/`。
   - 新增第一个 target 描述文件，例如 `artinchip_d12x_demo68_nor`。
   - 主工程先导出 `out/ep/<target>/lib/libep_app_core.a`。
   - Luban-Lite SDK 链接该静态库并输出最终固件。
   - 做最小启动和冒烟测试。

2. 全志 Linux：
   - 新增 `platforms/linux/tina/`。
   - 对接 Linux 文件系统、显示、触摸和输入输出。
   - 接入单独仓库维护的 LVGL 静态库。
   - 做最小启动和冒烟测试。

真实平台适配开始前，host 平台仍然作为主要验证环境。

## 阶段 6：业务组件和应用

目标：逐步补厨房项目真正需要的业务能力。

可能方向：

- 菜谱解析。
- 用户数据。
- 本地资源管理。
- 网络同步。
- 设备状态展示。
- UI 页面流程。
- cJSON 可用于菜谱 JSON、网络 JSON 和配置导入导出。
- SQLite 可用于用户数据、本地收藏、历史记录和状态缓存。

这些能力应尽量放在平台无关层，只有必须接触系统或硬件的部分才下沉到平台适配层。

## 当前下一步

当前建议下一步是：

```text
继续做小范围 host/macOS 验证，或者等真实需求明确后再新增组件
```

菜谱解析和用户数据暂时不急，因为菜谱格式和数据需求还没有完全确定。真实芯片平台也可以继续等板子和 SDK 环境更清楚后再开始。下一步更适合选择一个边界很小、能在 host/macOS 上验证的任务，例如资源工具脚本、真实资源加载示例，或某个已经明确的 UI/业务小能力。

发布、打包和平台差异相关规范见：

- `docs/development/release-and-packaging.md`
- `docs/porting/platform-differences.md`
- `docs/porting/platform-bringup-checklist.md`
- `docs/porting/rtos-sdk-library-model.md`
