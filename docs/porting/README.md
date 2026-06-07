# 平台移植文档入口

本目录是平台移植、兼容层 API 和真实板级适配记录的源头。GitHub Wiki 只作为阅读入口和阶段性总结，详细接口语义以本目录为准。

## 先看结论

当前 D12x + Luban-Lite + KI-141103-480p 平台基础适配已经完成，可以开始写业务代码。业务入口在 `app/main.c`，应用生命周期在 `app/app_core.c`，当前自检在 `app/selftest/app_selftest.c`，LVGL 页面入口在 `app/ui/app_ui.c`，最终会通过 `libep_app_core.a` 链接进 Luban-Lite 镜像。

当前已经确认的边界：

- OSAL、HAL 和设备兼容层是业务代码访问系统和硬件的入口。
- LVGL 页面代码写在 `app/ui/`，Mac host 和 AIC Luban-Lite 编译共用源码。
- UART、PWM、GPIO、I2C、RTC 已有 RT-Thread/Luban-Lite 真实 port。
- D12x/Luban-Lite 的 `ui.lvgl_provider=sdk`，display/touch 和 LVGL port 由原厂 SDK 负责，EP 不二次封装。
- Linux 芯片如果没有原厂 SDK 内置 LVGL，可以使用芯片专属 LVGL 组件仓库，例如 F133 的 `sunxi_lvgl_v9.1`。
- SD 卡文件系统使用 Luban-Lite/RT-Thread 已提供的文件系统能力，业务需要时按 SDK 的 `open/read/write` 方式读写。
- SPI、ADC 当前业务暂时不用，保持公共接口，等真实需求出现再补 port。
- 电源板 UART2 硬件通道已打开，协议后续按业务协议单独实现。

## 推荐阅读顺序

第一次看平台移植文档时，建议按下面顺序阅读：

| 顺序 | 文档 | 先看它的原因 |
| --- | --- | --- |
| 1 | `platform-differences.md` | 先理解平台差异应该放在哪里，避免业务代码、平台代码和 SDK 代码混在一起。 |
| 2 | `platform-bringup-checklist.md` | 再看新增真实平台时要按什么阶段推进。 |
| 3 | `rtos-sdk-library-model.md` | 理解 RTOS 平台为什么由主工程导出静态库、厂商 SDK 负责最终固件。 |
| 4 | `luban-lite-build-and-link.md` | 具体看 Luban-Lite 如何接收 `libep_app_core.a` 并生成镜像。 |
| 5 | `luban-lite-compatibility-overview.md` | 看 app、framework、OSAL、HAL、设备层和 Luban-Lite 的运行关系。 |
| 6 | `app-business-skeleton.md` | 看现在业务入口、应用上下文、自检、服务边界和 `app/ui` 页面入口怎么写。 |
| 7 | `osal-api-reference.md` | 查 OS 兼容层 API 的参数、返回值、生命周期和 RT-Thread 映射。 |
| 8 | `hal-api-reference.md` | 查硬件驱动兼容层 API 的设备名、句柄、读写和当前实现状态。 |
| 9 | `device-compatibility-reference.md` | 查逻辑设备名、设备注册表、平台能力和 KI 板设备映射。 |
| 10 | `ki-141103-480p-smoke-test.md` | 最后按板级冒烟手册验证镜像、串口、RTC、LCD、触摸、蜂鸣器和 SD 卡。 |

## 关键文件路径

| 内容 | 路径 |
| --- | --- |
| 业务入口 | `app/main.c` |
| 业务入口头文件 | `app/include/app_main.h` |
| 应用上下文 | `app/include/app_context.h` |
| 应用生命周期 | `app/app_core.c`、`app/include/app_core.h` |
| 应用自检 | `app/selftest/app_selftest.c`、`app/selftest/app_selftest.h` |
| 应用 UI 页面 | `app/ui/app_ui.c`、`app/ui/app_ui.h` |
| 业务骨架文档 | `docs/porting/app-business-skeleton.md` |
| 设备服务边界 | `app/services/` |
| framework 生命周期 | `core/src/ep_framework.c`、`core/include/ep_framework.h` |
| OSAL 公共头文件 | `osal/include/` |
| HAL 公共头文件 | `hal/include/` |
| 设备注册表公共头文件 | `components/device/include/ep_device.h` |
| RT-Thread OSAL port | `platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c` |
| RT-Thread HAL port | `platforms/rtos/demo_family/hal_port/` |
| RTOS 默认逻辑设备 | `platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c` |
| 主工程 target | `targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml` |
| SDK target env | `third_party/sdk/sdk-artinchip-luban-lite/targets/artinchip_d12x_lubanlite_ki_141103_480p.env` |
| SDK 构建脚本 | `third_party/sdk/sdk-artinchip-luban-lite/scripts/build_firmware.sh` |
| SDK staging 目录 | `third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/` |
| RT-Thread defconfig | `third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/target/configs/d12x_KI-141103-480p_rt-thread_helloworld_defconfig` |
| bootloader defconfig | `third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/target/configs/d12x_KI-141103-480p_baremetal_bootloader_defconfig` |
| 固件输出目录 | `out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/` |

## 按问题查文档

| 问题 | 应看文档 |
| --- | --- |
| 现在能不能开始写业务代码？ | `luban-lite-compatibility-overview.md`、`device-compatibility-reference.md` |
| 业务入口、服务初始化和自检顺序是什么？ | `app-business-skeleton.md` |
| 业务代码能不能直接调用 RT-Thread 或 Luban-Lite API？ | `luban-lite-compatibility-overview.md` |
| `build.sh` 怎么调用 SDK 生成固件？ | `luban-lite-build-and-link.md` |
| `ep_malloc`、`ep_thread_create`、`ep_queue_send` 怎么用？ | `osal-api-reference.md` |
| `ep_uart_open`、`ep_pwm_*`、`ep_i2c_read` 怎么用？ | `hal-api-reference.md` |
| `power_uart`、`beep_pwm`、`rtc` 这些逻辑设备名对应什么硬件？ | `device-compatibility-reference.md` |
| 板子烧录后怎么确认外设正常？ | `ki-141103-480p-smoke-test.md` |
| display/touch 和 LVGL 应该在哪里适配？ | `luban-lite-compatibility-overview.md`、`platform-differences.md` |
| Mac 写好的 LVGL 页面怎么进 AIC 镜像？ | `app-business-skeleton.md`、`luban-lite-compatibility-overview.md` |

## 维护规则

- 业务代码只依赖 `ep_*` 公共接口，不直接包含 RT-Thread 或 Luban-Lite 头文件。
- OS 差异收口到 OSAL，硬件差异收口到 HAL 和设备兼容层。
- 板级 pinmux、defconfig、SCons、镜像打包继续归 SDK 仓库维护。
- 文档中的“当前状态”必须和代码一致；未实现能力要明确标注为后续扩展。
- 每次改接口、返回值、设备名或板级映射时，同步更新本目录文档。
