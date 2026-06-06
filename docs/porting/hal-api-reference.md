# HAL API 参考

HAL 是硬件访问兼容层，用于隔离 GPIO、UART、I2C、SPI、PWM、ADC、RTC 等底层驱动差异。应用层不应该直接调用 RT-Thread device API、Luban-Lite BSP API 或板级 pinmux。

当前 HAL 公共头文件在 `hal/include/`。RT-Thread/Luban-Lite 真实 port 在 `platforms/rtos/demo_family/hal_port/`。本文同时记录接口契约、参数含义、返回值和当前实现状态。

当前 KI-141103-480p 已经接入 UART、PWM、GPIO、I2C、RTC。SPI 和 ADC 目前业务暂时不用，保留公共接口，等真实需求出现再补 port。display/touch 不规划 EP HAL，由各芯片自己的 LVGL display/input port 负责。

## 通用约定

HAL 复用 OSAL 错误码：

| 返回值 | 含义 |
| --- | --- |
| `EP_OK` | 成功。 |
| `EP_ERR_INVAL` | 参数非法。 |
| `EP_ERR_TIMEOUT` | 等待超时。 |
| `EP_ERR_BUSY` | 设备忙、资源不足或设备已被占用。 |
| `EP_ERR_UNSUPPORTED` | 当前平台不支持该设备或该操作。 |

句柄是不透明类型：

```c
typedef struct ep_gpio ep_gpio_t;
typedef struct ep_uart ep_uart_t;
typedef struct ep_i2c ep_i2c_t;
typedef struct ep_spi ep_spi_t;
typedef struct ep_pwm ep_pwm_t;
typedef struct ep_adc ep_adc_t;
typedef struct ep_rtc ep_rtc_t;
```

调用方只能通过 HAL API 使用句柄，不能访问内部字段。UART、PWM、RTC 当前已经有 close 接口；GPIO 和 I2C 当前没有统一 release/close 接口，长生命周期使用为主。后续如果需要动态设备管理，应先补齐生命周期接口并同步更新本文档。

公共头文件按功能拆分，不存在一个总入口头文件：

| 能力 | 业务应包含的头文件 |
| --- | --- |
| GPIO | `hal/include/ep_hal_gpio.h` |
| UART | `hal/include/ep_hal_uart.h` |
| I2C | `hal/include/ep_hal_i2c.h` |
| SPI | `hal/include/ep_hal_spi.h` |
| PWM | `hal/include/ep_hal_pwm.h` |
| ADC | `hal/include/ep_hal_adc.h` |
| RTC | `hal/include/ep_hal_rtc.h` |

## 设备名约定

`name` 参数表示逻辑设备名或平台设备名。为了避免业务代码绑定板级细节，推荐优先使用逻辑设备名：

| 逻辑设备名 | KI-141103-480p 当前映射 |
| --- | --- |
| `console_uart` | UART1，PA2/PA3 |
| `power_uart` | UART2，PA4/PA5 |
| `rtc_bus` | I2C1，PD4/PD5 |
| `rtc` | PCF8563，I2C1，PD4/PD5，地址 0x51 |
| `beep_pwm` | PWM1，PC7，channel 1 |
| `lcd_sleep_gpio` | PD3 |
| `panel_enable_gpio` | PE13 |

如果某个平台暂时还没有逻辑名映射，可以在平台 HAL port 内兼容底层设备名，例如 `uart1`、`uart2`、`i2c1`、`pwm`。业务代码仍应逐步迁移到逻辑名。

## GPIO

### `int ep_gpio_request(ep_gpio_t **gpio, const char *name)`

申请一个 GPIO 句柄。

| 参数 | 含义 |
| --- | --- |
| `gpio` | 输出 GPIO 句柄。 |
| `name` | GPIO 逻辑名或平台名。 |

返回值：

- `EP_OK`：申请成功。
- `EP_ERR_INVAL`：`gpio` 为空或 `name` 无效。
- `EP_ERR_BUSY`：GPIO 已被占用或资源不足。
- `EP_ERR_UNSUPPORTED`：当前平台不支持该 GPIO。

