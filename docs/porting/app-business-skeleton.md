# 应用业务骨架

本文记录当前 `app/` 目录的业务入口、初始化顺序、服务边界和后续写业务代码时应该遵守的规则。它回答一个问题：平台适配完成后，业务代码应该从哪里开始写。

## 当前结论

当前应用已经不是把所有逻辑都堆在 `app/main.c`。主工程已经拆出最小业务骨架：

```text
app/main.c
  -> app_context_init()
  -> app_core_start()
    -> beep_service_init()
    -> rtc_service_init()
    -> lcd_sleep_service_init()
    -> power_board_service_init()
  -> app/ui/app_ui.c         # 有 LVGL 的平台在 display/input ready 后调用
  -> app_selftest_run()
  -> app_core_run()
```

这些代码会被编进 `libep_app_core.a`，再由 Luban-Lite SDK 复制到 `application/rt-thread/ep_app` 并链接进最终镜像。后续业务代码优先放在 `app/app_core.c`、`app/services/`、`app/ui/` 或新增业务模块里，不直接修改 SDK staging 目录。

Mac 本地调试应用时运行：

```bash
./build.sh host
```

该命令会编译并运行 `ep_host_app`。它先走完整 framework 和 `app_main()` 生命周期，再初始化 host SDL2/LVGL，调用同一份 `app_ui_create()` 并进入 UI 循环。`./build.sh build-host` 和 `./build.sh run-host-app` 是同一入口。这个入口用于写应用业务和页面；`ep_host_lvgl_demo` 继续作为 LVGL demo/控件验证入口保留。

## 文件路径

| 作用 | 路径 |
| --- | --- |
| 应用入口 | `app/main.c` |
| 应用入口声明 | `app/include/app_main.h` |
| 应用上下文 | `app/include/app_context.h` |
| 应用生命周期接口 | `app/include/app_core.h` |
| 应用生命周期实现 | `app/app_core.c` |
| 当前自检接口 | `app/selftest/app_selftest.h` |
| 当前自检实现 | `app/selftest/app_selftest.c` |
| 应用 UI 公共接口 | `app/ui/app_ui.h` |
| 应用 UI 公共实现 | `app/ui/app_ui.c` |
| Mac app 运行入口 | `platforms/host/posix/startup/host_app_main.c` |
| 蜂鸣器服务 | `app/services/beep_service.h`、`app/services/beep_service.c` |
| RTC 服务 | `app/services/rtc_service.h`、`app/services/rtc_service.c` |
| LCD sleep 服务 | `app/services/lcd_sleep_service.h`、`app/services/lcd_sleep_service.c` |
| 电源板服务 | `app/services/power_board_service.h`、`app/services/power_board_service.c` |
| app 静态库目标 | `app/CMakeLists.txt` |
| SDK 导出脚本 | `tools/scripts/export_sdk_ep_package.sh` |

## `app/main.c` 职责

`app/main.c` 只负责入口编排：

```c
int app_main(void)
{
    app_context_t app;
    int rc;

    app_context_init(&app);

    rc = app_core_start(&app);
    if (rc != EP_OK) {
        return rc;
    }

    rc = app_selftest_run(&app);
    if (rc != EP_OK) {
        return rc;
    }

    return app_core_run(&app);
}
```

这里不直接写设备协议、UI 页面、菜谱解析或硬件操作。入口文件保持薄，可以让 host、RTOS 和后续 Linux target 共享同一套应用启动顺序。

## 应用上下文

应用上下文定义在 `app/include/app_context.h`：

```c
typedef struct app_context {
    int services_ready;
} app_context_t;
```

当前只有一个字段：

| 字段 | 含义 |
| --- | --- |
| `services_ready` | 服务初始化完成标志。`0` 表示未完成，`1` 表示 `app_core_start()` 已经完成服务初始化。 |

后续新增业务模块时，跨模块共享的长生命周期状态可以放进 `app_context_t`。不要把临时变量、协议局部缓存或平台私有句柄随意塞进全局变量。

## 生命周期 API

公共头文件是 `app/include/app_core.h`。

### `void app_context_init(app_context_t *app)`

初始化应用上下文。

| 参数 | 含义 |
| --- | --- |
| `app` | 应用上下文指针，可为 `NULL`。 |

