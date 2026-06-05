# KI-141103-480p 冒烟测试手册

本文记录 KI-141103-480p 在 Luban-Lite 上的最小板级验证方法。目标是确认镜像能启动，基础外设和 EP framework 入口可用。

## 基线信息

| 项目 | 当前值 |
| --- | --- |
| target | `artinchip_d12x_lubanlite_ki_141103_480p` |
| chip | `d12x` |
| board | `KI-141103-480p` |
| kernel | `rt-thread` |
| defconfig | `d12x_KI-141103-480p_rt-thread_helloworld_defconfig` |
| bootloader defconfig | `d12x_KI-141103-480p_baremetal_bootloader_defconfig` |
| LCD | RGB 800x480 |
| touch | GT911，800x480 |
| RTC | PCF8563，I2C1，PD4/PD5 |
| RTC I2C HAL | `rtc_bus -> i2c1` |
| RTC HAL | `rtc -> PCF8563` |
| console | UART1，PA2/PA3，115200 |
| power UART | UART2，PA4/PA5 |
| beep | PWM1，PC7，2700 Hz |
| LCD sleep GPIO | PD3 |
| panel enable GPIO | PE13 |

## 编译

```bash
./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p
```

清理后编译：

```bash
./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p --clean
```

Docker 内执行时使用普通用户：

```bash
docker exec -u yuwei -w /home/yuwei/samba/yuwei_work/project/embedded-platform-core 184d93cbb90f \
  bash -lc './build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p'
```

## 镜像位置

