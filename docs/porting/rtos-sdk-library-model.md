# RTOS SDK 静态库接入模型

本文记录 RTOS 芯片平台的正式接入方向。这个模型适用于匠芯创 Luban-Lite 这类原厂 SDK，也适用于后续其他 RTOS 芯片 SDK。

## 核心结论

RTOS 平台不由主工程直接生成最终固件。主工程先用目标 SDK 对应的交叉编译工具链编译出应用核心静态库，再交给芯片 SDK 链接、打包和烧录。

```text
embedded-platform-core
  -> libep_app_core.a + include + manifest
  -> 芯片 SDK 仓库
  -> 固件镜像
```

主工程输出的是应用框架库。芯片 SDK 输出的是最终固件。

这个边界不能反过来：不要把 RTOS SDK 大量源码放进主工程，也不要让主工程接管 SDK 的启动代码、链接脚本、内存布局和镜像打包。

## 仓库职责

### 主工程职责

`embedded-platform-core` 负责：

- 应用层和公共业务逻辑。
- 框架启动、生命周期和组件编排。
- OSAL、HAL、组件公共接口。
- 平台无关组件，例如日志、配置、文件、事件、定时器、UI。
- 目标平台的薄适配层。
- target 描述文件和构建调度入口。
- 导出给 RTOS SDK 使用的静态库包。

主工程不能直接依赖具体芯片 SDK 的内部目录，也不能让业务代码包含原厂 SDK 头文件。

### SDK 仓库职责

外部 SDK 仓库负责：

- 保存和维护原厂 SDK。
- 跟进原厂 SDK upstream 更新。
- 管理启动代码、中断向量、链接脚本和内存布局。
- 管理 RTOS 内核、BSP、驱动和板级配置。
- 管理 defconfig、SCons、Makefile 或原厂构建系统。
- 链接主工程导出的 `libep_app_core.a`。
- 生成最终固件、map、elf、bin 和烧录包。
- 提供烧录脚本和板级冒烟测试脚本。

例如匠芯创 Luban-Lite 使用独立仓库：

```text
sdk-artinchip-luban-lite
```

它基于官方仓库：

```text
https://gitee.com/artinchip/luban-lite.git
```

后续官方更新时，在 SDK 仓库里合并 upstream，不在主工程里直接同步 Luban-Lite 源码。

## SDK 获取和版本锁定策略

SDK 管理分成两件事：本地怎么拿到 SDK，以及工程如何锁定 SDK 版本。

### 外部缓存模式

如果没有检出 SDK 子模块，自动化脚本会使用外部缓存模式。主工程只保存 target 描述文件，描述 SDK 仓库地址和版本；本地 SDK 缓存放在主工程外部，避免污染主工程文件结构和 git 状态。

默认本地缓存路径：

```text
../sdks/<sdk.name>/
```

以当前仓库为例，默认会放在：

```text
项目父目录/
  embedded-platform-core/
  sdks/
    sdk-artinchip-luban-lite/
```

也可以通过环境变量指定统一缓存目录：

```bash
EP_SDK_ROOT=/opt/ep-sdks ./build.sh prepare-sdk artinchip_d121_lubanlite_demo68_nor
```

target 描述文件不要记录本地 SDK 路径。路径是每台开发机自己的事情，不属于工程配置。

### git submodule 锁定模式

如果项目需要由主工程明确记录“当前适配过的 SDK 版本”，可以把 SDK 仓库作为 `git submodule` 接入。submodule 是子仓库引用：主工程记录 SDK 仓库 URL、放置路径，以及固定到某个 commit 的 gitlink；主工程不是把 SDK 源码复制提交进自己的历史。

这个模式适合当前诉求：SDK 上游继续更新时，主工程不会自动跟随上游更新。主工程只会继续使用已经记录的那个 SDK commit，直到我们主动适配并提交新的 submodule 指针。

建议路径：

```text
third_party/sdk/<sdk.name>/
```

添加 SDK 子模块示例：

