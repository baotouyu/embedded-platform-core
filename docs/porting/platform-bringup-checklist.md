# 平台移植检查清单

本文作为新增真实平台时的执行清单。每个平台可以按这份清单逐步补齐，不要求一次做完全部能力。

当前 D12x + Luban-Lite + KI-141103-480p 已经完成基础 bring-up。这份清单后续主要用于接新 SDK、新芯片或新板子时复用。

## 适用平台

当前预期会覆盖：

- host/macOS。
- 匠芯创 Luban Lite。
- 全志 Linux。
- 后续其他 RTOS 或 Linux 平台。

## 第一阶段：建立平台边界

1. 确认平台管理方式。

RTOS 平台先确认 SDK 家族、芯片、板子和 target 名称。例如匠芯创 Luban-Lite 使用一个 SDK 家族仓库 `sdk-artinchip-luban-lite`，再用 target 区分 `d12x/demo68-nor`、`d13x/demo88-nor` 等具体目标。

当前 KI 板主工程 target：

```text
targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml
```

当前 SDK adapter env：

```text
third_party/sdk/sdk-artinchip-luban-lite/targets/artinchip_d12x_lubanlite_ki_141103_480p.env
```

2. 新建平台目录。

```text
platforms/rtos/artinchip/luban_lite/
platforms/linux/tina/
```

当前代码仍使用早期 RTOS 验证目录：

```text
platforms/rtos/demo_family/
```

其中真实 RT-Thread port 已经放在：

```text
platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c
platforms/rtos/demo_family/hal_port/
platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c
```

后续如果目录需要按厂商 SDK 家族细分，再从 `demo_family` 迁移到正式目录；当前不为了改名阻塞业务开发。

3. 新增 `CMakeLists.txt`。

4. 新增启动入口目录。

```text
startup/
```

5. 新增 OSAL、HAL、能力表、路径等目录。

```text
osal_port/
hal_port/
capability/
paths/
component_port/
board/
config/
```

6. 保证新平台目录只放该平台适配代码，不放业务代码。

7. RTOS 平台补 target 描述文件。

```text
targets/<target>.yaml
```

target 描述文件负责绑定 SDK 仓库、SDK ref、chip、board、kernel、defconfig 和输出目录。

## 第二阶段：启动入口

1. 接入平台启动入口。

```text
platforms/<family>/<platform>/startup/
```

2. 确认启动入口能进入框架生命周期。

3. 启动路径应保持清楚：

```text
平台 main 或 SDK app entry
  -> 平台 boot
  -> framework init
  -> app main
```

4. 启动入口不直接写业务 UI 页面、菜谱逻辑或设备业务。

当前 Luban-Lite 启动链路：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/helloworld/main.c
  -> third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/ep_app_main.c
    -> core/src/ep_framework.c
      -> app/main.c
