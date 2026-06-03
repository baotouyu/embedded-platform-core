# EP 导出包校验设计

## 背景

当前 RTOS 构建链路已经形成：

```text
targets/<target>.yaml
  -> prepare-sdk
  -> export-target
  -> out/ep/<target>/manifest.json
  -> build-firmware
  -> SDK scripts/build_firmware.sh
```

`export-target` 已经把 target 的 `platform`、`sdk` 和 `toolchain` 元数据写入 `manifest.json`。但 `build-firmware` 目前只把 `out/ep/<target>` 路径传给 SDK，并没有校验这个导出包是否真的匹配当前 target。

后续适配多个芯片、多个板子后，最容易出错的是拿错导出包：例如当前构建 D12x，但传入的是其他芯片或其他板级 target 的 `out/ep`。这种错误如果直接进入 SDK 构建，问题会变得难查。

## 目标

新增 EP 导出包校验入口，在进入 SDK 固件构建前确认：

- `manifest.json` 存在且可读取。
- manifest 里的 `target` 和命令 target 一致。
- manifest 里的 `platform` 与 `targets/<target>.yaml` 一致。
- manifest 里的 `sdk` 与 `targets/<target>.yaml` 一致。
- manifest 里的 `toolchain` 与 `targets/<target>.yaml` 一致。

这一步只校验主工程导出的静态库包和 target 描述是否匹配，不拉取 SDK，不进入真实交叉编译，不判断 SDK 内部配置是否正确。

## 非目标

本次不做这些事情：

- 不校验静态库 ABI、CPU 架构、编译器版本或链接脚本。
- 不解析 SDK 的 defconfig 或工程配置。
- 不修改 SDK 仓库的 `scripts/build_firmware.sh` 协议。
- 不引入 Python 或第三方 JSON 工具作为主流程依赖。
- 不改变直接 `export-ep` 的兼容行为。

## 命令入口

新增脚本：

```text
tools/scripts/validate_ep_package.sh
```

建议参数：

```text
tools/scripts/validate_ep_package.sh --target <target> --ep-package <路径> [--repo-root <路径>]
```

同时在 `build.sh` 增加命令：

```text
./build.sh validate-ep-package <target> [--ep-package <路径>]
```

如果用户不传 `--ep-package`，默认从 `targets/<target>.yaml` 的 `output.ep_package` 读取。

## 构建链路接入

`build_target_firmware.sh` 在执行完 `export_target.sh` 后、调用 SDK `scripts/build_firmware.sh` 前，自动执行：

```text
validate_ep_package.sh --target <target> --ep-package <EP_PACKAGE_DIR>
```

也就是流程变成：

```text
prepare_target_sdk.sh
SDK scripts/prepare.sh
export_target.sh
validate_ep_package.sh
SDK scripts/build_firmware.sh
```

这样可以保证进入 SDK 之前，主工程导出的包至少和当前 target 描述一致。

## 校验字段

第一版只校验稳定字段：

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
```

这些字段来自 `targets/<target>.yaml`，并且已经由 `export-target` 写入 `manifest.json`。

如果字段缺失或不一致，脚本用中文报错，例如：

```text
EP 导出包校验失败：manifest platform.chip 为 d122，target 描述为 d12x
```

## JSON 读取策略

当前 manifest 由主工程 shell 脚本生成，格式稳定。为了保持构建脚本轻量，第一版使用 shell 工具读取 manifest 字段。

约束：

- 只读取当前 manifest 中固定的简单字符串字段。
- 不支持复杂 JSON 查询。
- 不把这个读取逻辑扩展成通用 JSON parser。

如果后续 manifest 结构明显复杂，再考虑改成 Python 标准库 `json` 读取，或者引入更明确的工具依赖。

## 测试策略

新增 host unit 测试覆盖：

- `build.sh help` 包含 `validate-ep-package`。
- 校验脚本存在，并复用 `target_descriptor.sh`。
- 当前仓库真实 target 经过 `export-target` 后可以通过校验。
- 缺少 `manifest.json` 时失败。
- manifest `target` 不一致时失败。
- manifest `platform.chip` 不一致时失败。
- manifest `sdk.name` 不一致时失败。
- `build-firmware` 在调用 SDK 构建前会先调用导出包校验。

手动验证：

```sh
./build.sh configure
cmake --build build --target ep_app_core_export
./build.sh export-target artinchip_d12x_lubanlite_demo --clean
./build.sh validate-ep-package artinchip_d12x_lubanlite_demo
./build.sh test
```

## 后续方向

本次完成后，`manifest.json` 不再只是记录信息，而会参与构建安全校验。后续可以继续往两个方向增强：

- SDK 仓库也读取 `manifest.json`，在 SDK 侧二次确认 target、芯片、板级配置。
- 导出包增加编译器、架构、ABI 等更强元数据，再逐步扩展校验范围。