```bash
git submodule add <sdk-repo-url> third_party/sdk/sdk-artinchip-luban-lite
git -C third_party/sdk/sdk-artinchip-luban-lite checkout <sdk-commit-or-tag>
git add .gitmodules third_party/sdk/sdk-artinchip-luban-lite
git commit -m "chore: pin luban-lite sdk"
```

克隆主工程后拉取子模块：

```bash
git submodule update --init --recursive
```

日常开发不要运行：

```bash
git submodule update --remote
```

`git submodule update --remote` 会把子模块移动到远端分支的最新提交，和“主工程不受 SDK 上游更新影响”的目标相反。真实平台也不要使用浮动分支，例如 `main`、`master`、`develop` 作为稳定版本来源；`sdk.ref` 应填写已经验证过的 tag 或 commit。`host_rtos_demo` 这类 stub target 可以临时使用 `main`，但不能作为真实芯片 target 的版本锁定模板。

主动适配 SDK 新版本时，流程应该是：

```bash
git -C third_party/sdk/sdk-artinchip-luban-lite fetch --tags
git -C third_party/sdk/sdk-artinchip-luban-lite checkout <new-sdk-commit-or-tag>

./build.sh validate-targets
./build.sh build-firmware <target> --clean

git add third_party/sdk/sdk-artinchip-luban-lite targets/<target>.yaml
git commit -m "chore: update luban-lite sdk"
```

如果 SDK 已作为 submodule 接入，`targets/<target>.yaml` 仍然要保留 `sdk.name`、`sdk.repo` 和 `sdk.ref`，作为主工程和 SDK 仓库之间的契约；其中 `sdk.ref` 要和子模块当前 HEAD 对齐。当前 `prepare-sdk` 和 `build-firmware` 会优先复用 `third_party/sdk/<sdk.name>/`，没有检出子模块时才按 `sdk.repo` 和 `sdk.ref` 准备外部缓存。

## 产物格式

RTOS target 的主工程产物放在：

```text
out/ep/<target>/
```

建议结构：

```text
out/ep/<target>/
  lib/
    libep_app_core.a
  include/
    ep_framework.h
    其他需要暴露给 SDK 入口的公共头文件
  manifest.json
```

SDK 最终固件产物放在：

```text
out/firmware/<target>/
```

建议结构：

```text
out/firmware/<target>/
  firmware.elf
  firmware.bin
  firmware.map
  build_manifest.json
```

`manifest.json` 至少应该记录：

- target 名称。
- 主工程 git commit。
- SDK 名称和 SDK ref。
- 编译工具链信息。
- 编译选项摘要。
- 导出的库文件和头文件列表。

通过 `export-target` 导出的 `manifest.json` 会包含 target 元数据，包括 `platform`、`sdk` 和 `toolchain`。SDK 仓库可以用这些字段确认静态库包是否匹配当前芯片和板级构建。

## EP 导出包校验

进入 SDK 固件构建前，主工程会校验 EP 导出包是否匹配当前 target：

```sh
./build.sh validate-ep-package <target>
```

`build-firmware` 会在 `export-target` 之后、调用 SDK `scripts/build_firmware.sh` 之前自动执行这一步。校验内容包括 `manifest.json` 里的 `target`、`platform`、`sdk` 和 `toolchain` 是否与 `targets/<target>.yaml` 一致。

## 工具链规则

RTOS 静态库必须使用目标 SDK 对应的交叉编译工具链和编译参数生成，不能使用 host/macOS 的 clang 或本机 gcc 随便编译。

原因是 RTOS 平台对这些内容非常敏感：

- CPU 架构。
- ABI。
- 浮点参数。
- libc/newlib 配置。
- RTOS 配置宏。
- 芯片 SDK 头文件。
- 链接脚本和内存段约定。

因此构建流程应该先从 SDK 仓库获取工具链和必要编译参数，再回到主工程编译 `libep_app_core.a`。

## 平台、芯片、板子和 target

不同芯片平台不要只靠目录名管理，应该用 target 做最终入口。

建议概念如下：