```

## 第三阶段：OSAL

1. 确认平台需要实现哪些 OSAL 能力。

```text
时间
内存
线程
互斥锁
信号量
队列
```

2. 在平台 `osal_port/` 内补实现。

3. 先允许 stub，再逐步替换为真实实现。

4. 公共组件只包含 `osal/include/` 里的头文件。

当前 RT-Thread OSAL 已实现：

```text
platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c
```

覆盖内存、时间、sleep、线程 create/join、mutex、sem、queue。`ep_thread_join()` 只等待线程自然退出，不提供强制 stop。

## 第四阶段：HAL

1. 确认平台需要哪些 HAL 能力。

```text
GPIO
I2C
SPI
UART
PWM
ADC
```

2. 在平台 `hal_port/` 内补实现。

3. 没有真实硬件需求前，可以继续保持 stub。

4. 真实驱动接入后，需要补目标板冒烟测试。

当前 KI 板已经接入的真实 HAL port：

| 能力 | 代码路径 | 逻辑设备 |
| --- | --- | --- |
| UART | `platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtthread.c` | `console_uart`、`power_uart` |
| PWM | `platforms/rtos/demo_family/hal_port/ep_rtos_hal_pwm_rtthread.c` | `beep_pwm` |
| GPIO | `platforms/rtos/demo_family/hal_port/ep_rtos_hal_gpio_rtthread.c` | `lcd_sleep_gpio`、`panel_enable_gpio` |
| I2C | `platforms/rtos/demo_family/hal_port/ep_rtos_hal_i2c_rtthread.c` | `rtc_bus` |
| RTC | `platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtc_pcf8563.c` | `rtc` |

当前暂不推进：

- SPI：业务暂时不用，保留公共头文件，按需再补真实 port。
- ADC：业务暂时不用，保留公共头文件，按需再补真实 port。
- display/touch：由各芯片 LVGL display/input port 负责，不在 EP HAL 中二次封装。

## 第五阶段：平台能力表

1. 新增平台能力表。

```text
platforms/<family>/<platform>/capability/
```

2. 至少声明这些能力的真实状态：

```text
文件系统
配置持久化
日志
线程
LVGL
显示
触摸
GPIO
I2C
SPI
UART
PWM
ADC
网络
```

显示刷新和触摸输入优先由该芯片 SDK 自带的 LVGL display/input port 负责。EP 只维护 LVGL 生命周期和平台能力记录，不在 HAL 层二次封装 display/touch。

3. 应用和组件通过 `ep_platform_has_capability()` 查询能力，不直接判断平台名。

能力表用于描述平台可用能力，不等同于“EP 必须为每个能力封一套 HAL”。当前 display/touch 可以作为平台能力存在，但具体刷新和输入仍由 LVGL port 承担。

## 第六阶段：平台路径

1. 新增平台路径实现。

```text
platforms/<family>/<platform>/paths/
```

2. 确认这些路径能返回：

```text
配置文件
资源根目录
图片路径
字体路径
主题路径
```

3. host 可以使用仓库目录。

4. 真实平台可以使用安装目录、文件系统目录、flash 分区或 SDK 资源路径。

## 第七阶段：配置文件

1. 新增平台配置文件。

```text
config/profiles/<platform>.cfg
```

2. 配置内容只放小型运行参数和功能开关。

3. 不把大型资源、数据库、SDK 配置塞进 profile。

## 第八阶段：LVGL 来源声明

1. 先在 target 描述文件里声明 LVGL 来源。

```text
targets/<target>.yaml
```

```yaml
ui:
  lvgl_provider: sdk       # sdk/component/prebuilt/none
  lvgl_note: Luban-Lite SDK provides LVGL display and input ports.
```

2. 按 provider 决定放置方式。

| provider | 处理方式 |
| --- | --- |
| `sdk` | 原厂 SDK 已带 LVGL、显示和触摸 port，主工程不复制源码，不另建 display/touch HAL。 |
| `component` | Linux 等独立应用平台可以使用主工程组件或芯片专属 LVGL 仓库。 |
| `prebuilt` | 准备 `third_party/prebuilt/lvgl/<platform>/`，主工程只消费头文件、库和 manifest。 |
| `none` | 当前 target 不接 UI。 |

3. `prebuilt` 包内至少包含：

```text
include/
lib/
manifest
```

4. `prebuilt` manifest 需要说明：

```text
LVGL 版本
显示后端
输入后端
文件系统能力
图片解码能力
字体能力
```

5. 主工程不直接改该平台 `lv_conf.h`，应从对应 SDK、芯片专属 LVGL 仓库或 LVGL 预编译仓库重新产包。

## 第九阶段：资源目录

1. 新增平台资源目录。

```text
resources/<platform>/images
resources/<platform>/fonts
resources/<platform>/themes
```

2. 公共资源继续放在：

```text
resources/common/
```

3. 资源加载代码通过平台路径接口获取路径。

## 第十阶段：编译和冒烟测试

1. RTOS 平台先保证主工程能导出静态库包。

```text
out/ep/<target>/
  lib/libep_app_core.a
  include/
  manifest.json
```

2. 再保证 SDK 仓库能链接该静态库。

3. 再保证 SDK 输出最终固件。

```text
out/firmware/<target>/
```

4. 再保证最小程序能启动。

5. 再检查日志是否可用。

6. 再检查配置文件是否能加载。

7. 再检查资源路径是否能访问。

8. 最后再做 UI、触摸、硬件驱动等更复杂验证。

对当前 KI 板，基础判定已经完成：

- 镜像能构建和烧录。
- `app/main.c` 的 `EP_LOGI` 能从 UART1 控制台打印。
- UART/PWM/GPIO/I2C/RTC 真实 port 已接入。
- LCD/触摸由 Luban-Lite/LVGL port 验证。
- SD 卡文件系统使用 SDK 已提供能力；业务需要文件时按平台文件系统 API 读写。

每个平台最终都应该有自己的冒烟测试说明。真实目标板测试可能依赖串口、烧录器或专用 runner，不要求一开始接入 GitHub CI。