当前 RT-Thread/Luban-Lite GPIO 真实 port 已实现以下逻辑名：

```text
lcd_sleep_gpio    -> rt_pin_get("PD.3")
panel_enable_gpio -> rt_pin_get("PE.13")
```

当前也兼容直接传入已登记的底层 pin 名称 `PD.3` 和 `PE.13`。业务代码应优先使用逻辑名；新增 GPIO 应先登记逻辑名，再暴露给业务层。

### `int ep_gpio_set_direction(ep_gpio_t *gpio, ep_gpio_dir_e dir)`

设置 GPIO 输入或输出方向。

| 参数 | 含义 |
| --- | --- |
| `gpio` | GPIO 句柄。 |
| `dir` | `EP_GPIO_INPUT` 或 `EP_GPIO_OUTPUT`。 |

返回值：

- `EP_OK`：设置成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：底层不支持。

### `int ep_gpio_write(ep_gpio_t *gpio, int value)`

输出 GPIO 电平。

| 参数 | 含义 |
| --- | --- |
| `gpio` | GPIO 句柄。 |
| `value` | `0` 表示低电平，非 0 表示高电平。 |

返回值：

- `EP_OK`：写入成功。
- `EP_ERR_INVAL`：参数非法或 GPIO 不是输出模式。
- `EP_ERR_UNSUPPORTED`：底层不支持。

### `int ep_gpio_read(ep_gpio_t *gpio, int *value)`

读取 GPIO 电平。

| 参数 | 含义 |
| --- | --- |
| `gpio` | GPIO 句柄。 |
| `value` | 输出电平，`0` 为低，`1` 为高。 |

返回值：

- `EP_OK`：读取成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：底层不支持。

## UART

### `int ep_uart_open(ep_uart_t **uart, const char *name)`

打开串口。

| 参数 | 含义 |
| --- | --- |
| `uart` | 输出串口句柄。 |
| `name` | 串口逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙或资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持该串口。

当前建议逻辑名：

| 逻辑名 | 用途 |
| --- | --- |
| `console_uart` | 调试控制台，当前 KI 板对应 UART1。 |
| `power_uart` | 电源板通信，当前 KI 板对应 UART2。 |

当前 RT-Thread/Luban-Lite port 映射：

```text
console_uart -> uart1
power_uart   -> uart2
```

打开时使用 RT-Thread device 框架：

```text
rt_device_find(...)
rt_device_open(..., RT_DEVICE_OFLAG_RDWR | RT_DEVICE_FLAG_INT_RX | RT_DEVICE_FLAG_STREAM)
```

### `int ep_uart_write(ep_uart_t *uart, const void *buf, size_t len)`

写串口数据。

| 参数 | 含义 |
| --- | --- |
| `uart` | 串口句柄。 |
| `buf` | 待发送数据。 |
| `len` | 待发送字节数。 |

返回值：

- `EP_OK`：所有数据已提交到底层驱动。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：发送缓冲区忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

当前接口不返回实际写入字节数。需要部分写语义时，应新增接口或扩展返回约定，不能在业务层猜测。

当前 RT-Thread/Luban-Lite port 要求 `rt_device_write()` 返回完整长度才视为 `EP_OK`，否则返回 `EP_ERR_BUSY`。

### `int ep_uart_read(ep_uart_t *uart, void *buf, size_t len, unsigned int timeout_ms)`

读串口数据。

| 参数 | 含义 |
| --- | --- |
| `uart` | 串口句柄。 |
| `buf` | 接收缓冲区。 |
| `len` | 期望读取字节数。 |
| `timeout_ms` | 等待时间。`0` 表示非阻塞尝试。 |

返回值：

- `EP_OK`：读取成功。
- `EP_ERR_TIMEOUT`：超时未读到完整数据，或底层按超时返回。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：底层不支持。