| 概念 | 含义 | 示例 |
| --- | --- | --- |
| `platform.family` | 系统类型 | `host`、`linux`、`rtos` |
| `platform.vendor` | 厂商 | `artinchip`、`allwinner` |
| `platform.sdk_family` | SDK 家族 | `luban-lite`、`tina` |
| `platform.chip` | 芯片或芯片系列 | `d12x`、`d13x`、`d21x` |
| `platform.board` | 板子或产品硬件版本 | `demo68-nor`、`product-v1` |
| `platform.kernel` | RTOS 内核 | `rt-thread`、`freertos` |
| `target` | 最终可构建目标 | `artinchip_d12x_demo68_nor` |

`target` 是最终构建入口。它把 SDK、芯片、板子、内核、配置和输出目录组合起来。

## target 描述文件

当前已接入的 target 遵循一板一文件的原则，`targets/` 目录下每个 `.yaml` 代表一个可构建目标：

```text
targets/
  artinchip_d121_lubanlite_demo68_mmc.yaml
  artinchip_d121_lubanlite_demo68_nand.yaml
  artinchip_d121_lubanlite_demo68_nor.yaml
  artinchip_d121_lubanlite_hmi_nor.yaml
  host_rtos_demo.yaml                      ← 本地 stub 联调 target
```

> **命名说明**：当前 target 文件使用 `d121` 命名（如 `artinchip_d121_lubanlite_demo68_nor`），后续将随 SDK adapter 迁移到 `d12x` 系列命名（如 `artinchip_d12x_lubanlite_demo68_nor`）。`d121` 是具体芯片型号，属于 `d12x` 系列。

以下为 target 描述文件的结构示例（以目标命名约定 `d12x` 展示）：

```yaml
target: artinchip_d12x_lubanlite_demo68_nor

platform:
  family: rtos
  vendor: artinchip
  sdk_family: luban-lite
  chip: d12x
  board: demo68-nor
  kernel: rt-thread

sdk:
  name: sdk-artinchip-luban-lite
  repo: https://github.com/baotouyu/sdk-artinchip-luban-lite.git
  ref: e863ca3e2fc7c5a36f4db48a35ebf9c0ca66fa35

toolchain:
  source: sdk

sdk_config:
  defconfig: d12x_demo68-nor_rt-thread_helloworld_defconfig

output:
  ep_package: out/ep/artinchip_d12x_lubanlite_demo68_nor
  firmware: out/firmware/artinchip_d12x_lubanlite_demo68_nor
```

target 描述文件是主工程和 SDK 仓库之间的契约。主工程不应该在构建脚本里散落一堆芯片名判断。

`platform.chip` 使用芯片系列名，例如 `d12x`；`d121` 属于 `d12x` 系列。

## target 校验

新增或修改 target 后，先运行：

```bash
./build.sh validate-targets
```

这个命令只校验 `targets/*.yaml` 的结构和约定，不拉取 SDK，也不执行编译。它会检查 target 名、`platform:` 分组、SDK 来源字段、输出目录和禁止的本地 SDK 路径。

## 交互式 target 选择

`./build.sh` 支持交互式选择 target 和动作，不需要每次手敲完整 target 名：

```bash
./build.sh interactive
```

交互过程按层级逐步筛选：

1. **family** — 选择平台类型：`host`、`linux`、`rtos`
2. **vendor** — 选择厂商（从已有 target 中列出）
3. **sdk_family** — 选择 SDK 家族
4. **chip** — 选择芯片型号
5. **board** — 选择板级配置
6. **kernel** — 选择 RTOS 内核

选定 target 后，选择动作：

| 动作 | 说明 |
| --- | --- |
| `show-target` | 仅展示选中的 target 名 |
| `prepare-sdk` | 准备 SDK（检查/拉取/初始化） |
| `export-target` | 导出 EP 静态库包 |
| `build-firmware` | 调用 SDK 生成固件 |
| `full` | 依次执行 export-target → prepare-sdk → build-firmware |

也可以用非交互模式直接指定 target：

```bash
./build.sh export-target artinchip_d121_lubanlite_demo68_nor
./build.sh prepare-sdk artinchip_d121_lubanlite_demo68_nor
./build.sh build-firmware artinchip_d121_lubanlite_demo68_nor --clean
```

