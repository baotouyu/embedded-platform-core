# 仓库目录说明

这份文档说明主工程目录边界。后续整理目录、适配新平台、接入第三方库时，优先按这里的职责放置文件。

## 顶层目录

| 目录 | 职责 |
| --- | --- |
| `app/` | 平台无关的应用入口和业务流程。这里不能直接包含 Linux、RTOS、macOS 或厂商 SDK 头文件。 |
| `core/` | 框架启动、生命周期和公共编排逻辑。这里负责把组件按顺序初始化起来。 |
| `components/` | 可复用框架组件，例如日志、配置、文件、事件、定时器、UI。组件公共头文件必须保持平台无关。 |
| `osal/` | OS 抽象层公共接口，例如时间、内存、线程、互斥锁、信号量、队列。 |
| `hal/` | 硬件抽象层公共接口，例如 GPIO、I2C、SPI、UART、PWM、ADC。 |
| `platforms/` | 平台公共接口和平台适配代码。真实平台、host 调试平台、Linux 平台、RTOS 平台都在这里实现公共接口。 |
| `config/` | 运行配置样例。当前只保留已经使用的 `config/profiles/`。 |
| `resources/` | 平台资源目录，例如图片、字体、主题。主工程只放公共资源和 host 调试资源，真实平台资源按平台目录隔离。 |
| `cmake/` | CMake 模块和工具链文件。没有实际 preset 时不保留空 `cmake/presets/`。 |
| `tests/` | host 单元测试和 API 契约测试。集成测试、目标板冒烟测试需要真实需求时再新增目录。 |
| `docs/` | 中文设计、流程、移植和测试文档。 |
| `tools/` | 辅助脚本。没有实际 CI 脚本时不保留空 `tools/ci/`。 |
| `third_party/` | 第三方源码、预编译包，以及可选的 SDK 子模块入口。 |

主工程不再保留顶层 `vendor/` 空目录。大型厂商 SDK 放到外部 SDK 仓库管理。RTOS 平台的主线规则是：主工程编译出 `libep_app_core.a`、头文件和 manifest，芯片 SDK 仓库负责链接、打包和输出最终固件。

## 应用目录

`app/main.c` 只保留应用入口函数 `app_main()`，负责串起应用上下文、服务启动、自检和主流程。业务逻辑不继续堆在入口文件里。

当前应用骨架为：

```text
app/
  main.c                         # app_main 薄入口
  app_core.c                     # 应用生命周期和服务启动顺序
  include/app_context.h          # 应用上下文
  include/app_core.h             # 应用生命周期接口
  selftest/app_selftest.c        # 当前 timer/event 生命周期冒烟
  services/                      # 业务友好的设备服务边界
```

`app/services/` 是业务服务层，不替代 HAL，也不直接维护板级 pinmux。它负责把业务常用动作收口成清晰接口，例如蜂鸣器、RTC、LCD sleep 和电源板 UART。后续写业务时优先从服务层调用，再由服务层按需要使用 `hal/include/` 或 SDK 已提供能力。

当前第一版服务边界：

```text
app/services/beep_service.*
app/services/rtc_service.*
app/services/lcd_sleep_service.*
app/services/power_board_service.*
```

电源板协议还没有实现，`power_board_service` 当前只保留初始化和写入接口骨架。协议帧格式、校验、重发和状态解析应在协议明确后单独补。

## 第三方目录

`third_party/external/` 放第三方源码快照，例如 EasyLogger、cJSON 和 SQLite。这里可以包含少量为了主工程编译必须保留的本地 port 文件。

当前源码快照包括 EasyLogger、cJSON 和 SQLite。cJSON 暴露为 `ep_thirdparty_cjson`，SQLite 暴露为 `ep_thirdparty_sqlite`。这两个目标只负责第三方库接入，不代表主工程已经有 JSON 组件或数据库组件。

`third_party/prebuilt/` 放预编译包，例如：

```text
third_party/prebuilt/lvgl/host_macos
third_party/prebuilt/vendor/<platform>
```

预编译包必须包含头文件、静态库和 manifest。主工程只消费这些产物，不在这里直接改第三方库配置。

不要直接修改预编译包里的 lv_conf.h。正式修改 LVGL 配置时，先去对应的 `lvgl-prebuilt-*` 或芯片专属 LVGL 仓库修改源头配置并重新产包，再同步回主工程。

LVGL 的归属由 `targets/<target>.yaml` 的 `ui.lvgl_provider` 声明：

| provider | 放置和维护方式 |
| --- | --- |
| `sdk` | RTOS 原厂 SDK 已经内置 LVGL、显示和触摸 port。主工程不复制 LVGL 源码，不在 `components/` 另建该平台 LVGL。 |
| `component` | Linux 这类应用独立交叉编译平台可以放主工程组件或芯片专属组件仓库，例如 F133 的 `sunxi_lvgl_v9.1`。 |
| `prebuilt` | 主工程消费已经产好的 LVGL 头文件、库和 manifest，例如 host/macOS 预编译包。 |
| `none` | target 不提供 UI/LVGL。 |

