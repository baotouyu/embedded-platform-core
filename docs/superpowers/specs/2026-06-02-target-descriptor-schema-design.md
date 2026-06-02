# Target 描述规范设计

## 背景

主工程已经具备 RTOS SDK 外部仓库调度链路：

```text
target 描述文件
  -> 准备外部 SDK 仓库
  -> 调用 SDK scripts/prepare.sh
  -> 导出主工程静态库包
  -> 调用 SDK scripts/build_firmware.sh
  -> 输出固件目录
```

当前只有 `targets/host_rtos_demo.yaml`，字段还是早期占位格式。后续接入匠芯创 Luban-Lite、全志 Linux 或其他 RTOS 芯片时，如果继续临时加字段，target 文件会变成脚本和口头约定的混合体。需要先把 target 描述规范定下来。

## 目标

本次目标是定义一套清晰、够用、可扩展的 target 描述规范：

- 用 target 作为最终构建入口。
- 明确平台、厂商、SDK、芯片、板子和输出产物之间的关系。
- 让主工程构建脚本只读取稳定字段，不散落芯片名判断。
- 支持 SDK 仓库放在主工程外部，由 `sdk.name`、`sdk.repo` 和 `sdk.ref` 管理来源。
- 为后续真实 target，例如 `artinchip_d121_lubanlite_demo`，预留字段。

## 不做什么

本次不做以下内容：

- 不接入真实 Luban-Lite 编译。
- 不拉取或修改原厂 SDK 源码。
- 不实现通用 YAML 解析器。
- 不改 SDK 仓库构建逻辑。
- 不新增真实芯片驱动。
- 不把 SDK 本地路径写进 target 文件。
- 不处理烧录、串口、板级冒烟测试。

## 推荐结构

target 文件继续放在：

```text
targets/<target>.yaml
```

第一版规范使用以下结构：

```yaml
target: artinchip_d121_lubanlite_demo

platform:
  family: rtos
  vendor: artinchip
  sdk_family: luban-lite
  chip: d121
  board: demo
  kernel: rt-thread

sdk:
  name: sdk-artinchip-luban-lite
  repo: https://github.com/baotouyu/sdk-artinchip-luban-lite.git
  ref: main

toolchain:
  source: sdk

sdk_config:
  defconfig: d121_demo_rt-thread_ep_app_defconfig

output:
  ep_package: out/ep/artinchip_d121_lubanlite_demo
  firmware: out/firmware/artinchip_d121_lubanlite_demo
```

现有平铺字段：

```yaml
os:
vendor:
sdk_family:
chip:
board:
kernel:
```

应该迁移到 `platform:` 分组里。这样 target 文件更接近真实语义，也能避免顶层字段越来越多。

## 字段说明

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `target` | 是 | 最终构建目标名，必须和文件名一致。 |
| `platform.family` | 是 | 平台大类，例如 `host`、`linux`、`rtos`。 |
| `platform.vendor` | 是 | 厂商或平台来源，例如 `host`、`artinchip`、`allwinner`。 |
| `platform.sdk_family` | 是 | SDK 家族，例如 `demo`、`luban-lite`、`tina`。 |
| `platform.chip` | 是 | 芯片或芯片系列，例如 `host`、`d121`、`d12x`。 |
| `platform.board` | 是 | 板子或产品硬件版本，例如 `demo`、`demo68-nor`、`product-v1`。 |
| `platform.kernel` | 是 | 内核或运行环境，例如 `none`、`linux`、`rt-thread`。 |
| `sdk.name` | RTOS 必填 | 外部 SDK 仓库本地目录名。 |
| `sdk.repo` | RTOS 必填 | SDK 仓库地址。 |
| `sdk.ref` | RTOS 必填 | SDK 分支、tag 或 commit。 |
| `toolchain.source` | 是 | 工具链来源，第一版支持 `host` 和 `sdk` 两种语义。 |
| `sdk_config.defconfig` | 可选 | SDK 内部使用的 defconfig 或板级配置名。 |
| `output.ep_package` | 是 | 主工程静态库导出目录。 |
| `output.firmware` | RTOS 必填 | SDK 最终固件输出目录。 |

## 命名规则

target 名建议使用：

```text
<vendor>_<chip>_<sdk_family>_<board>
```