## 不同芯片平台管理规则

### 一个 SDK 家族一个 SDK 仓库

如果原厂 SDK 本身已经覆盖多个芯片，优先一个 SDK 家族一个仓库。

匠芯创 Luban-Lite 已经包含多个芯片系列，例如：

```text
d11x
d12x
d13x
d21x
g73x
```

所以先维护一个：

```text
sdk-artinchip-luban-lite
```

不要一开始拆成很多仓库：

```text
sdk-artinchip-d12x
sdk-artinchip-d13x
sdk-artinchip-d21x
```

只有当不同芯片的 SDK 来源、构建系统或维护方式完全不同，才考虑拆成多个 SDK 仓库。

### 一个具体板子一个 target

同一个芯片可以有多个板子或产品硬件版本。它们应该拆成不同 target。

示例：

```text
artinchip_d12x_demo68_nor
artinchip_d12x_demo68_nand
artinchip_d13x_demo88_nor
artinchip_d21x_demo100_nor
```

这样可以清楚表达：

- 用哪个芯片。
- 用哪个板子。
- 用哪种存储介质。
- 用哪个 defconfig。
- 输出目录在哪里。

### 平台目录按 SDK 家族收口

主工程里的平台适配目录建议按 SDK 家族收口：

```text
platforms/rtos/artinchip/luban_lite/
```

这里放主工程侧的薄适配代码，例如：

```text
osal_port/
hal_port/
capability/
paths/
component_port/
```

芯片和板子的具体差异优先放在 target 描述文件、SDK defconfig 和 SDK 仓库板级目录里，不在主工程重复维护一套大型 BSP。

### Linux 平台不要套 RTOS SDK 模型

Linux 平台优先作为用户态程序处理。Linux 已经提供统一的文件系统、线程、socket、输入、显示和设备接口，通常不需要把原厂 SDK 编译成最终固件工程。

因此 Linux target 更适合输出：

```text
可执行文件 + 配置文件 + 资源目录 + 必要动态库或静态库
```

RTOS target 更适合输出：

```text
主工程静态库包 + SDK 最终固件
```

这两类平台不要强行使用同一种产物模型。

## SDK 仓库标准入口

为了让主工程不理解每个 SDK 的内部细节，每个 RTOS SDK 仓库后续应该提供固定入口：

```text
sdk.yaml
scripts/prepare.sh
scripts/build_firmware.sh
scripts/flash.sh
```

建议主工程调用方式：

```bash
./build.sh build-firmware artinchip_d121_lubanlite_demo68_nor --clean
```

主工程内部调度顺序是：

```text
prepare-sdk
  -> SDK scripts/prepare.sh
  -> export-target
  -> SDK scripts/build_firmware.sh
```

主工程会先调用 SDK 的 `scripts/prepare.sh --target <target>`，确认 SDK 仓库结构和脚本契约可用；再把 `--target`、`--ep-package` 和 `--out` 传给 SDK 的 `scripts/build_firmware.sh`。SDK 内部可以继续使用 SCons、Makefile 或原厂脚本。主工程只认这些稳定入口，不解析 SDK 内部构建细节。

## 两仓库本地联调

主工程和 SDK 仓库按同级目录组织：

```text
C08/
  embedded-platform-core/
  sdk-artinchip-luban-lite/
```

`sdk-artinchip-luban-lite` 是独立维护的 SDK 适配仓库；它内部的 `upstream/luban-lite` 子模块固定到 `baotouyu/luban-lite` 这个 GitHub 维护副本。主工程不直接维护 Luban-Lite SDK 源码，只固定 `sdk-artinchip-luban-lite` 的提交。

`baotouyu/luban-lite` 从官方 Gitee v1.3.0 导入。两个超过 GitHub 普通 Git 单文件限制的 toolchain 压缩包放在 Release：

```text
https://github.com/baotouyu/luban-lite/releases/tag/luban-lite-v1.3.0-toolchains
```

### 当前 stub 联调流程

当前链路已打通。以 `host_rtos_demo` 为例：

