# SDK 指针同步入口设计

## 背景

当前主工程采用两层 SDK 锁定：

```text
embedded-platform-core
  -> third_party/sdk/sdk-artinchip-luban-lite
      -> upstream/luban-lite
```

每次修改 Luban-Lite upstream 后，会产生新的 upstream commit。SDK 适配仓库需要更新内部 submodule gitlink 和 `sdk.yaml`，主工程又需要更新 SDK submodule gitlink 和 `targets/*.yaml` 里的 `sdk.ref`。这些位置如果手工逐个改，容易漏改，也容易出现 YAML ref 和真实 submodule HEAD 不一致。

## 目标

新增统一命令：

```bash
./build.sh sync-sdk-pins sdk-artinchip-luban-lite --commit
```

它只同步当前本地已经检出的 commit，不自动拉取远端、不自动 checkout、不访问网络。

推荐使用方式是：开发者先在 `upstream/luban-lite` 完成修改并提交，然后回到主工程执行这个命令。脚本会按顺序完成：

1. 读取 `upstream/luban-lite` 当前 HEAD。
2. 更新 SDK 适配仓库里的 `sdk.yaml upstream.ref` 和相关说明。
3. 在 SDK 适配仓库提交 upstream gitlink 与 `sdk.yaml`。
4. 读取 SDK 适配仓库新的 HEAD。
5. 更新主工程所有匹配该 SDK 的 `targets/*.yaml sdk.ref`。
6. 在主工程提交 SDK gitlink 与 `targets/*.yaml`。
7. 执行一致性检查并输出同步结果。

## 不做什么

本次不做以下内容：

- 不使用浮动分支替代 commit 锁定。
- 不执行 `git fetch`、`git pull`、`git checkout` 或 `git submodule update --remote`。
- 不推送远端分支。
- 不创建 PR。
- 不修改真实构建流程。
- 不解析或修改工具链 Release。
- 不支持同时同步多个 SDK。

## 命令设计

`build.sh` 新增命令：

```text
sync-sdk-pins  同步 SDK submodule 指针和 targets/*.yaml 中的 sdk.ref
```

脚本入口：

```text
tools/scripts/sync_sdk_pins.sh
```

支持参数：

```bash
./build.sh sync-sdk-pins <sdk-name> --check
./build.sh sync-sdk-pins <sdk-name> --commit
./build.sh sync-sdk-pins <sdk-name> --repo-root <path> --check
```

参数语义：

- `--check`：只检查，不修改文件。发现不一致时返回非零。
- `--commit`：执行同步、提交 SDK 适配仓库、提交主工程。
- `--repo-root`：测试或脚本调用时指定主工程根目录，默认自动定位。

第一版必须显式传 `--check` 或 `--commit`，避免误操作。

## 一致性规则

对 `sdk-artinchip-luban-lite`，脚本检查以下关系：

```text
third_party/sdk/sdk-artinchip-luban-lite/upstream/luban-lite HEAD
  == third_party/sdk/sdk-artinchip-luban-lite/sdk.yaml upstream.ref

third_party/sdk/sdk-artinchip-luban-lite HEAD
  == targets/*.yaml 中 sdk.name=sdk-artinchip-luban-lite 的 sdk.ref
  == 主工程记录的 third_party/sdk/sdk-artinchip-luban-lite gitlink
```

如果某个 target 的 `sdk.name` 不是传入的 SDK 名称，脚本不能修改它。

## 安全策略

`--commit` 执行前需要检查：

- 主工程是 Git 仓库。
- `third_party/sdk/<sdk-name>` 是 Git 仓库。
- SDK 仓库里的 `upstream/luban-lite` 是 Git 仓库。
- `upstream/luban-lite` 工作区干净，防止把未提交源码误认为可锁定版本。
- SDK 适配仓库除了允许的 upstream gitlink 和 `sdk.yaml` 外没有其他未提交变更。
- 主工程除了允许的 SDK gitlink 和 `targets/*.yaml` 外没有其他未提交变更。

如果存在不相关脏文件，脚本直接失败并输出具体路径。脚本不能自动 stash、reset 或丢弃用户修改。

提交信息使用中文：

```text
chore: 同步 Luban-Lite upstream 指针
chore: 同步 Luban-Lite SDK 指针
```

如果某一层没有变化，不创建空提交。

## YAML 更新策略

不引入外部 YAML 依赖。可以使用一个小的 Python 标准库脚本完成保格式更新：

- 在 `targets/*.yaml` 中定位 `sdk:` 块。
- 只更新 `sdk.name` 等于传入 SDK 名称的 `ref:` 行。
- 在 `sdk.yaml` 中定位 `upstream:` 块，只更新其 `ref:` 行。
- 如果 `sdk.yaml notes` 中存在 `upstream/luban-lite 固定到提交 ...`，同步替换其中的 commit。
- 保留现有缩进、字段顺序和注释。

如果目标 YAML 缺少应更新的字段，脚本失败并提示具体文件。

## 输出设计

成功时输出关键指针：

```text
SDK：sdk-artinchip-luban-lite
upstream/luban-lite HEAD：<commit>
SDK adapter HEAD：<commit>
已更新 target 数量：<n>
检查结果：指针一致
```

失败时输出中文错误，例如：

```text
SDK 仓库存在不相关未提交变更：scripts/build_firmware.sh
targets/artinchip_d12x_lubanlite_demo68_nor.yaml 的 sdk.ref 与 SDK HEAD 不一致
sdk.yaml upstream.ref 与 upstream/luban-lite HEAD 不一致
```

## 测试设计

新增主工程测试：

```text
tests/host_unit/test_sync_sdk_pins.py
```

覆盖：

- `./build.sh help` 展示 `sync-sdk-pins`。
- `--check` 在全部一致时通过。
- `--check` 在 `targets/*.yaml sdk.ref` 过期时失败。
- `--check` 在 `sdk.yaml upstream.ref` 过期时失败。
- `--commit` 会先提交 SDK 适配仓库，再提交主工程。
- `--commit` 会更新所有匹配 `sdk.name=sdk-artinchip-luban-lite` 的 target。
- `--commit` 不修改其他 SDK 的 target。
- upstream 工作区有未提交变更时失败。
- SDK 适配仓库存在不相关脏文件时失败。
- 主工程存在不相关脏文件时失败。

测试使用临时 Git 仓库和本地 submodule，不访问网络。必要时用：

```bash
git -c protocol.file.allow=always submodule add ...
```

## 验证命令

实现完成后至少运行：

```bash
python3 -m pytest tests/host_unit/test_sync_sdk_pins.py -q
python3 -m pytest tests/host_unit tests/api_contract -q
./build.sh validate-targets
./build.sh sync-sdk-pins sdk-artinchip-luban-lite --check
```

如果 DeepSeek 在 PR 中修改了 SDK 适配仓库，还需要在 SDK 仓库运行已有 shell 测试：

```bash
cd third_party/sdk/sdk-artinchip-luban-lite
tests/test_sdk_contract.sh
tests/test_d12x_target_configs.sh
```

## DeepSeek 实施要求

DeepSeek 创建独立分支实现，不直接改 `main`。PR 描述和 commit 信息使用中文。实现时重点注意：

- 不要自动联网。
- 不要使用浮动分支。
- 不要重置用户改动。
- `--commit` 的提交顺序必须是先 SDK 适配仓库，后主工程。
- 脚本失败时必须返回非零。
- 所有新增输出使用中文。