示例：

```text
artinchip_d121_lubanlite_demo
artinchip_d12x_lubanlite_demo68_nor
allwinner_t113_linux_product_v1
host_rtos_demo
```

规则：

- 全部小写。
- 单词之间使用下划线。
- board 内部如果需要区分 flash、屏幕或硬件版本，也使用下划线。
- target 名不写本地路径、不写开发者姓名、不写临时目录。
- 如果一个芯片有多个板子，每个板子单独一个 target。

## 主工程解析边界

主工程第一版只需要解析这些稳定字段：

```text
target
platform.family
platform.vendor
platform.sdk_family
platform.chip
platform.board
platform.kernel
sdk.name
sdk.repo
sdk.ref
toolchain.source
output.ep_package
output.firmware
```

`sdk_config` 下的字段属于 SDK 仓库内部契约。主工程可以把 target 名传给 SDK，也可以后续把 target 文件路径传给 SDK，但主工程不应该理解每个 SDK 的所有配置细节。

第一版仍然可以用现有 shell 解析方式，只支持固定字段，不引入完整 YAML 解析器。等字段复杂到 shell 难以维护时，再考虑用 Python 小工具统一解析和校验。

## SDK 仓库边界

target 文件只描述 SDK 来源：

```yaml
sdk:
  name: sdk-artinchip-luban-lite
  repo: https://github.com/baotouyu/sdk-artinchip-luban-lite.git
  ref: main
```

它不描述本地 SDK 放在哪里。本地路径由 `EP_SDK_ROOT` 或默认外部缓存目录决定。

SDK 仓库需要提供稳定入口：

```text
scripts/prepare.sh --target <target>
scripts/build_firmware.sh --target <target> --ep-package <path> --out <path>
```

如果后续 SDK 需要读取更多 target 字段，优先让 SDK 仓库自己维护 target 映射，或者由主工程传入 target 文件路径。不要把 SDK 内部 defconfig、SCons 参数、链接脚本路径全部摊到主工程脚本里。

## 迁移步骤

第一阶段只做规范和兼容迁移：

1. 新增 target 描述规范文档。
2. 把 `targets/host_rtos_demo.yaml` 从平铺字段迁移到 `platform:` 分组。
3. 更新脚本解析逻辑，使 `build-firmware`、`prepare-sdk` 和 `export-target` 读取新字段。
4. 保留现有 `host_rtos_demo` 的 stub 联调能力。

第二阶段增加真实占位 target：

1. 新增 `targets/artinchip_d121_lubanlite_demo.yaml`。
2. 先指向 `sdk-artinchip-luban-lite`。
3. 暂时仍使用 SDK stub 构建入口。
4. 验证 `prepare-sdk` 和 `build-firmware` 可以按新 target 走完整链路。

第三阶段再进入 SDK 仓库：

1. 在 `sdk-artinchip-luban-lite` 中接真实 Luban-Lite upstream。
2. 根据 target 名映射 defconfig、工具链和板级构建目录。
3. 让 SDK 仓库真正链接主工程导出的 `libep_app_core.a`。
4. 输出真实固件。

## 测试设计

主工程需要补以下测试：

- 检查 `host_rtos_demo.yaml` 使用 `platform:` 分组。
- 检查 target 文件名和 `target` 字段一致。
- 检查必填字段存在。
- 检查脚本能从 `platform:` 分组读取字段。
- 检查 `prepare-sdk` 仍能根据 `sdk.name`、`sdk.repo` 和 `sdk.ref` 准备 SDK。
- 检查 `build-firmware` 仍能调用 SDK `prepare.sh` 和 `build_firmware.sh`。
- 检查缺少必填字段时给出中文错误。

测试仍然用 fake SDK 仓库，不依赖真实 Luban-Lite。

## 后续方向

target 描述规范稳定后，下一步可以做：

- 新增 `artinchip_d121_lubanlite_demo` 占位 target。
- 给 `targets/` 增加统一校验脚本，例如 `./build.sh validate-targets`。
- 把 target 信息写入 `out/ep/<target>/manifest.json`。
- 让 SDK 构建输出 `build_manifest.txt` 或 `build_manifest.json` 时记录 target、SDK ref、EP commit 和构建模式。