当前接口不返回实际读取字节数。后续如果电源板协议需要变长帧，建议新增带 `out_len` 的读取接口。

当前 RT-Thread/Luban-Lite port 读取语义：

```text
timeout_ms == 0 -> rt_device_read 读一次，不足 len 返回 EP_ERR_TIMEOUT
timeout_ms > 0  -> 每 1 ms 轮询一次，直到读满 len 或超时
```

如果底层每次只返回部分数据，port 会按缓冲区偏移累计，直到累计长度达到 `len`。

### `int ep_uart_close(ep_uart_t *uart)`

关闭串口句柄。

| 参数 | 含义 |
| --- | --- |
| `uart` | 串口句柄。 |

返回值：

- `EP_OK`：关闭成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：底层不支持关闭或关闭失败。

## I2C

### `int ep_i2c_open(ep_i2c_t **bus, const char *name)`

打开 I2C 总线。

| 参数 | 含义 |
| --- | --- |
| `bus` | 输出 I2C 总线句柄。 |
| `name` | I2C 逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙或资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持该 I2C 总线。

当前 RT-Thread/Luban-Lite I2C 真实 port 已实现以下逻辑名：

```text
rtc_bus -> rt_i2c_bus_device_find("i2c1")
```

当前也兼容直接传入底层总线名 `i2c1`。业务代码应优先使用逻辑名；新增 I2C 设备应先登记逻辑名，再暴露给业务层。

### `int ep_i2c_write(ep_i2c_t *bus, uint16_t addr, const void *buf, size_t len)`

向 I2C 从设备写数据。

| 参数 | 含义 |
| --- | --- |
| `bus` | I2C 总线句柄。 |
| `addr` | 7 位或平台约定的从设备地址。当前公共接口不包含 10 位地址标志。 |
| `buf` | 待写数据。 |
| `len` | 待写字节数。 |

返回值：

- `EP_OK`：写入成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_TIMEOUT`：传输超时。
- `EP_ERR_BUSY`：总线忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

### `int ep_i2c_read(ep_i2c_t *bus, uint16_t addr, void *buf, size_t len)`

从 I2C 从设备读取数据。

| 参数 | 含义 |
| --- | --- |
| `bus` | I2C 总线句柄。 |
| `addr` | 从设备地址。 |
| `buf` | 接收缓冲区。 |
| `len` | 读取字节数。 |

返回值：

- `EP_OK`：读取成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_TIMEOUT`：传输超时。
- `EP_ERR_BUSY`：总线忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

注意：

- 当前 API 没有寄存器地址参数。寄存器读写可以由业务协议层先写寄存器地址再读，或后续补 `ep_i2c_mem_read/write`。

## RTC

### 时间结构

```c
typedef struct {
    uint16_t year;
    uint8_t month;
    uint8_t day;
    uint8_t hour;
    uint8_t minute;
    uint8_t second;
    uint8_t weekday;
} ep_rtc_time_t;
```

| 字段 | 含义 |
| --- | --- |
| `year` | 完整年份。当前 PCF8563 port 支持 `2000-2099`。 |
| `month` | 月，`1-12`。 |
| `day` | 日，`1-31`。当前公共接口不校验大小月和闰年。 |
| `hour` | 时，`0-23`。 |
| `minute` | 分，`0-59`。 |
| `second` | 秒，`0-59`。 |
| `weekday` | 星期，`0-6`，约定 `0` 为周日。 |

### `int ep_rtc_open(ep_rtc_t **rtc, const char *name)`

打开 RTC 设备。

| 参数 | 含义 |
| --- | --- |
| `rtc` | 输出 RTC 句柄。 |
| `name` | RTC 逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持该 RTC。

当前 RT-Thread/Luban-Lite RTC 真实 port 已实现：

```text
rtc     -> PCF8563，I2C1，地址 0x51
pcf8563 -> PCF8563，I2C1，地址 0x51
```

业务代码应优先使用逻辑名 `rtc`。