当前行为：

- `app == NULL` 时直接返回。
- 非空时将 `services_ready` 置为 `0`。

### `int app_core_start(app_context_t *app)`

启动应用服务。

| 参数 | 含义 |
| --- | --- |
| `app` | 应用上下文指针，不能为 `NULL`。 |

返回值：

- `EP_OK`：所有服务初始化成功。
- `EP_ERR_INVAL`：`app` 为空。
- 其他 `EP_ERR_*`：某个服务初始化失败，错误码直接向上传播。

当前初始化顺序：

```text
beep_service_init()
rtc_service_init()
lcd_sleep_service_init()
power_board_service_init()
```

全部成功后，`app->services_ready` 置为 `1`。

### `int app_core_run(app_context_t *app)`

进入当前应用主流程。

| 参数 | 含义 |
| --- | --- |
| `app` | 应用上下文指针，不能为 `NULL`，且 `services_ready` 必须为 `1`。 |

返回值：

- `EP_OK`：当前主流程正常结束。
- `EP_ERR_INVAL`：上下文为空或服务尚未启动。

当前实现只打印 `app lifecycle done` 并返回。后续真正业务主循环、后台任务管理或 UI 主流程可以从这里向外拆。

## 应用 UI 层

应用 UI 层放在：

```text
app/ui/
```

当前公共接口是：

```c
int app_ui_create(void);
```

这个接口的含义是：在“当前已经初始化好的 LVGL active screen” 上创建应用页面。它不负责初始化 LVGL，不负责创建显示设备，不负责触摸输入，也不负责窗口或 framebuffer。调用它之前，平台必须已经完成自己的 LVGL、display 和 input 准备工作。

当前调用关系：

```text
host/macOS:
  ./build.sh run-host-app
  ep_framework_start()
  app_main()
  ep_ui_init()
  ep_host_ui_port_init()
  app_ui_create()
  ep_ui_process() loop

D12x/Luban-Lite:
  Luban-Lite SDK 初始化 LVGL/display/touch
  主工程导出的 app/ui/app_ui.c 编进 libep_app_core.a
  lv_user_gui_init()
    -> ep_lubanlite_lvgl_app_ui_create()
      -> app_ui_create()
```

`app_ui_create()` 返回值：

| 返回值 | 含义 |
| --- | --- |
| `EP_OK` | 页面创建成功。 |
| `EP_ERR_UNSUPPORTED` | 当前 LVGL active screen 或控件创建失败，通常表示 LVGL/display/input 尚未准备好，或该 target 不提供 LVGL。 |

`app/ui/app_ui.h` 故意不包含 `lvgl.h`，只暴露业务 UI 创建入口，避免公共头文件把 LVGL 类型向外扩散。`app/ui/app_ui.c` 可以包含标准 `lvgl.h` 并使用通用 LVGL API，例如 `lv_screen_active()`、`lv_label_create()`、`lv_label_set_text()` 和 `lv_obj_align()`。

这一层必须保持平台无关，不能包含：

- `SDL2/SDL.h`
- `ep_host_ui_port.h`
- `rtthread.h`
- Luban-Lite/AIC 私有 BSP 头文件
- 具体 LCD、触摸、framebuffer 或 pinmux 头文件

后续在 Mac 上写 LVGL 页面、页面切换、控件布局和事件回调时，优先写在 `app/ui/`。Mac host 使用 `third_party/prebuilt/lvgl/host_macos` 提供 LVGL 头文件和 SDL2 后端；D12x/Luban-Lite 使用 SDK 自带 LVGL 头文件和显示触摸 port，并通过 `lv_user_gui_init()` 的 `ep_lubanlite_lvgl_app_ui_create()` 弱符号桥接进入 `app_ui_create()`。只要 `app/ui/` 不碰平台私有 API，同一份页面源码就可以被两边编译和运行。

## 自检流程

当前自检在 `app/selftest/app_selftest.c`：

```text
app_selftest_run()
  -> ep_event_subscribe(APP_EVENT_TIMER_DONE, ...)
  -> ep_timer_start(APP_TIMER_ID_SELF_TEST, 50 ms, APP_EVENT_TIMER_DONE)
  -> ep_sleep_ms(10 ms) 循环等待
```

