# 设备兼容层说明

设备兼容层用于把“业务可见的逻辑设备”与“平台真实设备”隔离开。业务代码不应该知道某个功能具体用了 PA2/PA3、PD4/PD5 或 Luban-Lite 哪个驱动节点。

## 设备注册表 API

公共头文件：

```text
components/device/include/ep_device.h
```

### 设备类型

```c
typedef enum {
    EP_DEVICE_TYPE_GPIO = 0,
    EP_DEVICE_TYPE_I2C,
    EP_DEVICE_TYPE_SPI,
    EP_DEVICE_TYPE_UART,
    EP_DEVICE_TYPE_DISPLAY,
    EP_DEVICE_TYPE_TOUCH,
    EP_DEVICE_TYPE_STORAGE,
    EP_DEVICE_TYPE_NETWORK,
    EP_DEVICE_TYPE_SENSOR,
    EP_DEVICE_TYPE_OTHER,
    EP_DEVICE_TYPE_COUNT
} ep_device_type_e;
```

### 设备状态

```c
typedef enum {
    EP_DEVICE_STATE_OFFLINE = 0,
    EP_DEVICE_STATE_ONLINE,
    EP_DEVICE_STATE_ERROR,
    EP_DEVICE_STATE_COUNT
} ep_device_state_e;
```

### 设备描述

```c
typedef struct {
    const char *name;
    ep_device_type_e type;
    ep_device_state_e state;
    ep_platform_capability_e capability;
    void *context;
} ep_device_desc_t;
```

| 字段 | 含义 |
| --- | --- |
| `name` | 逻辑设备名。必须非空，当前最大长度小于 32 字节。 |
| `type` | 设备类型。 |
| `state` | 当前状态。 |
| `capability` | 该设备对应的平台能力。 |
| `context` | 平台私有上下文，可指向 HAL 句柄、配置结构或驱动对象。 |

`context` 的所有权由注册方管理。当前设备注册表只保存指针，不释放 context。

## 函数说明

### `int ep_device_init(void)`

初始化设备注册表。

返回值：

- `EP_OK`：初始化成功。

当前状态：

- 该函数会标记注册表可用。
- 当前 `ep_framework_init()` 还没有自动调用 `ep_device_init()`；后续应把它纳入 framework 初始化顺序。

### `int ep_device_register(const ep_device_desc_t *desc, ep_device_t **device)`

注册一个设备。

| 参数 | 含义 |
| --- | --- |
| `desc` | 设备描述。 |
| `device` | 输出注册后的设备句柄，可为 `NULL`。 |

返回值：

- `EP_OK`：注册成功。
- `EP_ERR_UNSUPPORTED`：注册表尚未初始化。
- `EP_ERR_INVAL`：描述为空、名称非法、类型非法或状态非法。
- `EP_ERR_BUSY`：同名设备已存在，或设备槽位已满。

当前限制：

- 最大设备数为 8。
- 不支持注销设备。
- 不支持动态更新状态。

### `ep_device_t *ep_device_find(const char *name)`

按名称查找设备。

| 参数 | 含义 |
| --- | --- |
| `name` | 逻辑设备名。 |

返回值：

- 找到时返回设备句柄。
- 未找到、名称非法或注册表未初始化时返回 `NULL`。

### `ep_device_t *ep_device_find_by_type(ep_device_type_e type, unsigned int index)`

按类型和序号查找设备。

| 参数 | 含义 |
| --- | --- |
| `type` | 设备类型。 |
| `index` | 同类型设备序号，从 0 开始。 |

返回值：

- 找到时返回设备句柄。
- 未找到、类型非法或注册表未初始化时返回 `NULL`。

### 查询函数

| 函数 | 返回内容 |
| --- | --- |
| `ep_device_name(device)` | 设备名，非法句柄返回 `NULL`。 |
| `ep_device_type(device)` | 设备类型，非法句柄返回 `EP_DEVICE_TYPE_COUNT`。 |
| `ep_device_state(device)` | 设备状态，非法句柄返回 `EP_DEVICE_STATE_COUNT`。 |
| `ep_device_capability(device)` | 对应平台能力，非法句柄返回 `EP_PLATFORM_CAPABILITY_COUNT`。 |
| `ep_device_context(device)` | 平台私有上下文，非法句柄返回 `NULL`。 |