Luban-Lite SDK 原始镜像目录：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/output/d12x_KI-141103-480p_rt-thread_helloworld/images/
```

典型烧录镜像：

```text
d12x_demo68-nor_v1.0.0.img
```

主工程收集目录：

```text
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/
```

构建日志：

```text
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/build.log
```

## 启动日志检查

串口参数：

```text
UART1
115200 8N1
```

启动后至少应看到：

```text
Welcome to ArtInChip Luban-Lite 1.3.0 [D12x Inside]
Board: KI-141103-480p
```

关键驱动日志：

```text
I/PWM: ArtInChip PWM loaded
I/pcf8563: Init RTC PCF8563 Success!
I/gt911: touch device gt911 init success
panel-rgb type: RGB pclk: 28 Mhz h: 800 v: 480
```

EP app 日志应能看到 `app/main.c` 中的 `EP_LOGI` 输出，例如：

```text
app lifecycle start
```

如果能看到 EP 日志，说明：

- `app/main.c` 已经进入最终镜像。
- `ep_lubanlite_app_main()` 已经进入 `ep_framework_start()`。
- EasyLogger RT-Thread 输出 port 正常。

## MSH 基础命令

进入 `aic />` 后可以先执行：

```text
help
list_device
```

期望：

- 能看到 RT-Thread shell。
- 能看到已注册的 UART、I2C、PWM、touch、SDMC 等设备。

## RTC 测试

当前 RTC 使用：

```text
PCF8563
I2C1
PD4/PD5
EP I2C HAL: rtc_bus -> i2c1
EP RTC HAL: rtc -> PCF8563
```

启动日志应包含：

```text
I/pcf8563: Init RTC PCF8563 Success!
```

如果系统提供 `date` 或 RTC 相关 MSH 命令，可以进一步测试：

```text
date
```

判断标准：

- 驱动初始化成功。
- I2C1 没有报通信失败。
- 读写时间命令能正常返回。

如果没有 RTC shell 命令，后续应补一个 EP 或 MSH 冒烟命令，用于读取 RTC 秒计数或日历时间。
当前 EP RTC HAL 已能通过 `ep_rtc_open("rtc")`、`ep_rtc_get_time()`、`ep_rtc_set_time()` 读写 PCF8563 日历时间。应用层不需要直接处理 PCF8563 BCD 和寄存器地址。

## LCD 测试

当前 LCD：

```text
RGB 800x480
```

启动日志应包含类似：

```text
panel-rgb type: RGB pclk: 28 Mhz h: 800 v: 480
```

判断标准：

- 屏幕点亮。
- 颜色正常。
- boot 阶段进度条居中显示。
- 文本没有被裁剪到不可见区域。
- RT-Thread 阶段 framebuffer 初始化成功。

如果颜色异常，优先检查：

- RGB/BGR 顺序。
- 18-bit / 24-bit 数据线模式。
- panel timing。
- bootloader 和 RT-Thread 阶段配置是否一致。

## 触摸测试

当前触摸：

```text
GT911
800x480
```

启动日志应包含：

```text
id = GT911
range_x = 800
range_y = 480
```

判断标准：

- `range_x` 必须是 800。
- `range_y` 必须是 480。
- 点击屏幕四角时坐标方向和范围正确。

如果显示 `1024x600`，说明 GT911 或屏幕坐标配置没有同步到当前 800x480 屏。

## 蜂鸣器测试

当前蜂鸣器：

```text
PWM1
PC7
2700 Hz
```

2.7 kHz 对应近似 PWM 参数：

```text
period_ns = 370370
duty_ns   = 185185
```

如果 MSH 有 PWM 命令，可以测试：

```text
pwm probe pwm
pwm set 1 370370 185185
pwm enable 1
pwm disable 1
```

如果启用了 beep package，可以测试：

```text
beep 1 500 50 2700
```

当前 EP PWM HAL 已能把 `beep_pwm` 映射到 RT-Thread 设备 `pwm` 的 channel 1。业务代码应通过 `ep_pwm_open("beep_pwm")`、`ep_pwm_set()`、`ep_pwm_enable()`、`ep_pwm_disable()` 控制蜂鸣器，不直接依赖 MSH 命令。

判断标准：

- `pwm enable 1` 后蜂鸣器发声。
- `pwm disable 1` 后停止。
- `beep` 命令能按指定频率和时长响。

## 电源板 UART2 测试

当前电源板串口：

```text
UART2
PA4/PA5
```

建议后续补一个专用 MSH 命令或 EP HAL 冒烟程序，用于：

- 打开 `power_uart`。
- 发送固定握手帧。
- 读取电源板响应。
- 打印十六进制收发日志。

当前 EP UART HAL 已能把 `power_uart` 映射到 RT-Thread 设备 `uart2`。在电源板协议接入前，可以先用临时 EP HAL 冒烟代码验证引脚、波特率和收发方向。

## SD 卡测试

当前 SD：

```text
SDMC1
boot 阶段单线 SD
```

启动时如果看到：

```text
E/DFS: mount fs[elm] on /sdcard failed.
```

说明 SDMC 驱动可能已加载，但文件系统挂载失败。需要区分：

- 卡未插入。
- 分区或文件系统格式不对。
- SDMC 驱动、引脚或供电问题。

建议测试：

```text
list_device
```

确认 SDMC 设备是否存在。后续可补格式化、挂载、读写文件的 MSH 冒烟步骤。

## app 接入测试

`app/main.c` 当前用于验证 EP framework 已经进入业务入口。

判断标准：

- 串口能看到 `EP_LOGI` 输出。
- 如果 app 使用 timer/event，应看到对应生命周期日志。
- 如果 framework 初始化失败，应看到 `EP app failed: rc=<code>`。

如果没有 app 日志：

1. 检查 `ep_lubanlite_app_main()` 是否调用 `ep_framework_start()`。
2. 检查 `libep_app_core.a` 是否被 SCons 链接。
3. 检查 EasyLogger RT-Thread port 是否走 `rt_kprintf()`。
4. 检查 log level 是否过滤了 `INFO`。

## 当前已知限制

- `ep_device_init()` 已自动纳入 framework 初始化，并注册当前 KI 板默认逻辑设备。
- SPI、ADC 等 HAL 真实 RT-Thread/Luban-Lite port 仍待按需求补齐。
- display、touch 由 Luban-Lite / LVGL 平台 port 管理，EP 不再另封公共高层 API。
- SD 卡文件系统挂载需要按实际卡和分区继续验证。
