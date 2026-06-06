# Luban-Lite 构建和链接流程

本文记录主工程如何把 `libep_app_core.a` 接入 Luban-Lite，并由 SDK 生成最终固件。

## 核心边界

RTOS target 的最终镜像不由主工程直接链接。主工程负责生成 EP 应用核心静态库，Luban-Lite SDK 负责最终链接、打包和镜像输出。

```text
<repo-root>
  -> targets/<target>.yaml
  -> out/ep/<target>/lib/libep_app_core.a
  -> third_party/sdk/sdk-artinchip-luban-lite/targets/<target>.env
  -> third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/
  -> third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/tools/onestep.sh
  -> Luban-Lite SCons
  -> third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/output/<project_config>/images/*.img
  -> out/firmware/<target>/
```

不能把边界反过来：

- 主工程不接管 Luban-Lite 链接脚本。
- 主工程不接管 bootloader、BSP、pinmux 和镜像打包。
- 业务代码不直接包含 Luban-Lite SDK 私有头文件。

## target 入口

KI-141103-480p 当前 target：

```text
artinchip_d12x_lubanlite_ki_141103_480p
```

对应描述文件：

```text
targets/artinchip_d12x_lubanlite_ki_141103_480p.yaml
```

关键字段：

```yaml
platform:
  family: rtos
  vendor: artinchip
  sdk_family: luban-lite
  chip: d12x
  board: KI-141103-480p
  kernel: rt-thread

sdk_config:
  defconfig: d12x_KI-141103-480p_rt-thread_helloworld_defconfig
```

SDK adapter 侧 env 文件：

```text
third_party/sdk/sdk-artinchip-luban-lite/targets/artinchip_d12x_lubanlite_ki_141103_480p.env
```

关键字段：

```sh
TARGET_NAME=artinchip_d12x_lubanlite_ki_141103_480p
CHIP=d12x
BOARD=KI-141103-480p
KERNEL=rt-thread
DEFCONFIG=d12x_KI-141103-480p_rt-thread_helloworld_defconfig
SDK_APP_STAGING_DIR=application/rt-thread/ep_app
```

## 构建命令

在 Linux 或 Docker Ubuntu 20.04 环境中执行：

```bash
./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p
```

清理后重新构建：

```bash
./build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p --clean
```

Docker 内测试时要使用普通用户，避免生成 root 权限文件：

```bash
docker exec -u yuwei -w <repo-root> <container> \
  bash -lc './build.sh build-firmware artinchip_d12x_lubanlite_ki_141103_480p'
```

如果误用 root 构建导致权限问题，常见现象是：

```text
Permission denied
rm: cannot remove ...
Fatal error: can't create ... Permission denied
```

这时应先修正文件属主，再用普通用户重新构建。

## 构建阶段

`build-firmware` 对 Luban-Lite target 的主要流程是：

```text
./build.sh build-firmware <target>
  -> tools/scripts/build_target_firmware.sh
    -> 读取 targets/<target>.yaml
    -> tools/scripts/check_target_env.sh 检查 SDK 环境
    -> 使用 SDK 工具链构建 EP 静态库
    -> tools/scripts/export_target.sh 导出 out/ep/<target>/
    -> tools/scripts/validate_ep_package.sh 校验 manifest
    -> third_party/sdk/sdk-artinchip-luban-lite/scripts/build_firmware.sh
      -> 读取 third_party/sdk/sdk-artinchip-luban-lite/targets/<target>.env
      -> 复制 ep_app 到 Luban-Lite SDK
      -> 进入 upstream/luban-lite
      -> source tools/onestep.sh
      -> lunch <defconfig>
      -> 调用 makebootandapp
      -> 收集镜像和日志到 out/firmware/<target>/
```

注意：

- Luban-Lite 的 `m` 是 shell alias，非交互式脚本里不能稳定直接调用。
- 构建脚本应 source `tools/onestep.sh` 后调用 alias 背后的函数，例如 `makebootandapp`。
- 清理时使用对应的底层函数，例如 `cleanbootandapp`。

