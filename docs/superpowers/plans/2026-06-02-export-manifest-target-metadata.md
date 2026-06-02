# 导出包 Manifest Target 元数据 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 `./build.sh export-target <target>` 生成的 `out/ep/<target>/manifest.json` 包含 target 的 `platform`、`sdk` 和 `toolchain` 元数据。

**Architecture:** `export_target.sh` 继续负责 target 驱动导出，并把 `targets/<target>.yaml` 通过 `--target-file` 传给 `export_ep_package.sh`。`export_ep_package.sh` 保持直接导出兼容；只有传入 `--target-file` 时才读取 target 元数据并写入 manifest。

**Tech Stack:** POSIX shell、现有 `target_descriptor.sh`、pytest、JSON manifest。

---

## 文件结构

- 修改 `tools/scripts/export_ep_package.sh`：新增 `--target-file <路径>` 参数，读取 target 元数据并写入 manifest。
- 修改 `tools/scripts/export_target.sh`：调用 `export_ep_package.sh` 时传入 `--target-file "$TARGET_FILE"`。
- 修改 `tests/host_unit/test_target_descriptor_export.py`：验证 target 驱动导出的 manifest 包含 `platform`、`sdk`、`toolchain`。
- 修改 `tests/host_unit/test_ep_static_library_export.py`：验证直接 `export_ep_package.sh` 导出仍保持兼容。
- 修改 `docs/porting/rtos-sdk-library-model.md`：记录导出包 manifest 包含 target 元数据。

## Task 1: 为 export-target manifest 增加失败测试

**Files:**
- Modify: `tests/host_unit/test_target_descriptor_export.py`

- [ ] **Step 1: Update fake target fixture with platform/sdk/toolchain**

In `_prepare_minimal_repo()`, ensure the target file contains:

```yaml
target: host_rtos_demo

platform:
  family: rtos
  vendor: host
  sdk_family: demo
  chip: host
  board: rtos-demo
  kernel: none

sdk:
  name: fake-sdk
  repo: https://example.com/fake-sdk.git
  ref: main

toolchain:
  source: sdk

output:
  ep_package: out/ep/host_rtos_demo
```

- [ ] **Step 2: Add manifest metadata assertions**

In `test_export_target_script_reads_descriptor_and_creates_package()`, after existing manifest assertions, add:

```python
assert manifest["platform"] == {
    "family": "rtos",
    "vendor": "host",
    "sdk_family": "demo",
    "chip": "host",
    "board": "rtos-demo",
    "kernel": "none",
}
assert manifest["sdk"] == {
    "name": "fake-sdk",
    "repo": "https://example.com/fake-sdk.git",
    "ref": "main",
}
assert manifest["toolchain"] == {"source": "sdk"}
```

- [ ] **Step 3: Run test and verify it fails**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py::test_export_target_script_reads_descriptor_and_creates_package -v
```

Expected: FAIL with missing `platform`, `sdk` or `toolchain` in manifest.

## Task 2: 让 export-target 传递 target 文件

**Files:**
- Modify: `tools/scripts/export_target.sh`
- Modify: `tools/scripts/export_ep_package.sh`

- [ ] **Step 1: Add `--target-file` argument parsing to `export_ep_package.sh`**

Add variable near the top:

```sh
TARGET_FILE=
```

Add help line:

```text
  --target-file <路径> target 描述文件，存在时写入 platform/sdk/toolchain 元数据
```

Add argument parser branch:

```sh
        --target-file)
            [ "$#" -ge 2 ] || die "缺少 --target-file 参数值"
            TARGET_FILE=$2
            shift 2
            ;;
```

After resolving `REPO_ROOT`, resolve `TARGET_FILE` when non-empty:

```sh
if [ -n "$TARGET_FILE" ]; then
    TARGET_FILE=$(resolve_path "$TARGET_FILE" "$REPO_ROOT")
    [ -f "$TARGET_FILE" ] || die "缺少 target 描述文件：$TARGET_FILE"
fi
```

- [ ] **Step 2: Source target descriptor helper in `export_ep_package.sh`**

After `SCRIPT_DIR=...`, add:

```sh
. "$SCRIPT_DIR/target_descriptor.sh"
```

- [ ] **Step 3: Pass target file from `export_target.sh`**

In both branches that call `export_ep_package.sh`, add:

```sh
--target-file "$TARGET_FILE"
```

The clean branch should become:

```sh
"$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent" --target-file "$TARGET_FILE" --clean
```

The non-clean branch should become:

```sh
"$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent" --target-file "$TARGET_FILE"
```

- [ ] **Step 4: Run test and confirm it still fails on missing manifest fields**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py::test_export_target_script_reads_descriptor_and_creates_package -v
```

Expected: still FAIL because `export_ep_package.sh` accepts the target file but does not write metadata yet.

## Task 3: 写入 manifest target 元数据

**Files:**
- Modify: `tools/scripts/export_ep_package.sh`

- [ ] **Step 1: Add helper to read target metadata**

Add before manifest generation:

