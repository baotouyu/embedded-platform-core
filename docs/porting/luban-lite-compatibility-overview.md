# Luban-Lite 兼容层总览

本文记录 `embedded-platform-core` 接入匠芯创 Luban-Lite 后的兼容层边界。目标是让业务代码只依赖 EP 公共接口，不直接绑定 RT-Thread、Luban-Lite 或具体板级 pinmux。

## 分层关系

```text
app/main.c 和后续业务模块
  -> core/src/ep_framework.c
    -> components/: log/config/event/timer/device/file/ui
      -> OSAL: osal/include/
      -> HAL: hal/include/
      -> device registry: components/device/include/ep_device.h
        -> platforms/rtos/demo_family/*_port/
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

- 应用层和公共业务逻辑，当前入口是 `app/main.c`。
- framework 生命周期，当前实现在 `core/src/ep_framework.c`。
- OSAL 公共接口，当前头文件在 `osal/include/`。
- HAL 公共接口，当前头文件在 `hal/include/`。
- 设备注册表公共接口，当前头文件在 `components/device/include/ep_device.h`。
- host 和真实平台可复用的组件实现。
- target 描述文件，例如 `targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml`。
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
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/helloworld/main.c
  -> third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/ep_app_main.c
    -> ep_lubanlite_app_main()
      -> core/src/ep_framework.c: ep_framework_start()
        -> ep_platform_boot()
        -> ep_framework_init()
        -> app/main.c: app_main()
```

`application/rt-thread/ep_app/` 是构建时 staging 目录，由 `third_party/sdk/sdk-artinchip-luban-lite/scripts/build_firmware.sh` 复制生成，不作为主工程业务源码维护。

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

## 现在写业务时该用什么

业务代码优先从 `app/main.c` 拆模块，不直接落到 SDK 目录。当前建议使用的公共接口如下：

| 能力 | 业务应包含的头文件 | 当前状态 |
| --- | --- | --- |
| 日志 | `components/log/include/ep_log.h` | 已接入 EasyLogger 和 RT-Thread console。 |
| 时间和 sleep | `osal/include/ep_osal_time.h` | 已接入 RT-Thread tick 和 sleep。 |
| 内存 | `osal/include/ep_osal_mem.h` | 已接入 `rt_malloc/rt_free`。 |
| 线程 | `osal/include/ep_osal_thread.h` | 已支持 create/join，join 等待线程自然退出。 |
| mutex | `osal/include/ep_osal_mutex.h` | 已接入 RT-Thread mutex。 |
| semaphore | `osal/include/ep_osal_sem.h` | 已接入 RT-Thread semaphore。 |
| queue | `osal/include/ep_osal_queue.h` | 已接入 RT-Thread message queue。 |
| UART | `hal/include/ep_hal_uart.h` | `console_uart`、`power_uart` 已可用。 |
| PWM | `hal/include/ep_hal_pwm.h` | `beep_pwm` 已可用，默认 2700 Hz 蜂鸣器。 |
| GPIO | `hal/include/ep_hal_gpio.h` | `lcd_sleep_gpio`、`panel_enable_gpio` 已可用。 |
| I2C | `hal/include/ep_hal_i2c.h` | `rtc_bus` 已可用。 |
| RTC | `hal/include/ep_hal_rtc.h` | `rtc -> PCF8563` 已可用。 |
| 文件读写 | SDK/RT-Thread 文件系统 API | SD 卡文件系统由 SDK 负责，业务可按平台已提供的 `open/read/write` 路线使用。 |
| UI | LVGL API | D12x/Luban-Lite 的 `ui.lvgl_provider=sdk`，LVGL、显示和触摸 port 由原厂 SDK 提供；EP 只管理公共 UI 生命周期，不封 display/touch HAL。 |

## 当前推进结论

当前平台适配可以认为完成了“能写业务”的基础条件：

1. `./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p` 能进入 Luban-Lite 真实构建。
2. `app/main.c` 已经链接进最终镜像，`EP_LOGI` 能从串口打印。
3. OSAL 基础能力已经覆盖常用业务线程、同步和消息队列场景。
4. KI 板当前需要的 UART/PWM/GPIO/I2C/RTC 已有真实 HAL port。
5. display/touch 交给平台 LVGL port，避免 EP 重复封一层低价值 API。
6. SD 卡文件系统能力由 Luban-Lite/RT-Thread 提供，业务层需要文件读写时直接按平台文件系统能力使用。

## LVGL 归属规则

`targets/<target>.yaml` 的 `ui.lvgl_provider` 是判断 LVGL 放在哪里的唯一入口。

当前 D12x/Luban-Lite 使用：

```yaml
ui:
  lvgl_provider: sdk
  lvgl_note: Luban-Lite SDK provides LVGL display and input ports.
```

这表示 LVGL 源码、`lv_conf.h`、显示刷新、触摸输入和硬件加速配置都归 Luban-Lite SDK 维护。主工程不把这套 LVGL 复制进 `components/`，也不在 EP HAL 中再封 display/touch。业务需要写 UI 时，按 Luban-Lite 暴露的 LVGL API 和工程习惯编写。

Linux 芯片如果没有这种原厂 RTOS SDK 集成，可以使用 `ui.lvgl_provider=component` 或 `prebuilt`。例如 F133/Tina Linux 可以用芯片专属 LVGL 仓库维护 framebuffer、输入、G2D 加速、旋转和交叉编译规则，再由主工程按组件或预编译依赖消费。
7. SPI、ADC 当前不作为主线任务，等业务确实用到再补对应 port 和冒烟测试。
8. 电源板 UART2 的硬件通道已经打开，协议层后续在业务模块或专用组件里实现。

线程停止约定：

- `ep_thread_join()` 只等待线程入口自然返回。
- 当前没有强制 stop API，也不使用 `rt_thread_delete()` 强杀业务线程。
- 需要停止后台线程时，通过 stop 标志、事件或队列消息通知线程自行退出，然后再 join。

详细 API 说明见：

- `osal-api-reference.md`
- `hal-api-reference.md`
- `device-compatibility-reference.md`