### `int ep_rtc_get_time(ep_rtc_t *rtc, ep_rtc_time_t *time)`

读取 RTC 日历时间。

| 参数 | 含义 |
| --- | --- |
| `rtc` | RTC 句柄。 |
| `time` | 输出时间。 |

返回值：

- `EP_OK`：读取成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_UNSUPPORTED`：底层 I2C 读失败、PCF8563 VL bit 表示时间无效，或读出的字段超出公共范围。

当前 PCF8563 port 会先写寄存器地址 `0x02`，再连续读取秒、分、时、日、星期、月、年 7 个寄存器，并在 port 内完成 BCD 转换。业务层不应直接处理 PCF8563 寄存器。

### `int ep_rtc_set_time(ep_rtc_t *rtc, const ep_rtc_time_t *time)`

设置 RTC 日历时间。

| 参数 | 含义 |
| --- | --- |
| `rtc` | RTC 句柄。 |
| `time` | 待写入时间。 |

返回值：

- `EP_OK`：写入成功。
- `EP_ERR_INVAL`：参数非法或字段超出支持范围。
- `EP_ERR_UNSUPPORTED`：底层 I2C 写失败。

当前 PCF8563 port 支持年份 `2000-2099`，并从寄存器 `0x02` 开始连续写 7 个时间寄存器。

### `int ep_rtc_close(ep_rtc_t *rtc)`

关闭 RTC 句柄并释放平台资源。调用方关闭后不能继续使用该句柄。

返回值：

- `EP_OK`：关闭成功。
- `EP_ERR_INVAL`：参数非法。

## SPI

### `int ep_spi_open(ep_spi_t **bus, const char *name)`

打开 SPI 总线或设备。

| 参数 | 含义 |
| --- | --- |
| `bus` | 输出 SPI 句柄。 |
| `name` | SPI 逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙或资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持。

### `int ep_spi_transfer(ep_spi_t *bus, const void *tx_buf, void *rx_buf, size_t len)`

执行一次 SPI 全双工传输。

| 参数 | 含义 |
| --- | --- |
| `bus` | SPI 句柄。 |
| `tx_buf` | 发送缓冲区，可按平台实现约定允许为 `NULL`。 |
| `rx_buf` | 接收缓冲区，可按平台实现约定允许为 `NULL`。 |
| `len` | 传输字节数。 |

返回值：

- `EP_OK`：传输成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_TIMEOUT`：传输超时。
- `EP_ERR_BUSY`：总线忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

当前接口没有片选、模式、频率配置参数。真实业务需要 SPI 外设时，应先补配置接口。

## PWM

### `int ep_pwm_open(ep_pwm_t **pwm, const char *name)`

打开 PWM 设备。

| 参数 | 含义 |
| --- | --- |
| `pwm` | 输出 PWM 句柄。 |
| `name` | PWM 逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙或资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持。

KI 板当前建议：

```text
beep_pwm -> RT-Thread device "pwm", channel 1, PC7
```

### `int ep_pwm_set(ep_pwm_t *pwm, unsigned int period_ns, unsigned int duty_ns)`

设置 PWM 周期和占空比。

| 参数 | 含义 |
| --- | --- |
| `pwm` | PWM 句柄。 |
| `period_ns` | 周期，单位纳秒。 |
| `duty_ns` | 高电平时间，单位纳秒。必须小于等于 `period_ns`。 |

返回值：

- `EP_OK`：设置成功。
- `EP_ERR_INVAL`：参数非法，例如周期为 0 或占空比大于周期。
- `EP_ERR_BUSY`：设备忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

2.7 kHz 被动蜂鸣器的近似参数：

```text
period_ns = 370370
duty_ns   = 185185
```

### `int ep_pwm_enable(ep_pwm_t *pwm)`

启动 PWM 输出。

| 参数 | 含义 |
| --- | --- |
| `pwm` | PWM 句柄。 |

返回值：

- `EP_OK`：启动成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

### `int ep_pwm_disable(ep_pwm_t *pwm)`

