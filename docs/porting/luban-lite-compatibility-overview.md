# Luban-Lite 兼容层总览

本文记录 `embedded-platform-core` 接入匠芯创 Luban-Lite 后的兼容层边界。目标是让业务代码只依赖 EP 公共接口，不直接绑定 RT-Thread、Luban-Lite 或具体板级 pinmux。

## 分层关系

```text
app/main.c 薄入口
  -> app/app_core.c
    -> app/selftest/app_selftest.c
    -> app/services/
    -> app/ui/
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

- 应用层和公共业务逻辑，当前入口是 `app/main.c`，生命周期收口在 `app/app_core.c`。
- 可复用的应用 LVGL 页面代码，当前入口是 `app/ui/app_ui.c`。
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
          -> ep_log_init()
          -> ep_config_init()
          -> ep_event_init()
          -> ep_timer_init()
          -> ep_device_init()
          -> ep_platform_register_default_devices()
        -> app/main.c: app_main()
          -> app_context_init()
          -> app_core_start()
          -> app_selftest_run()
          -> app_core_run()

third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/packages/artinchip/lvgl-ui/lv_demo.c
  -> lv_user_gui_init()
    -> ep_lubanlite_lvgl_app_ui_create()
      -> app/ui/app_ui.c: app_ui_create()
    -> 如果 EP UI 未接入或返回非 0，则回退 aic_ui_init()
```

`application/rt-thread/ep_app/` 是构建时 staging 目录，由 `third_party/sdk/sdk-artinchip-luban-lite/scripts/build_firmware.sh` 复制生成，不作为主工程业务源码维护。

应用业务骨架的详细文件路径、API 参数和返回值见 `app-business-skeleton.md`。

## 当前已跑通的 KI 板基线

| 项目 | 当前状态 |
| --- | --- |
| target | `artinchip_d12x_lubanlite_ki_141103_480p` |
| defconfig | `d12x_KI-141103-480p_rt-thread_helloworld_defconfig` |
| bootloader defconfig | `d12x_KI-141103-480p_baremetal_bootloader_defconfig` |
| app 链接 | `app/main.c`、`app/app_core.c`、`app/selftest/`、`app/services/`、`app/ui/` 已进入最终镜像 |
| 日志 | `EP_LOG*` 通过 EasyLogger 和 RT-Thread console 输出 |
| 控制台串口 | UART1，PA2/PA3，115200 |
| 电源板串口 | UART2，PA4/PA5 |
| RTC | PCF8563，I2C1，PD4/PD5，EP RTC HAL 已接入 `rtc` |
| LCD | RGB 800x480 |
| 触摸 | GT911，800x480 坐标范围 |
| 蜂鸣器 | PWM1，PC7，默认 2700 Hz |
| 默认逻辑设备注册 | `console_uart`、`power_uart`、`beep_pwm`、`rtc_bus`、`rtc`、`lcd_sleep_gpio`、`panel_enable_gpio` |
| SD 卡 | SDMC1，boot 阶段单线 SD |

## 当前 app 业务骨架

当前业务入口已经拆成四层：

| 层级 | 路径 | 职责 |
| --- | --- | --- |
| 薄入口 | `app/main.c` | 只编排 `app_context_init()`、`app_core_start()`、`app_selftest_run()`、`app_core_run()`。 |
| 应用上下文 | `app/include/app_context.h` | 保存跨服务共享的应用状态，当前有 `services_ready`。 |
| 生命周期 | `app/app_core.c` | 初始化业务服务，进入应用主流程。 |
| 自检 | `app/selftest/app_selftest.c` | 用 event/timer/sleep 验证 framework 到 app 的链路。 |
| 服务层 | `app/services/` | 提供蜂鸣器、RTC、LCD sleep、电源板 UART 的业务边界。 |
| 应用 UI | `app/ui/` | 提供 Mac 和目标平台共用的 LVGL 页面代码。 |

当前服务层已经完成第一批真实硬件动作。业务代码优先调用服务接口，服务层再通过 HAL 逻辑设备名访问目标板硬件；host/macOS 和 Linux demo 仍保留 stub 行为，用来保证同一份业务代码可以先在本机编译和跑生命周期。

