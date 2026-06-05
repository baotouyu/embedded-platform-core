# Luban-Lite 兼容层总览

本文记录 `embedded-platform-core` 接入匠芯创 Luban-Lite 后的兼容层边界。目标是让业务代码只依赖 EP 公共接口，不直接绑定 RT-Thread、Luban-Lite 或具体板级 pinmux。

## 分层关系

```text
app/main.c 和业务模块
  -> framework / components
    -> OSAL: 内存、时间、线程、锁、信号量、队列
    -> HAL: GPIO、UART、I2C、SPI、PWM、ADC
    -> device registry: 逻辑设备名、设备状态、能力归属
      -> RT-Thread / Luban-Lite 驱动 / 板级配置
        -> KI-141103-480p 硬件
```

应用层只能调用 `ep_*` 接口。应用层不应该直接包含：

- `rtthread.h`
- Luban-Lite SDK 内部头文件
- BSP 驱动私有头文件
- 具体板级 pinmux 或 defconfig 细节

## 主工程职责

主工程负责：

- 应用层和公共业务逻辑。
- framework 生命周期。
- OSAL、HAL、components 的公共接口。
- host 和真实平台可复用的组件实现。
- target 描述文件。
- 生成 `libep_app_core.a`、头文件和 manifest。

主工程不负责：

- RTOS 启动代码。
- 链接脚本。
- 板级 pinmux。
- Luban-Lite defconfig。
- 固件镜像打包。
- 大型工具链和原厂 SDK 源码快照。

## SDK 仓库职责

`sdk-artinchip-luban-lite` 负责：

- 保存原厂 Luban-Lite SDK。
- 维护 KI-141103-480p 板级配置。
- 恢复原厂工具链目录。
- 接收主工程导出的 `libep_app_core.a` 和头文件。
- 通过 Luban-Lite 原厂构建系统生成最终固件。

当前 Luban-Lite 入口逻辑为：

```text
Luban-Lite helloworld main
  -> ep_lubanlite_app_main()
    -> ep_framework_start()
      -> ep_platform_boot()
      -> ep_framework_init()
      -> app_main()
```

## 当前已跑通的 KI 板基线

| 项目 | 当前状态 |
| --- | --- |
| target | `artinchip_d12x_lubanlite_ki_141103_480p` |
| defconfig | `d12x_KI-141103-480p_rt-thread_helloworld_defconfig` |
| bootloader defconfig | `d12x_KI-141103-480p_baremetal_bootloader_defconfig` |
| app 链接 | `app/main.c` 已进入最终镜像 |
| 日志 | `EP_LOG*` 通过 EasyLogger 和 RT-Thread console 输出 |
| 控制台串口 | UART1，PA2/PA3，115200 |
| 电源板串口 | UART2，PA4/PA5 |
| RTC | PCF8563，I2C1，PD4/PD5，EP RTC HAL 已接入 `rtc` |
| LCD | RGB 800x480 |
| 触摸 | GT911，800x480 坐标范围 |
| 蜂鸣器 | PWM1，PC7，默认 2700 Hz |
| 默认逻辑设备注册 | `console_uart`、`power_uart`、`beep_pwm`、`rtc_bus`、`rtc`、`lcd_sleep_gpio`、`panel_enable_gpio` |
| SD 卡 | SDMC1，boot 阶段单线 SD |

## 兼容层推进顺序

建议后续按以下顺序推进：

1. 固定接口契约：参数、返回值、生命周期、阻塞语义。
2. RT-Thread OSAL 已支持 thread create/join；join 只等待线程入口自然返回，不提供强制 stop。
3. 需要停止后台线程时，通过 stop 标志、事件或队列消息让线程自行退出后再 join。
4. 为 KI 板继续补真实 HAL port，UART 已有 `console_uart` / `power_uart`，PWM 已有 `beep_pwm`，GPIO 已有 `lcd_sleep_gpio` / `panel_enable_gpio`，I2C 已有 `rtc_bus`，RTC 已有 `rtc -> PCF8563`。
5. LCD flush、触摸输入和 LVGL driver 由各芯片 SDK 或对应平台 LVGL port 负责，EP 不再另封 display/touch HAL。
6. 后续按需求继续补 SPI、ADC、SD 卡文件系统、电源板 UART 协议等真实设备能力。
7. 为每个真实设备补 Docker 构建验证和板级冒烟测试记录。

详细 API 说明见：

- `osal-api-reference.md`
- `hal-api-reference.md`
- `device-compatibility-reference.md`