停止 PWM 输出。

| 参数 | 含义 |
| --- | --- |
| `pwm` | PWM 句柄。 |

返回值：

- `EP_OK`：停止成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙。
- `EP_ERR_UNSUPPORTED`：底层不支持。

### `int ep_pwm_close(ep_pwm_t *pwm)`

关闭 PWM 句柄并释放平台资源。调用方关闭后不能继续使用该句柄。

| 参数 | 含义 |
| --- | --- |
| `pwm` | PWM 句柄。 |

返回值：

- `EP_OK`：关闭成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙。
- `EP_ERR_UNSUPPORTED`：底层不支持关闭或关闭失败。

当前 RT-Thread/Luban-Lite PWM 真实 port 已实现 `beep_pwm`。映射关系是 `rt_device_find("pwm")` + channel 1，对应 KI 板 PWM1/PC7 蜂鸣器。`ep_pwm_set()` 直接调用 `rt_pwm_set()`，单位保持纳秒；`ep_pwm_enable()` / `ep_pwm_disable()` 分别调用 `rt_pwm_enable()` / `rt_pwm_disable()`。

## ADC

### `int ep_adc_open(ep_adc_t **adc, const char *name)`

打开 ADC 通道或设备。

| 参数 | 含义 |
| --- | --- |
| `adc` | 输出 ADC 句柄。 |
| `name` | ADC 逻辑名或平台名。 |

返回值：

- `EP_OK`：打开成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_BUSY`：设备忙或资源不足。
- `EP_ERR_UNSUPPORTED`：平台不支持。

### `int ep_adc_read(ep_adc_t *adc, uint32_t *value)`

读取 ADC 原始值。

| 参数 | 含义 |
| --- | --- |
| `adc` | ADC 句柄。 |
| `value` | 输出原始采样值。单位和量程由平台定义。 |

返回值：

- `EP_OK`：读取成功。
- `EP_ERR_INVAL`：参数非法。
- `EP_ERR_TIMEOUT`：采样超时。
- `EP_ERR_UNSUPPORTED`：平台不支持。

注意：

- 当前接口只返回原始值，不做电压、电流、温度等物理量换算。
- 换算应放在设备驱动兼容层或业务组件中，并记录标定参数来源。

## 当前 HAL 状态

| 能力 | 公共头文件 | 当前状态 |
| --- | --- | --- |
| GPIO | 已定义 | RT-Thread/Luban-Lite 真实 port 已实现 `lcd_sleep_gpio` 和 `panel_enable_gpio`，基于 RT-Thread pin API。 |
| UART | 已定义 | RT-Thread/Luban-Lite 真实 port 已实现 `console_uart` 和 `power_uart`，基于 RT-Thread device。 |
| I2C | 已定义 | RT-Thread/Luban-Lite 真实 port 已实现 `rtc_bus`，基于 RT-Thread I2C bus `i2c1`。 |
| SPI | 已定义 | 当前业务暂时不用，RT-Thread/Luban-Lite 真实 port 暂缓。 |
| PWM | 已定义 | RT-Thread/Luban-Lite 真实 port 已实现 `beep_pwm`，基于 RT-Thread PWM device `"pwm"` channel 1。 |
| ADC | 已定义 | 当前业务暂时不用，RT-Thread/Luban-Lite 真实 port 暂缓。 |
| RTC | 已定义 | RT-Thread/Luban-Lite 真实 port 已实现 `rtc`，基于 PCF8563 + I2C1，地址 0x51。 |
| Display | 不规划 EP HAL | 当前由各芯片 SDK 的 LVGL display port 或 framebuffer / panel 驱动负责。 |
| Touch | 不规划 EP HAL | 当前由各芯片 SDK 的 LVGL input port 或触摸驱动负责。 |

后续补 SPI、ADC 等真实驱动时，应同时补 host fake 或单测，确保 API 语义稳定。display/touch 不在 EP HAL 中二次封装，业务 UI 直接使用 LVGL。