| 服务 | 头文件 | 当前状态 |
| --- | --- | --- |
| 蜂鸣器 | `app/services/beep_service.h` | `beep_service_init()` 已可用；`beep_service_beep_ms(duration_ms)` 会打开 `beep_pwm`，输出 2700 Hz、50% 占空比 PWM，持续 `duration_ms` 毫秒后关闭。`duration_ms == 0` 返回 `EP_ERR_INVAL`。 |
| RTC | `app/services/rtc_service.h` | `rtc_service_init()` 已可用；`rtc_service_get_time(time)` 会打开 `rtc`，读取 PCF8563 日历时间并关闭。`time == NULL` 返回 `EP_ERR_INVAL`。 |
| LCD sleep | `app/services/lcd_sleep_service.h` | `lcd_sleep_service_init()` 会申请 `lcd_sleep_gpio` 并设置输出；`lcd_sleep_service_set_sleep(sleep_enabled)` 写 PD3，`0` 为低电平 wake，非 0 为高电平 sleep。 |
| 电源板 | `app/services/power_board_service.h` | `power_board_service_init()` 已可用；`power_board_service_write()` 目前返回 `EP_ERR_UNSUPPORTED`，协议待定义。 |

业务代码优先使用服务层接口。服务层确实需要访问硬件时，再调用 `hal/include/` 下的 HAL API 或 SDK 已提供能力。

## 现在写业务时该用什么

业务代码优先放在 `app/app_core.c`、`app/services/` 或后续新增业务模块，不直接落到 SDK 目录。`app/main.c` 只保留入口编排。当前建议使用的公共接口如下：

| 能力 | 业务应包含的头文件 | 当前状态 |
| --- | --- | --- |
| 日志 | `components/log/include/ep_log.h` | 已接入 EasyLogger 和 RT-Thread console。 |
| 时间和 sleep | `osal/include/ep_osal_time.h` | 已接入 RT-Thread tick 和 sleep。 |
| 内存 | `osal/include/ep_osal_mem.h` | 已接入 `rt_malloc/rt_free`。 |
| 线程 | `osal/include/ep_osal_thread.h` | 已支持 create/join，join 等待线程自然退出。 |
| mutex | `osal/include/ep_osal_mutex.h` | 已接入 RT-Thread mutex。 |
| semaphore | `osal/include/ep_osal_sem.h` | 已接入 RT-Thread semaphore。 |
| queue | `osal/include/ep_osal_queue.h` | 已接入 RT-Thread message queue。 |
| UART | `hal/include/ep_hal_uart.h` | `console_uart`、`power_uart` 已可用；电源板协议还未实现。 |
| PWM | `app/services/beep_service.h`，底层才用 `hal/include/ep_hal_pwm.h` | 业务蜂鸣器动作调用 `beep_service_beep_ms()`；底层映射 `beep_pwm -> PWM1/PC7`，默认 2700 Hz。 |
| GPIO | `app/services/lcd_sleep_service.h`，底层才用 `hal/include/ep_hal_gpio.h` | 业务 LCD 休眠调用 `lcd_sleep_service_set_sleep()`；底层映射 `lcd_sleep_gpio -> PD3`。`panel_enable_gpio` 已在 HAL 可用。 |
| I2C | `hal/include/ep_hal_i2c.h` | `rtc_bus` 已可用。 |
| RTC | `app/services/rtc_service.h`，底层才用 `hal/include/ep_hal_rtc.h` | 业务读时间调用 `rtc_service_get_time()`；底层映射 `rtc -> PCF8563`。 |
| 文件读写 | SDK/RT-Thread 文件系统 API | SD 卡文件系统由 SDK 负责，业务可按平台已提供的 `open/read/write` 路线使用。 |
| UI 页面 | `app/ui/app_ui.h` 和 LVGL API | 页面代码写在 `app/ui/`，Mac host 和 AIC SDK 编译共用源码。 |
| UI 生命周期 | `components/ui/include/ep_ui.h` | host/macOS 用它调用 `lv_init/timer_handler/deinit`；D12x/Luban-Lite 由 SDK 自己管理 LVGL 生命周期。 |
| display/touch | 各平台 LVGL port | D12x/Luban-Lite 的 `ui.lvgl_provider=sdk`，显示和触摸 port 由原厂 SDK 提供；EP 不封 display/touch HAL。 |

