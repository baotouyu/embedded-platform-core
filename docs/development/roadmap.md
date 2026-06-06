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

设备管理组件本身仍然只做注册和查询，不直接提供 open/read/write/ioctl。真实硬件访问通过 HAL 或平台 SDK 能力完成；当前 KI 板已经在 RTOS port 中接入 UART/PWM/GPIO/I2C/RTC。

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
   - 对接 Linux 文件系统和输入输出。
   - 接入单独仓库维护的 LVGL 静态库。
   - 显示和触摸由 Tina/Linux 平台自己的 LVGL display/input port 负责，不在 EP HAL 中二次封装。
   - 做最小启动和冒烟测试。

当前 D12x/Luban-Lite/KI-141103-480p 已经完成基础真实平台适配。host 平台仍然作为平台无关组件的主要验证环境，真实板用于验证 SDK 构建、OSAL/HAL port 和板级行为。

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
进入具体业务协议和业务模块开发，优先从 app/services/ 已有边界往下接
```

KI-141103-480p 已经完成基础板级启动、镜像构建、`app/main.c` 链接、RT-Thread OSAL、UART/PWM/GPIO/I2C/RTC 真实 port 和主要板级冒烟。display/touch 由各芯片 LVGL port 负责；SD 卡文件系统走 SDK 已有能力；SPI/ADC 当前业务暂时不用，按需再补。

应用入口已经拆成基础业务骨架：

- `app/main.c`：只保留 `app_main()` 薄入口。
- `app/app_core.c`：管理应用上下文、服务启动顺序和主流程收口。
- `app/selftest/app_selftest.c`：保留当前 timer/event 生命周期冒烟，确保 framework 到 app 的链路可验证。
- `app/services/`：建立蜂鸣器、RTC、LCD sleep、电源板 UART 的业务服务边界。

后续主线建议：

1. 电源板 UART2 协议按实际帧格式单独实现。
2. 明确后续业务模块边界，例如 UI 页面流程、配置、用户数据、资源加载。
3. 蜂鸣器、RTC、LCD sleep 服务在真实业务第一次调用时补具体 HAL 操作和板级冒烟。
4. 需要后台任务时，使用 OSAL thread + queue/sem/event，线程通过显式退出协议自然结束后再 join。
5. 每增加一个真实业务能力，同步补 API 文档、板级验证步骤和 Wiki。

发布、打包和平台差异相关规范见：

- `docs/development/release-and-packaging.md`
- `docs/porting/app-business-skeleton.md`
- `docs/porting/platform-differences.md`
- `docs/porting/platform-bringup-checklist.md`
- `docs/porting/rtos-sdk-library-model.md`
