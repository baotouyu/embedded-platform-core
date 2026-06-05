# 平台移植文档入口

本目录是平台移植、兼容层 API 和真实板级适配记录的源头。GitHub Wiki 只作为阅读入口和阶段性总结，详细接口语义以本目录为准。

## 推荐阅读顺序

第一次看平台移植文档时，建议按下面顺序阅读：

| 顺序 | 文档 | 先看它的原因 |
| --- | --- | --- |
| 1 | `platform-differences.md` | 先理解平台差异应该放在哪里，避免业务代码、平台代码和 SDK 代码混在一起。 |
| 2 | `platform-bringup-checklist.md` | 再看新增真实平台时要按什么阶段推进。 |
| 3 | `rtos-sdk-library-model.md` | 理解 RTOS 平台为什么由主工程导出静态库、厂商 SDK 负责最终固件。 |
| 4 | `luban-lite-build-and-link.md` | 具体看 Luban-Lite 如何接收 `libep_app_core.a` 并生成镜像。 |
| 5 | `luban-lite-compatibility-overview.md` | 看 app、framework、OSAL、HAL、设备层和 Luban-Lite 的运行关系。 |
| 6 | `osal-api-reference.md` | 查 OS 兼容层 API 的参数、返回值、生命周期和 RT-Thread 映射。 |
| 7 | `hal-api-reference.md` | 查硬件驱动兼容层 API 的设备名、句柄、读写和当前实现状态。 |
| 8 | `device-compatibility-reference.md` | 查逻辑设备名、设备注册表、平台能力和 KI 板设备映射。 |
| 9 | `ki-141103-480p-smoke-test.md` | 最后按板级冒烟手册验证镜像、串口、RTC、LCD、触摸、蜂鸣器和 SD 卡。 |

## 按问题查文档

| 问题 | 应看文档 |
| --- | --- |
| 业务代码能不能直接调用 RT-Thread 或 Luban-Lite API？ | `luban-lite-compatibility-overview.md` |
| `build.sh` 怎么调用 SDK 生成固件？ | `luban-lite-build-and-link.md` |
| `ep_malloc`、`ep_thread_create`、`ep_queue_send` 怎么用？ | `osal-api-reference.md` |
| `ep_uart_open`、`ep_pwm_set`、`ep_i2c_read` 怎么用？ | `hal-api-reference.md` |
| `power_uart`、`beep_pwm`、`rtc` 这些逻辑设备名对应什么硬件？ | `device-compatibility-reference.md` |
| 板子烧录后怎么确认外设正常？ | `ki-141103-480p-smoke-test.md` |

## 维护规则

- 业务代码只依赖 `ep_*` 公共接口，不直接包含 RT-Thread 或 Luban-Lite 头文件。
- OS 差异收口到 OSAL，硬件差异收口到 HAL 和设备兼容层。
- 板级 pinmux、defconfig、SCons、镜像打包继续归 SDK 仓库维护。
- 文档中的“当前状态”必须和代码一致；未实现能力要明确标注为后续扩展。
- 每次改接口、返回值、设备名或板级映射时，同步更新本目录文档。
