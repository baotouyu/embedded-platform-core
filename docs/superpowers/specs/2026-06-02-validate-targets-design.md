# Target 校验入口设计

## 背景

主工程已经把 target 描述迁移到 `platform:` 分组，并新增了 `artinchip_d12x_lubanlite_demo` 占位 target。现在 target 已经成为平台适配的正式入口：

```text
targets/<target>.yaml
  -> prepare-sdk
  -> export-target
  -> build-firmware
```

后续会继续增加匠芯创、全志和其他平台 target。如果 target 字段写错，最好在本地和 CI 里尽早发现，而不是等到 SDK 构建阶段才失败。

## 目标

新增统一命令：

```bash
./build.sh validate-targets
```

它负责校验 `targets/*.yaml` 是否符合当前 target 描述规范。这个命令只做结构和约定检查，不执行编译、不拉 SDK、不访问网络。

## 不做什么

本次不做以下内容：

- 不实现完整 YAML 解析器。
- 不调用 SDK 仓库。
- 不检查 SDK repo 是否真实存在。
- 不检查 `sdk.ref` 是否能 checkout。
- 不检查 defconfig 是否存在。
- 不生成 manifest。
- 不修改 `build-firmware` 行为。

## 校验规则

`validate-targets` 第一版校验以下规则：

1. `targets/` 目录必须存在。
2. 至少存在一个 `targets/*.yaml`。
3. 文件名必须和顶层 `target` 字段一致。
4. 必须存在 `platform.family`、`platform.vendor`、`platform.sdk_family`、`platform.chip`、`platform.board`、`platform.kernel`。
5. 必须存在 `toolchain.source`。
6. 必须存在 `output.ep_package`。
7. `platform.family=rtos` 时，必须存在 `sdk.name`、`sdk.repo`、`sdk.ref` 和 `output.firmware`。
8. 禁止使用旧顶层字段：`os`、`vendor`、`sdk_family`、`chip`、`board`、`kernel`。
9. 禁止在 target 文件里写本地 SDK 路径，例如 `.sdk`、`/Users/`、`/opt/`。

第一版不强制枚举 `platform.family` 的所有合法值，只要求字段存在。后续如果 target 变多，再增加枚举校验。

## 脚本设计

新增：

```text
tools/scripts/validate_targets.sh
```

脚本风格和现有构建脚本一致：

- POSIX shell。
- 支持 `--repo-root <路径>`，默认自动定位主工程根目录。
- 复用 `tools/scripts/target_descriptor.sh` 读取固定字段。
- 输出中文错误信息。
- 任意 target 校验失败时返回非零。
- 全部通过时输出 `target 校验通过：<数量>`。

`build.sh` 新增命令：

```text
validate-targets 校验 targets/*.yaml 描述文件
```

示例：

```bash
./build.sh validate-targets
```

## 错误输出

错误信息要能定位到具体文件和字段，例如：

```text
target 描述缺少 platform.family：targets/bad.yaml
target 文件名和 target 字段不一致：targets/foo.yaml
target 描述禁止使用旧顶层字段 os：targets/foo.yaml
target 描述不能写本地 SDK 路径：targets/foo.yaml
```

多个错误可以先第一版遇到第一个就退出。后续如果 target 数量变多，再考虑一次输出所有错误。

## 测试设计

新增测试：

```text
tests/host_unit/test_target_validation.py
```

测试覆盖：

- `./build.sh help` 展示 `validate-targets`。
- 当前仓库 target 可以通过校验。
- 临时 repo 里合法 target 可以通过校验。
- 文件名和 `target` 不一致时失败。
- 缺少 `platform.family` 时失败。
- RTOS target 缺少 `sdk.name` 时失败。
- RTOS target 缺少 `output.firmware` 时失败。
- 出现旧顶层字段 `os` 时失败。
- 出现本地 SDK 路径时失败。

这些测试只使用临时目录，不依赖真实 SDK 仓库。

## 后续方向

`validate-targets` 稳定后，下一步可以做：

- 让 CI 显式运行 `./build.sh validate-targets`。
- 把 target 信息写入导出包 `manifest.json`。
- 让 `build-firmware` 在执行前先调用 target 校验。
- 根据 target 数量增加枚举校验，例如 `platform.family` 只能是 `host`、`linux`、`rtos`。