## 平台能力

公共头文件：

```text
platforms/include/ep_platform_capability.h
```

平台能力用于声明平台是否具备某类能力：

| 能力 | 含义 |
| --- | --- |
| `EP_PLATFORM_CAPABILITY_FILESYSTEM` | 文件系统。 |
| `EP_PLATFORM_CAPABILITY_CONFIG_PERSISTENCE` | 配置持久化。 |
| `EP_PLATFORM_CAPABILITY_LOG` | 日志输出。 |
| `EP_PLATFORM_CAPABILITY_THREAD` | 线程。 |
| `EP_PLATFORM_CAPABILITY_LVGL` | LVGL。 |
| `EP_PLATFORM_CAPABILITY_DISPLAY` | 显示。 |
| `EP_PLATFORM_CAPABILITY_TOUCH` | 触摸。 |
| `EP_PLATFORM_CAPABILITY_GPIO` | GPIO。 |
| `EP_PLATFORM_CAPABILITY_I2C` | I2C。 |
| `EP_PLATFORM_CAPABILITY_SPI` | SPI。 |
| `EP_PLATFORM_CAPABILITY_UART` | UART。 |
| `EP_PLATFORM_CAPABILITY_PWM` | PWM。 |
| `EP_PLATFORM_CAPABILITY_ADC` | ADC。 |
| `EP_PLATFORM_CAPABILITY_RTC` | RTC。 |
| `EP_PLATFORM_CAPABILITY_NETWORK` | 网络。 |

应用层应该通过 `ep_platform_has_capability()` 判断平台能力，而不是写死平台名。

## KI-141103-480p 逻辑设备映射

当前 KI 板推荐的逻辑设备名如下：

| 逻辑设备名 | 类型 | 能力 | 当前真实映射 | 用途 |
| --- | --- | --- | --- | --- |
| `console_uart` | UART | UART | UART1，PA2/PA3，115200 | 调试控制台。 |
| `power_uart` | UART | UART | UART2，PA4/PA5 | 电源板通信。 |
| `rtc` | SENSOR 或 OTHER | RTC | PCF8563，I2C1，PD4/PD5 | 实时时钟。 |
| `rtc_bus` | I2C | I2C | I2C1，PD4/PD5 | RTC 所在 I2C 总线。 |
| `beep` | OTHER | PWM | PWM1 channel 1，PC7 | 2.7 kHz 蜂鸣器。 |
| `beep_pwm` | GPIO 或 OTHER | PWM | PWM1 channel 1，PC7 | PWM 输出通道。 |
| `lcd_sleep_gpio` | GPIO | GPIO | PD3 | LCD sleep 控制脚；当前 18-bit RGB LD 配置未占用 PD3 作为数据线。 |
| `panel_enable_gpio` | GPIO | GPIO | PE13 | 面板 enable 控制脚。 |
| `display` | DISPLAY | DISPLAY | RGB 800x480 | LCD 显示。 |
| `touch` | TOUCH | TOUCH | GT911，800x480 | 触摸输入。 |
| `sdcard` | STORAGE | FILESYSTEM | SDMC1 | SD 卡存储。 |

其中 pinmux、pull、drive strength、LCD timing、GT911 坐标范围等继续由 Luban-Lite SDK 板级配置维护。业务代码只能使用逻辑设备名和公共接口。

## 当前建议的初始化顺序

后续 framework 初始化建议固定为：

```text
ep_log_init()
ep_config_init()
ep_event_init()
ep_timer_init()
ep_device_init()
平台设备注册
app_main()
```

当前代码状态：

- `ep_framework_init()` 已初始化 log、config、event、timer。
- `ep_device_init()` 尚未纳入 framework 自动初始化。
- KI 板真实硬件由 Luban-Lite defconfig 和 RT-Thread 驱动先行初始化。

## 后续补齐项

设备兼容层后续建议补：

- 设备注销或状态更新接口。
- 更多设备槽位或动态注册策略。
- 设备名常量头文件，避免字符串散落。
- 设备到 HAL 句柄的标准 context 类型。
- RTC、display、touch 等高层设备 API。