```sh
target_platform_family=
target_platform_vendor=
target_platform_sdk_family=
target_platform_chip=
target_platform_board=
target_platform_kernel=
target_sdk_name=
target_sdk_repo=
target_sdk_ref=
target_toolchain_source=

if [ -n "$TARGET_FILE" ]; then
    td_validate_declared_target "$TARGET_FILE" "$TARGET"
    target_platform_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "family")")
    target_platform_vendor=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "vendor")")
    target_platform_sdk_family=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "sdk_family")")
    target_platform_chip=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "chip")")
    target_platform_board=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "board")")
    target_platform_kernel=$(td_trim "$(td_read_section_value "$TARGET_FILE" "platform" "kernel")")
    target_sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
    target_sdk_repo=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "repo")")
    target_sdk_ref=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "ref")")
    target_toolchain_source=$(td_trim "$(td_read_section_value "$TARGET_FILE" "toolchain" "source")")
fi
```

- [ ] **Step 2: Add manifest JSON blocks when `TARGET_FILE` is set**

In the manifest writer, after `library`, add:

```sh
    if [ -n "$TARGET_FILE" ]; then
        printf '  "platform": {\n'
        printf '    "family": "%s",\n' "$(json_escape "$target_platform_family")"
        printf '    "vendor": "%s",\n' "$(json_escape "$target_platform_vendor")"
        printf '    "sdk_family": "%s",\n' "$(json_escape "$target_platform_sdk_family")"
        printf '    "chip": "%s",\n' "$(json_escape "$target_platform_chip")"
        printf '    "board": "%s",\n' "$(json_escape "$target_platform_board")"
        printf '    "kernel": "%s"\n' "$(json_escape "$target_platform_kernel")"
        printf '  },\n'
        printf '  "sdk": {\n'
        printf '    "name": "%s",\n' "$(json_escape "$target_sdk_name")"
        printf '    "repo": "%s",\n' "$(json_escape "$target_sdk_repo")"
        printf '    "ref": "%s"\n' "$(json_escape "$target_sdk_ref")"
        printf '  },\n'
        printf '  "toolchain": {\n'
        printf '    "source": "%s"\n' "$(json_escape "$target_toolchain_source")"
        printf '  },\n'
    fi
```

Keep the existing `headers` block after these new fields so JSON remains valid.

- [ ] **Step 3: Run target export test and verify it passes**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py::test_export_target_script_reads_descriptor_and_creates_package -v
```

Expected: PASS.

- [ ] **Step 4: Run direct export compatibility test**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py::test_export_script_creates_standard_package_from_existing_archive -v
```

Expected: PASS. Direct export does not need to assert `platform`.

- [ ] **Step 5: Commit manifest metadata implementation**

Run:

```bash
git add tools/scripts/export_ep_package.sh tools/scripts/export_target.sh tests/host_unit/test_target_descriptor_export.py
git commit -m "feat: 导出manifest写入target元数据"
```

## Task 4: 补充兼容和文档测试

**Files:**
- Modify: `tests/host_unit/test_ep_static_library_export.py`
- Modify: `docs/porting/rtos-sdk-library-model.md`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Add direct export compatibility assertion**

In `test_export_script_creates_standard_package_from_existing_archive()`, after existing manifest assertions, add:

```python
assert "platform" not in manifest
assert "sdk" not in manifest
assert "toolchain" not in manifest
```

- [ ] **Step 2: Update RTOS SDK model document**

In `docs/porting/rtos-sdk-library-model.md`, add under the export package section:

```markdown
通过 `export-target` 导出的 `manifest.json` 会包含 target 元数据，包括 `platform`、`sdk` 和 `toolchain`。SDK 仓库可以用这些字段确认静态库包是否匹配当前芯片和板级构建。
```

- [ ] **Step 3: Update doc assertion**

In `test_rtos_sdk_document_describes_build_firmware_entry()`, add:

```python
assert "manifest.json" in text
assert "platform" in text
assert "toolchain" in text
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_ep_static_library_export.py tests/host_unit/test_target_firmware_build.py -v
```

Expected: PASS.

- [ ] **Step 5: Run manual export-target command**

Run:

```bash
./build.sh configure
cmake --build build --target ep_app_core_export
./build.sh export-target artinchip_d121_lubanlite_demo --clean
python3 -m json.tool out/ep/artinchip_d121_lubanlite_demo/manifest.json >/dev/null
```

Expected: all commands exit `0`.

- [ ] **Step 6: Run full verification**

Run:

```bash
./build.sh test
git diff --check
```

Expected:

- `./build.sh test` exits `0`.
- `git diff --check` exits `0`.

- [ ] **Step 7: Commit documentation and compatibility tests**

Run:

```bash
git add tests/host_unit/test_ep_static_library_export.py docs/porting/rtos-sdk-library-model.md tests/host_unit/test_target_firmware_build.py
git commit -m "docs: 记录manifest target元数据"
```

## Completion

After all tasks pass:

```bash
git status --short --branch
git log --oneline -5
```

Then push and create a PR:

```bash
git push -u origin <branch>
gh pr create --base main --head <branch> --title "feat: 导出manifest写入target元数据" --body "<中文PR内容>"
```

PR 内容必须包含：

- `export-target` manifest 新增 `platform`、`sdk`、`toolchain`。
- 直接 `export-ep` 兼容旧 manifest。
- 测试和手动命令结果。