```bash
EP_SDK_ROOT=/Users/yuwei/Documents/KitchenIdea/项目/C08 \
./build.sh build-firmware host_rtos_demo --clean
```

如果没有检出 SDK 子模块，命令会复用同级的 SDK 仓库：

```text
/Users/yuwei/Documents/KitchenIdea/项目/C08/sdk-artinchip-luban-lite
```

输出结果：

```text
out/ep/host_rtos_demo/
  lib/
    libep_app_core_export.a
  include/
    ...
  manifest.json

out/firmware/host_rtos_demo/
  firmware.bin
  build_manifest.txt
```

### 真实 D12x 系列 target 的当前状态

当前 `targets/` 下四个 ArtInChip D121 target（`artinchip_d121_lubanlite_demo68_*` 和 `artinchip_d121_lubanlite_hmi_nor`，属于 D12x 系列）已经完成以下能力：

- **EP 静态库包导出**：`export-target` 能从主工程编译产出 `libep_app_core_export.a` 并写入 `out/ep/<target>/`
- **Luban-Lite ep_app 接入包生成**：SDK adapter 的 `scripts/build_firmware.sh` 能为每个 target 生成对应的 Luban-Lite 应用目录结构（`application/rt-thread/ep_app/`），包含 `main.c` 和 `SConscript`
- **EP 导出包校验**：`validate-ep-package` 会在 `build-firmware` 流程中自动执行，校验 `manifest.json` 的 target 元数据与 `targets/<target>.yaml` 一致
- **SDK adapter 一板一 env**：每个 target 对应 `sdk-artinchip-luban-lite` 中的一个独立 env，env 名与 target 名对应，包含独立的 board 配置和 defconfig

当前 `host_rtos_demo` 的 `build_manifest.txt` 中记录 `mode=stub`，D121/Luban-Lite target 则记录 `mode=integration-skeleton`。两者都表示 EP 静态库导出和 SDK adapter 的目录结构已经打通，已生成 ep_app 接入包，但尚未调用真实 Luban-Lite scons 编译、链接和打包流程。后续接真实芯片时，优先在 SDK 仓库内部替换 `scripts/build_firmware.sh` 的实现，主工程命令和参数保持不变。

## 干净克隆验证

SDK 子模块接入后，建议用独立目录验证新机器能完整拉取并构建：

```bash
git clone --recursive https://github.com/baotouyu/embedded-platform-core.git ep-core-check
cd ep-core-check
git submodule status

./build.sh validate-targets
./build.sh configure
./build.sh build
./build.sh build-firmware artinchip_d121_lubanlite_demo68_nor --clean
```

`build-firmware` 会消费 `build/libep_app_core_export.a`，所以干净克隆后必须先执行 `configure` 和 `build`。如果只运行 `validate-targets`，不会生成静态库产物。

## Luban-Lite 接入方式

### SDK adapter 一板一 env

当前 `sdk-artinchip-luban-lite` 已采用一板一 env 的模式。每个 target 在 SDK 仓库中对应一个独立的 env：

| Target | SDK env | defconfig |
| --- | --- | --- |
| `artinchip_d121_lubanlite_demo68_mmc` | `artinchip_d121_lubanlite_demo68_mmc` | `d12x_demo68-mmc_rt-thread_helloworld_defconfig` |
| `artinchip_d121_lubanlite_demo68_nand` | `artinchip_d121_lubanlite_demo68_nand` | `d12x_demo68-nand_rt-thread_helloworld_defconfig` |
| `artinchip_d121_lubanlite_demo68_nor` | `artinchip_d121_lubanlite_demo68_nor` | `d12x_demo68-nor_rt-thread_helloworld_defconfig` |
| `artinchip_d121_lubanlite_hmi_nor` | `artinchip_d121_lubanlite_hmi_nor` | `d12x_hmi-nor_rt-thread_helloworld_defconfig` |

每个 env 包含：

```text
application/rt-thread/ep_app/
  main.c
  SConscript
```

`main.c` 调用主工程入口：

```c
#include "ep_framework.h"

int main(void)
{
    return ep_framework_start();
}
```