## 当前推进结论

当前平台适配可以认为完成了“能写业务”的基础条件：

1. `./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p` 能进入 Luban-Lite 真实构建。
2. 应用骨架已经链接进最终镜像，`EP_LOGI` 能从串口打印。
3. OSAL 基础能力已经覆盖常用业务线程、同步和消息队列场景。
4. KI 板当前需要的 UART/PWM/GPIO/I2C/RTC 已有真实 HAL port。
5. 蜂鸣器、RTC、LCD sleep 已经有业务服务接口，业务代码可以先调用 `app/services/`，不用直接碰 HAL 或 pinmux。
6. display/touch 交给平台 LVGL port，避免 EP 重复封一层低价值 API。
7. SD 卡文件系统能力由 Luban-Lite/RT-Thread 提供，业务层需要文件读写时直接按平台文件系统能力使用。
8. LVGL 页面代码已经有 `app/ui/` 公共入口，可以在 Mac 上写页面，再随 `libep_app_core.a` 进入 AIC 镜像。
9. SPI、ADC 当前不作为主线任务，等业务确实用到再补对应 port 和冒烟测试。
10. 电源板 UART2 的硬件通道已经打开，协议层后续在业务模块或专用组件里实现。

## LVGL 归属规则

`targets/<target>.yaml` 的 `ui.lvgl_provider` 是判断 LVGL 放在哪里的唯一入口。

当前 D12x/Luban-Lite 使用：

```yaml
ui:
  lvgl_provider: sdk
  lvgl_note: Luban-Lite SDK provides LVGL display and input ports.
```

这表示 LVGL 源码、`lv_conf.h`、显示刷新、触摸输入和硬件加速配置都归 Luban-Lite SDK 维护。主工程不把这套 LVGL 复制进 `components/`，也不在 EP HAL 中再封 display/touch。业务需要写 UI 时，把页面代码写进 `app/ui/`，只使用标准 LVGL API 和 EP 公共服务接口。

Mac 开发时的路径是：

```text
./build.sh run-host-app
  -> ep_host_app
  -> ep_framework_start()
  -> app/main.c: app_main()
  -> app/ui/app_ui.c
  -> include host_macos 预编译包里的 lvgl.h
  -> platforms/host/posix/ui_port 创建 SDL2 window/mouse/keyboard
  -> app_ui_create()
  -> ep_ui_process() loop
```

AIC 编译时的路径是：

```text
app/ui/app_ui.c
  -> export_sdk_ep_package.sh 使用 Luban-Lite SDK 的 lvgl_v9 头文件编译
  -> libep_app_core.a
  -> application/rt-thread/ep_app/
  -> ep_lubanlite_lvgl_app_ui_create()
  -> lv_user_gui_init()
  -> Luban-Lite SDK 链接最终镜像
```

Linux 芯片如果没有这种原厂 RTOS SDK 集成，可以使用 `ui.lvgl_provider=component` 或 `prebuilt`。例如 F133/Tina Linux 可以用芯片专属 LVGL 仓库维护 framebuffer、输入、G2D 加速、旋转和交叉编译规则，再由主工程按组件或预编译依赖消费。

线程停止约定：

- `ep_thread_join()` 只等待线程入口自然返回。
- 当前没有强制 stop API，也不使用 `rt_thread_delete()` 强杀业务线程。
- 需要停止后台线程时，通过 stop 标志、事件或队列消息通知线程自行退出，然后再 join。

详细 API 说明见：

- `app-business-skeleton.md`
- `osal-api-reference.md`
- `hal-api-reference.md`
- `device-compatibility-reference.md`