`components/ui` 是 EP 自己的 UI 生命周期薄封装，只负责 `lv_init`、tick 和 handler 这类公共生命周期，不代表主工程接管每个平台的 LVGL port。RTOS SDK 自带 LVGL 时，业务 UI 可以按该 SDK 暴露的 LVGL 使用方式写，底层显示刷新和触摸输入继续归 SDK 维护。

厂商 SDK 适配不把完整 SDK 放到 `third_party/prebuilt/`。RTOS SDK 先在外部 SDK 仓库里处理原厂工程、工具链、芯片差异和固件打包，再由主工程导出 `out/ep/<target>` 静态库包给 SDK 链接。只有少量确实需要被主工程直接消费的厂商预编译库，才放到 `third_party/prebuilt/vendor/<platform>`。

需要主工程明确锁定 SDK 版本时，把 SDK 仓库作为 `git submodule` 放在：

```text
third_party/sdk/<sdk.name>/
```

这个目录只用于 submodule gitlink，不用于直接提交大型 SDK 源码快照。submodule 默认固定到主工程记录的 commit，不会自动跟随 SDK 上游更新；主动升级规则见 `docs/porting/rtos-sdk-library-model.md`。

## 平台目录

`platforms/include/` 放平台公共接口，例如平台能力注册表。组件和应用需要了解平台能力时，优先包含这里的公共头文件，不直接包含具体平台目录里的头文件。

平台资源路径接口放在：

```text
platforms/include/ep_platform_paths.h
```

这个接口负责告诉应用和组件当前平台的配置文件路径、资源根目录，以及图片、字体、主题这类资源的拼接路径。组件不应该自己硬编码 `resources/host` 或真实平台路径，而是通过平台资源路径接口获取。

`platforms/host/posix/` 是本机调试平台，目前负责 macOS host 程序和 SDL2/LVGL demo。没有实际公共代码时，不保留 `platforms/host/common/`、`platforms/linux/common/` 或 `platforms/rtos/common/` 空目录。

`platforms/linux/demo_family/` 是 Linux 平台边界占位。`platforms/rtos/demo_family/` 最初也是 RTOS 边界占位，现在已经承载当前 Luban-Lite/KI 板真实 RT-Thread port，包括：

```text
platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c
platforms/rtos/demo_family/hal_port/
platforms/rtos/demo_family/component_port/ep_rtos_default_devices.c
```

后续真实芯片适配如果需要长期维护，应按 SDK 家族新增具体平台目录，例如：

```text
platforms/rtos/artinchip/luban_lite/
platforms/linux/allwinner/<chip>/
```

当前不为了改目录名阻塞业务开发。RTOS 具体芯片、板子、内核和 defconfig 不靠平台目录堆深层级表达，而是通过 `targets/<target>.yaml` 描述。相关规则见 `docs/porting/rtos-sdk-library-model.md`。

## 组件目录

已经实现的组件需要有：

```text
components/<name>/include
components/<name>/src
components/<name>/CMakeLists.txt
```

不为远期想法预留空目录。网络、菜谱解析、用户数据等方向暂时不放空目录，等需求明确并开始实现时，再新增对应组件目录。

当前真实组件包括：

```text
components/config
components/device
components/event
components/file
components/log
components/timer
components/ui
```

## 资源目录

资源目录先按“公共资源”和“平台资源”拆开：

```text
resources/common/
resources/host/images
resources/host/fonts
resources/host/themes
```

`resources/common/` 放所有平台都可以复用的资源。当前如果没有真实公共资源，不强行保留 `images`、`fonts`、`themes` 空子目录。`resources/host/` 放本机调试资源。后续接入真实平台时，可以新增类似下面的目录：

```text
resources/jxc_<chip>/
resources/allwinner_<chip>/
```

当前 host/macOS 平台约定：

| 类型 | 路径 |
| --- | --- |
| 配置文件 | `config/profiles/host.cfg` |
| 资源根目录 | `resources/host` |
| 图片 | `resources/host/images` |
| 字体 | `resources/host/fonts` |
| 主题 | `resources/host/themes` |

平台资源路径接口只负责路径约定和路径拼接，不负责扫描目录、解码图片、加载字体或管理 LVGL 对象。这些能力后续应该放在具体组件或对应平台适配里。

## 本地生成文件

以下内容是本地生成或工具缓存，不应该提交：

```text
build/
.worktrees/
.pytest_cache/
__pycache__/
.DS_Store
```

如果这些文件出现在工作区，优先清理本地文件或补充 `.gitignore`，不要把它们混进功能提交。
