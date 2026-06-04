# 平台移植文档入口

本目录是平台移植、兼容层 API 和真实板级适配记录的源头。GitHub Wiki 只作为阅读入口和阶段性总结，详细接口语义以本目录为准。

## 文档索引

| 文档 | 内容 |
| --- | --- |
| `platform-differences.md` | 平台差异归属，说明 OS、硬件、启动、资源、能力表和厂商 SDK 分别放在哪里。 |
| `platform-bringup-checklist.md` | 新增真实平台时的执行清单。 |
| `rtos-sdk-library-model.md` | RTOS SDK 静态库接入模型，说明主工程和厂商 SDK 的边界。 |
| `luban-lite-compatibility-overview.md` | Luban-Lite 兼容层总览，说明 app、framework、OSAL、HAL、设备层和 SDK 的关系。 |
| `osal-api-reference.md` | OSAL API 参考，记录线程、锁、队列、信号量、时间和内存接口的参数、返回值和平台语义。 |
| `hal-api-reference.md` | HAL API 参考，记录 GPIO、UART、I2C、SPI、PWM、ADC 接口契约和当前实现状态。 |
| `device-compatibility-reference.md` | 设备兼容层说明，记录逻辑设备名、设备注册表、平台能力和 KI 板设备映射。 |
| `luban-lite-build-and-link.md` | Luban-Lite 构建和链接流程，说明 `libep_app_core.a` 如何进入最终镜像。 |
| `ki-141103-480p-smoke-test.md` | KI-141103-480p 板级冒烟测试手册。 |

## 维护规则

- 业务代码只依赖 `ep_*` 公共接口，不直接包含 RT-Thread 或 Luban-Lite 头文件。
- OS 差异收口到 OSAL，硬件差异收口到 HAL 和设备兼容层。
- 板级 pinmux、defconfig、SCons、镜像打包继续归 SDK 仓库维护。
- 文档中的“当前状态”必须和代码一致；未实现能力要明确标注为后续扩展。
- 每次改接口、返回值、设备名或板级映射时，同步更新本目录文档。