### 当前接入范围

- 只接入 RT-Thread helloworld 配置，不接入 baremetal_bootloader
- defconfig 从官方 `helloworld` defconfig 派生，应用入口切换为 `ep_app`
- SDK adapter 的 `scripts/build_firmware.sh` 负责根据 target 名选择对应 env、生成 Luban-Lite 应用目录结构

### 后续扩展

新增板子时，在 SDK 仓库中新增对应 env 和 defconfig 即可，主工程只需增加一个 target 描述文件。

## 当前落地状态

以下是目前已完成和尚未完成的事项：

| 事项 | 状态 |
| --- | --- |
| target 描述文件（4 个 D121 + 1 个 host_rtos_demo，D121 属于 D12x 系列） | 已完成 |
| `./build.sh interactive` 交互选择 | 已完成 |
| `validate-targets` 校验 target 描述文件 | 已完成 |
| host/macOS 端 EP 静态库编译和导出（`export-target`） | 已完成 |
| EP 导出包校验（`validate-ep-package`） | 已完成 |
| SDK adapter 一板一 env 目录结构 | 已完成 |
| `build-firmware` stub 模式（host_rtos_demo） | 已完成 |
| `build-firmware` integration-skeleton 模式（D121/Luban-Lite，已生成 ep_app 接入包） | 已完成 |
| Luban-Lite 真实 scons 编译固件 | 尚未接入 |
| toolchain 下载和 SDK 依赖初始化 | 尚未接入 |
| 真实板级烧录和冒烟测试 | 尚未接入 |

## 下一步设计

下一阶段将 `build-firmware` 从 stub 模式升级为真实 Luban-Lite 编译。以下是三个待实现的环节：

### inspect-sdk

在调用 SDK 编译前，先检查 SDK 环境是否就绪：

- toolchain 是否已安装且路径正确
- defconfig 是否存在于 SDK 仓库中
- SDK 依赖（子模块、构建工具）是否满足
- 输出预检报告，明确指出缺失项

设计目标：`inspect-sdk` 只检查不修改，让开发者清楚当前环境缺什么，再决定如何修复。

### bootstrap-sdk

自动初始化 SDK 依赖：

- 下载对应 toolchain（如果 `toolchain.source` 为 `sdk`，由 SDK 仓库管理下载逻辑）
- 初始化 SDK 内部子模块
- 安装必要的构建依赖（Python 包、系统工具等）

设计目标：新机器上执行一次 `bootstrap-sdk` 后，`build-firmware` 可以直接运行。

### build-firmware（真实模式）

替换当前的 stub `scripts/build_firmware.sh`，接入真实 Luban-Lite scons 编译：

- 将主工程导出的 `libep_app_core_export.a` 和头文件链接到 Luban-Lite ep_app 目录
- 调用 `scons --apply-defconfig=<defconfig>` 配置
- 调用 `scons` 编译生成 `.elf`、`.bin`、`.map`
- 将产物收集到 `out/firmware/<target>/`
- 生成 `build_manifest.json`（mode=real，包含编译时间、工具链版本、scons 日志摘要）

设计目标：主工程命令不变（`./build.sh build-firmware <target> --clean`），内部链路从 stub 切换为真实编译。

### 推荐推进顺序

1. 先在 SDK 仓库实现 `inspect-sdk` 和 `bootstrap-sdk`
2. 在 SDK 仓库实现 `scripts/build_firmware.sh` 的真实模式
3. 主工程侧 `build-firmware` 调用链路无需修改
4. 第一个真实芯片只选一个 target 跑通（建议 `demo68_nor`），不同时适配所有芯片

## 禁止事项

- 不把 Luban-Lite 源码直接提交进主工程。
- 不在主工程里大量解析 Luban-Lite 内部 SCons 细节。
- 不让业务代码直接包含 Luban-Lite、RT-Thread 或芯片 SDK 私有头文件。
- 不使用 host/macOS 编译器生成 RTOS 静态库。
- 不把不同芯片的板级配置复制到主工程里重复维护。
- 不为了远期芯片预留大量空目录。