这个自检的目的不是做产品逻辑，而是验证 framework 到 app 的基础链路：

- `ep_event_init()` 已经在 `ep_framework_init()` 中完成。
- `ep_timer_init()` 已经在 `ep_framework_init()` 中完成。
- `ep_sleep_ms()` 的 RT-Thread OSAL port 可用。
- app 代码确实链接进最终镜像并在运行。

返回值：

- `EP_OK`：定时器事件在 500 ms 内触发。
- `EP_ERR_INVAL`：上下文为空。
- `EP_ERR_TIMEOUT`：等待超时。
- 其他 `EP_ERR_*`：事件订阅或定时器启动失败。

后续产品逻辑稳定后，可以把这段自检改成可配置的启动自检，或仅在 debug/profile 构建中启用。

## 服务边界

`app/services/` 是业务服务层。它不替代 HAL，也不直接维护 pinmux、defconfig 或 SDK 驱动。它负责把业务常用动作封成更容易读的接口。

### 蜂鸣器服务

头文件：

```text
app/services/beep_service.h
```

接口：

```c
#define BEEP_SERVICE_DEFAULT_FREQUENCY_HZ 2700u

int beep_service_init(void);
int beep_service_beep_ms(unsigned int duration_ms);
```

含义：

| 接口 | 含义 |
| --- | --- |
| `BEEP_SERVICE_DEFAULT_FREQUENCY_HZ` | 默认蜂鸣器频率，当前为 2700 Hz。 |
| `beep_service_init()` | 初始化蜂鸣器服务。当前只打印 ready 日志并返回 `EP_OK`。 |
| `beep_service_beep_ms(duration_ms)` | 让蜂鸣器鸣叫指定毫秒数。`duration_ms == 0` 返回 `EP_ERR_INVAL`；成功时返回 `EP_OK`；底层 PWM 不支持或失败时返回对应 `EP_ERR_*`。 |

当前实现通过 `ep_pwm_open("beep_pwm")` 打开蜂鸣器 PWM，按 2700 Hz 计算周期：

```text
period_ns = 1000000000 / 2700 = 370370
duty_ns   = period_ns / 2     = 185185
```

调用顺序：

```text
ep_pwm_open("beep_pwm")
ep_pwm_set(period_ns, duty_ns)
ep_pwm_enable()
ep_sleep_ms(duration_ms)
ep_pwm_disable()
ep_pwm_close()
```

业务层不要直接调用 RT-Thread PWM API，也不要写死 `"pwm"`、channel 1 或 PC7。板级映射属于 HAL port。

### RTC 服务

头文件：

```text
app/services/rtc_service.h
```

接口：

```c
int rtc_service_init(void);
int rtc_service_get_time(ep_rtc_time_t *time);
```

含义：

| 接口 | 含义 |
| --- | --- |
| `rtc_service_init()` | 初始化 RTC 服务。当前只打印 ready 日志并返回 `EP_OK`。 |
| `rtc_service_get_time(time)` | 读取 RTC 日历时间。`time == NULL` 返回 `EP_ERR_INVAL`；成功时返回 `EP_OK`；底层 RTC 不支持或读失败时返回对应 `EP_ERR_*`。 |

当前实现调用 `ep_rtc_open("rtc")`、`ep_rtc_get_time()`、`ep_rtc_close()`。KI 板上 `rtc` 由 HAL 映射到 PCF8563，挂在 I2C1 PD4/PD5，地址 `0x51`。业务层不直接处理 PCF8563 寄存器和 BCD 编码。

### LCD Sleep 服务

头文件：

```text
app/services/lcd_sleep_service.h
```

接口：

```c
int lcd_sleep_service_init(void);
int lcd_sleep_service_set_sleep(int sleep_enabled);
```

含义：

| 接口 | 含义 |
| --- | --- |
| `lcd_sleep_service_init()` | 初始化 LCD sleep 服务，申请 `lcd_sleep_gpio` 并设置为输出。成功返回 `EP_OK`。 |
| `lcd_sleep_service_set_sleep(sleep_enabled)` | 控制 LCD sleep。`0` 写低电平，非 0 写高电平。当前按高电平 sleep、低电平 wake 处理。 |

