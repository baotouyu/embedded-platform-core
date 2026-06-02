# 导出包 Manifest Target 元数据设计

## 背景

主工程已经可以按 target 导出静态库包：

```bash
./build.sh export-target host_rtos_demo
./build.sh export-target artinchip_d121_lubanlite_demo
```

当前 `out/ep/<target>/manifest.json` 只记录包名、target、库文件、头文件列表等基础信息。随着 RTOS SDK 仓库开始消费这些导出包，manifest 需要能回答几个问题：

- 这个静态库包是给哪个平台、芯片、板子导出的？
- 它应该由哪个 SDK 仓库消费？
- 它使用 target 文件里声明的哪套工具链来源？

这些信息都已经在 `targets/<target>.yaml` 里存在，应该同步写入导出包 manifest，方便 SDK 仓库、CI、人工排查和后续发布归档读取。

## 目标

增强 `out/ep/<target>/manifest.json`，在现有字段基础上增加 target 元数据：

```json
{
  "target": "artinchip_d121_lubanlite_demo",
  "platform": {
    "family": "rtos",
    "vendor": "artinchip",
    "sdk_family": "luban-lite",
    "chip": "d121",
    "board": "demo",
    "kernel": "rt-thread"
  },
  "sdk": {
    "name": "sdk-artinchip-luban-lite",
    "repo": "https://github.com/baotouyu/sdk-artinchip-luban-lite.git",
    "ref": "main"
  },
  "toolchain": {
    "source": "sdk"
  }
}
```

现有字段 `package`、`format`、`library`、`headers` 保持不变。

## 不做什么

本次不做以下内容：

- 不生成最终固件 manifest。
- 不记录真实编译器版本。
- 不记录 git commit。
- 不拉取或查询 SDK 仓库。
- 不校验 SDK repo/ref 是否存在。
- 不改 `sdk-artinchip-luban-lite` 仓库。
- 不引入 JSON 或 YAML 解析依赖。

真实编译器、EP commit、SDK commit 这些属于后续“可追溯构建清单”范围，等 SDK 真实构建接入后再做。

## 数据来源

当用户通过：

```bash
./build.sh export-target <target>
```

导出时，数据来源是：

```text
targets/<target>.yaml
```

`export_target.sh` 已经负责读取 target 描述并调用 `export_ep_package.sh`。本次建议由 `export_target.sh` 把 target 文件路径传给 `export_ep_package.sh`：

```bash
export_ep_package.sh --target <target> --target-file targets/<target>.yaml
```

`export_ep_package.sh` 继续支持不传 `--target-file` 的旧用法，例如：

```bash
./build.sh export-ep --target host_rtos_demo
```

这种直接导出模式只写现有基础字段，不强制写 `platform`、`sdk`、`toolchain`。这样可以保持兼容。

## Manifest 字段规则

`--target-file` 存在时，manifest 增加：

```json
"platform": {
  "family": "...",
  "vendor": "...",
  "sdk_family": "...",
  "chip": "...",
  "board": "...",
  "kernel": "..."
}
```

`toolchain.source` 存在时，manifest 增加：

```json
"toolchain": {
  "source": "..."
}
```

`sdk.name`、`sdk.repo`、`sdk.ref` 存在时，manifest 增加：

```json
"sdk": {
  "name": "...",
  "repo": "...",
  "ref": "..."
}
```

第一版只支持这些固定字段。字段缺失时，`export-target` 应该在导出前通过已有 target 校验能力失败，不让不完整 manifest 被生成。

## 脚本边界

`export_target.sh` 职责：

- 校验 target 文件存在。
- 校验 target 名一致。
- 读取 `output.ep_package`。
- 调用 `export_ep_package.sh` 时传入 `--target-file "$TARGET_FILE"`。

`export_ep_package.sh` 职责：

- 继续复制静态库和头文件。
- 继续生成原有 manifest 字段。
- 如果收到 `--target-file`，读取 target 元数据并追加到 manifest。

这样 `export_ep_package.sh` 仍然可以作为低层导出脚本使用，`export_target.sh` 则负责 target 驱动导出。

## 测试设计

需要补充测试：

- `export_target` 生成的 manifest 包含 `platform`、`sdk`、`toolchain`。
- `export_ep_package.sh` 直接导出时仍然兼容旧行为。
- manifest 中的 target 元数据来自 `targets/<target>.yaml`。
- JSON 仍然能被 Python `json.loads()` 正常解析。
- 文档记录 manifest 包含 target 元数据。

优先修改现有测试：

```text
tests/host_unit/test_target_descriptor_export.py
tests/host_unit/test_ep_static_library_export.py
```

不需要新增真实 SDK 依赖。

## 后续方向

这个 manifest 元数据稳定后，后续可以继续做：

- 把 EP git commit 写入 manifest。
- 把 SDK commit 写入固件 build manifest。
- 让 SDK 仓库读取 `manifest.json` 校验 target 是否匹配。
- 在发布包里保存 `target.yaml` 快照。