## EP app 放置位置

主工程导出的 EP 应用包会复制到 Luban-Lite SDK：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/application/rt-thread/ep_app/
```

典型结构：

```text
application/rt-thread/ep_app/
  include/
  lib/
    libep_app_core.a
  ep_app_main.c
  SConscript
  manifest.json
```

其中：

- `lib/libep_app_core.a` 是主工程业务和公共组件静态库。
- `include/` 是 SDK 侧编译入口需要的公共头文件。
- `ep_app_main.c` 提供 Luban-Lite 到 EP framework 的入口。
- `SConscript` 负责把静态库加入 Luban-Lite 链接。

`application/rt-thread/ep_app/` 是构建生成的 staging 内容，不应该作为业务源码直接维护。

## 启动链路

当前启动链路：

```text
Luban-Lite application/rt-thread/helloworld/main.c
  -> application/rt-thread/ep_app/ep_app_main.c
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
```

`app/main.c` 中的日志如果能在串口看到，说明：

- `libep_app_core.a` 已经被链接进镜像。
- `ep_lubanlite_app_main()` 已经进入 framework。
- `app/main.c`、`app/app_core.c`、`app/selftest/`、`app/services/` 已经进入最终链接。
- EasyLogger 的 RT-Thread 输出 port 已经工作。

## 产物位置

Luban-Lite SDK 原始产物位于：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/output/<project_config>/images/
```

KI 板当前项目配置：

```text
d12x_KI-141103-480p_rt-thread_helloworld
```

典型镜像：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/output/d12x_KI-141103-480p_rt-thread_helloworld/images/d12x_demo68-nor_v1.0.0.img
```

主工程收集后的固件目录：

```text
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/
```

构建日志：

```text
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/build.log
```

该目录通常包含：

```text
out/firmware/artinchip_d12x_lubanlite_ki_141103_480p/
  build.log
  build_manifest.txt
  d12x.bin
  d12x.elf
  d12x.map
  *.img
```

烧录时优先使用 Luban-Lite 输出的整包镜像 `*.img`。调试链接问题时看 `d12x.elf`、`d12x.map` 和 `build.log`。

## 工具链位置

交叉工具链从 Release 下载后恢复到原厂 SDK 预期位置：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite/toolchain/
```

检查路径：

```text
toolchain/bin/riscv64-unknown-elf-gcc
```

该目录属于大文件工具链，不应提交到 git。SDK 仓库应通过 `.gitignore` 或 `.git/info/exclude` 忽略它。

## 常见失败

### 找不到工具链

现象：

```text
缺失 RISC-V 工具链
```

处理：

```bash
./build.sh install-env artinchip_d12x_lubanlite_ki_141103_480p
```

或通过本地归档：

```bash
EP_TOOLCHAIN_ARCHIVE=/path/to/toolchain.tar.gz ./build.sh install-env artinchip_d12x_lubanlite_ki_141103_480p
```

### app 符号未链接

现象：

```text
undefined reference to `ep_lubanlite_app_main'
```

重点检查：

- `application/rt-thread/ep_app/ep_app_main.c` 是否已复制。
- `SConscript` 是否把 `libep_app_core.a` 加入链接。
- helloworld `main.c` 是否声明并调用 `ep_lubanlite_app_main()`。

### 日志没打印

重点检查：

- `ep_lubanlite_app_main()` 是否调用 `ep_framework_start()`。
- `ep_framework_init()` 是否调用 `ep_log_init()`。
- EasyLogger RT-Thread port 是否通过 `rt_kprintf()` 输出。
- 当前 log level 是否允许 `EP_LOGI`。

### root 权限污染

现象：

```text
Permission denied
```

处理：

- Docker 内使用 `docker exec -u yuwei`。
- 清理或修正 root 创建的 `build/`、`out/`、`application/rt-thread/ep_app/` 文件属主。