底层逻辑设备名是 `lcd_sleep_gpio`，当前 KI 板映射到 PD3。服务层缓存 GPIO 句柄，避免重复 `ep_gpio_request()` 触发 busy。业务层不要直接操作 RT-Thread pin，也不要写死 `PD.3`。

host/macOS 和 Linux demo 的 HAL stub 会让 `lcd_sleep_service_init()` 成功，以便业务生命周期可以在非目标平台跑起来；真正写电平的动作在 stub 平台仍会返回 `EP_ERR_UNSUPPORTED`。

### 电源板服务

头文件：

```text
app/services/power_board_service.h
```

接口：

```c
int power_board_service_init(void);
int power_board_service_write(const void *buf, size_t len);
```

含义：

| 接口 | 含义 |
| --- | --- |
| `power_board_service_init()` | 初始化电源板服务。当前只打印 ready 日志并返回 `EP_OK`。 |
| `power_board_service_write(buf, len)` | 向电源板发送原始数据。当前协议尚未实现，返回 `EP_ERR_UNSUPPORTED`。 |

电源板硬件通道已经打开：逻辑设备 `power_uart` 映射 UART2 PA4/PA5。真正协议层还缺帧头、长度、命令字、校验、应答、超时、重发和状态解析定义。协议明确后，应先补协议文档和测试，再实现服务层。

## 和 framework 的关系

`core/src/ep_framework.c` 负责平台无关基础设施初始化：

```text
ep_framework_start()
  -> ep_platform_boot()
  -> ep_framework_init()
    -> ep_log_init()
    -> ep_config_init()
    -> ep_event_init()
    -> ep_timer_init()
    -> ep_device_init()
    -> ep_platform_register_default_devices()
  -> app_main()
```

`app/` 不负责初始化 log/config/event/timer/device registry。这些能力在进入 `app_main()` 前已经由 framework 初始化。`app_core_start()` 只负责业务服务启动。

## 和 Luban-Lite SDK 的关系

主工程构建时会生成：

```text
out/ep/<target>/lib/libep_app_core.a
out/ep/<target>/include/
out/ep/<target>/manifest.json
```

Luban-Lite 构建时会复制到：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/
```

典型结构：

```text
application/rt-thread/ep_app/
  include/
  lib/libep_app_core.a
  ep_app_main.c
  SConscript
  manifest.json
```

`application/rt-thread/ep_app` 是 staging 目录，不是业务源头。业务源头永远在主工程 `app/`、`components/`、`osal/`、`hal/`、`platforms/` 这些目录。

SDK 导出时，`tools/scripts/export_sdk_ep_package.sh` 会把 `app/ui/app_ui.c` 一起编进 `libep_app_core.a`。D12x/Luban-Lite 目标使用 SDK 自带 LVGL，所以导出脚本使用 Luban-Lite 里的 LVGL include 路径：

```text
<luban-lite-root>/packages/artinchip/lvgl-ui/lvgl_v9/
<luban-lite-root>/packages/artinchip/lvgl-ui/lvgl_v9/lvgl/
```

同时，SDK 导出仍然不包含 `components/ui/src/ep_ui.c`。原因是 RTOS SDK 已经负责 LVGL 生命周期、显示刷新和触摸输入，主工程不能在 SDK 静态库里再执行一套 host 风格的 LVGL 初始化。

## 后续写业务的规则

- 新业务先判断是“纯业务逻辑”还是“硬件/系统相关逻辑”。
- 纯业务逻辑优先放 `app/` 下的新模块，或后续明确复用价值后放 `components/`。
- LVGL 页面、页面切换和控件事件优先放 `app/ui/`，不要写进 `platforms/host/` 或 SDK staging 目录。
- 硬件动作优先落到 `app/services/`，服务层再调用 HAL 或 SDK 已有能力。
- OS 差异只能通过 `osal/include/` 访问。
- 硬件差异只能通过 `hal/include/`、设备注册表或平台能力访问。
- 不在业务代码里包含 `rtthread.h`、Luban-Lite BSP 头文件或板级 pinmux 头文件。
- 未实现接口明确返回 `EP_ERR_UNSUPPORTED`，不要假装成功。
- 每新增真实业务服务，都同步补 API 文档、板级验证步骤和 Wiki。
