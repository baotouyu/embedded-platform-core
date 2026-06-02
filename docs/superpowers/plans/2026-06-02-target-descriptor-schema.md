# Target 描述规范 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 target 描述从早期平铺字段迁移到 `platform:` 分组，并让 SDK 准备、EP 导出和固件构建脚本继续按 target 文件稳定调度。

**Architecture:** 新增一个小型 POSIX shell 辅助脚本 `tools/scripts/target_descriptor.sh`，集中读取 target 固定字段，三个构建脚本通过 source 复用它。第一版仍只支持固定字段，不引入通用 YAML 解析器；真实 SDK 编译和烧录继续留到 SDK 仓库后续处理。

**Tech Stack:** POSIX shell、pytest、YAML 风格 target 描述、现有 `build.sh` 调度入口。

---

## 文件结构

- 新增 `tools/scripts/target_descriptor.sh`：集中提供 `td_read_top_level_value`、`td_read_section_value`、`td_require_value`、`td_validate_declared_target` 等固定字段读取和校验函数。
- 修改 `targets/host_rtos_demo.yaml`：迁移到 `platform:` 分组，并增加 `toolchain.source: sdk`。
- 新增 `targets/artinchip_d121_lubanlite_demo.yaml`：匠芯创 D121 Luban-Lite 占位 target，暂时仍走 SDK stub。
- 修改 `tools/scripts/prepare_target_sdk.sh`：复用 `target_descriptor.sh` 读取 `sdk.*` 字段。
- 修改 `tools/scripts/export_target.sh`：复用 `target_descriptor.sh` 读取 `output.ep_package`。
- 修改 `tools/scripts/build_target_firmware.sh`：复用 `target_descriptor.sh` 读取 `sdk.name`、`output.*`。
- 新增 `tests/host_unit/test_target_descriptor_schema.py`：覆盖新 schema、必填字段和占位 target。
- 修改 `tests/host_unit/test_target_sdk_prepare.py`、`tests/host_unit/test_target_descriptor_export.py`、`tests/host_unit/test_target_firmware_build.py`：把测试夹具里的 target 文件改成 `platform:` 分组。
- 修改 `docs/porting/rtos-sdk-library-model.md`：同步 target 示例到新 schema。
- 修改 `docs/architecture/repository-layout.md` 或 `docs/porting/platform-differences.md`：补一句 `targets/` 现在使用 `platform:` 分组描述平台差异。

## Task 1: 增加 target schema 测试

**Files:**
- Create: `tests/host_unit/test_target_descriptor_schema.py`
- Modify: `targets/host_rtos_demo.yaml`

- [ ] **Step 1: Write failing schema tests**

Create `tests/host_unit/test_target_descriptor_schema.py`:

```python
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGETS_DIR = REPO_ROOT / "targets"
HOST_RTOS_TARGET = TARGETS_DIR / "host_rtos_demo.yaml"
ARTINCHIP_D121_TARGET = TARGETS_DIR / "artinchip_d121_lubanlite_demo.yaml"


def _read_section_value(text: str, section: str, key: str) -> str:
    in_section = False
    for line in text.splitlines():
        if line == f"{section}:":
            in_section = True
            continue
        if line and not line.startswith(" ") and line.endswith(":"):
            in_section = False
        if in_section:
            prefix = f"  {key}:"
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
    return ""


def test_host_rtos_demo_uses_platform_grouped_schema():
    text = HOST_RTOS_TARGET.read_text(encoding="utf-8")

    assert "target: host_rtos_demo" in text
    assert "platform:" in text
    assert _read_section_value(text, "platform", "family") == "rtos"
    assert _read_section_value(text, "platform", "vendor") == "host"
    assert _read_section_value(text, "platform", "sdk_family") == "demo"
    assert _read_section_value(text, "platform", "chip") == "host"
    assert _read_section_value(text, "platform", "board") == "rtos-demo"
    assert _read_section_value(text, "platform", "kernel") == "none"
    assert "os: rtos" not in text
    assert "\nvendor: host" not in text
    assert "\nsdk_family: demo" not in text


def test_target_file_names_match_declared_target_names():
    for target_file in sorted(TARGETS_DIR.glob("*.yaml")):
        text = target_file.read_text(encoding="utf-8")
        declared = ""
        for line in text.splitlines():
            if line.startswith("target:"):
                declared = line.split(":", 1)[1].strip()
                break

        assert declared, f"{target_file} 缺少 target 字段"
        assert target_file.stem == declared


def test_target_files_declare_required_schema_fields():
    for target_file in sorted(TARGETS_DIR.glob("*.yaml")):
        text = target_file.read_text(encoding="utf-8")

        assert _read_section_value(text, "platform", "family"), target_file
        assert _read_section_value(text, "platform", "vendor"), target_file
        assert _read_section_value(text, "platform", "sdk_family"), target_file
        assert _read_section_value(text, "platform", "chip"), target_file
        assert _read_section_value(text, "platform", "board"), target_file
        assert _read_section_value(text, "platform", "kernel"), target_file
        assert _read_section_value(text, "toolchain", "source"), target_file
        assert _read_section_value(text, "output", "ep_package"), target_file


def test_artinchip_d121_lubanlite_placeholder_target_exists():
    text = ARTINCHIP_D121_TARGET.read_text(encoding="utf-8")

    assert "target: artinchip_d121_lubanlite_demo" in text
    assert _read_section_value(text, "platform", "family") == "rtos"
    assert _read_section_value(text, "platform", "vendor") == "artinchip"
    assert _read_section_value(text, "platform", "sdk_family") == "luban-lite"
    assert _read_section_value(text, "platform", "chip") == "d121"
    assert _read_section_value(text, "platform", "kernel") == "rt-thread"
    assert _read_section_value(text, "sdk", "name") == "sdk-artinchip-luban-lite"
    assert _read_section_value(text, "output", "firmware") == (
        "out/firmware/artinchip_d121_lubanlite_demo"
    )
```

- [ ] **Step 2: Run schema tests and verify they fail**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_schema.py -v
```

Expected: FAIL because `host_rtos_demo.yaml` still uses flat fields and `artinchip_d121_lubanlite_demo.yaml` does not exist.

## Task 2: 迁移 target 文件到新 schema

**Files:**
- Modify: `targets/host_rtos_demo.yaml`
- Create: `targets/artinchip_d121_lubanlite_demo.yaml`

- [ ] **Step 1: Update `targets/host_rtos_demo.yaml`**

Replace the file with:

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
  name: sdk-artinchip-luban-lite
  repo: https://github.com/baotouyu/sdk-artinchip-luban-lite.git
  ref: main

toolchain:
  source: sdk

output:
  ep_package: out/ep/host_rtos_demo
  firmware: out/firmware/host_rtos_demo
```

- [ ] **Step 2: Add `targets/artinchip_d121_lubanlite_demo.yaml`**

Create:

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

- [ ] **Step 3: Run schema tests and verify remaining failures are script-related only**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_schema.py -v
```

Expected: PASS for schema tests after target files are updated.

- [ ] **Step 4: Commit target schema files**

Run:

```bash
git add targets/host_rtos_demo.yaml targets/artinchip_d121_lubanlite_demo.yaml tests/host_unit/test_target_descriptor_schema.py
git commit -m "feat: 迁移target描述规范"
```

## Task 3: 增加共享 target 描述读取脚本

**Files:**
- Create: `tools/scripts/target_descriptor.sh`
- Create: `tests/host_unit/test_target_descriptor_helpers.py`

- [ ] **Step 1: Write failing helper tests**

Create `tests/host_unit/test_target_descriptor_helpers.py`:

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "tools" / "scripts" / "target_descriptor.sh"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_target_descriptor_helper_reads_top_level_and_section_values(tmp_path):
    target_file = tmp_path / "target.yaml"
    _write_file(
        target_file,
        """target: host_rtos_demo

platform:
  family: rtos
  vendor: host

output:
  ep_package: out/ep/host_rtos_demo
""",
    )

    script = f""". '{HELPER}'
printf 'target=%s\\n' "$(td_read_top_level_value '{target_file}' target)"
printf 'family=%s\\n' "$(td_read_section_value '{target_file}' platform family)"
printf 'ep=%s\\n' "$(td_read_section_value '{target_file}' output ep_package)"
"""

    result = subprocess.run(
        ["sh", "-c", script],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "target=host_rtos_demo" in result.stdout
    assert "family=rtos" in result.stdout
    assert "ep=out/ep/host_rtos_demo" in result.stdout


def test_target_descriptor_helper_requires_values_with_chinese_error(tmp_path):
    target_file = tmp_path / "target.yaml"
    _write_file(target_file, "target: host_rtos_demo\n")

    script = f""". '{HELPER}'
td_require_value "$(td_read_section_value '{target_file}' sdk name)" "target 描述缺少 sdk.name：{target_file}"
"""

    result = subprocess.run(
        ["sh", "-c", script],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert f"target 描述缺少 sdk.name：{target_file}" in result.stderr
```

- [ ] **Step 2: Run helper tests and verify they fail**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_helpers.py -v
```

Expected: FAIL because `tools/scripts/target_descriptor.sh` does not exist.

- [ ] **Step 3: Add `tools/scripts/target_descriptor.sh`**

Create:

```sh
#!/bin/sh

td_die() {
    printf '%s\n' "$1" >&2
    exit 1
}

td_trim() {
    printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

td_read_top_level_value() {
    file=$1
    key=$2
    sed -n "s/^${key}:[[:space:]]*//p" "$file" | head -n 1
}

td_read_section_value() {
    file=$1
    section=$2
    key=$3
    awk -v section="$section" -v key="$key" '
        $0 ~ "^" section ":" { in_section = 1; next }
        /^[^[:space:]].*:/ { in_section = 0 }
        in_section && $0 ~ "^[[:space:]]+" key ":" {
            sub("^[[:space:]]+" key ":[[:space:]]*", "")
            print
            exit
        }
    ' "$file"
}

td_require_value() {
    value=$1
    message=$2
    [ -n "$(td_trim "$value")" ] || td_die "$message"
}

td_validate_declared_target() {
    target_file=$1
    target=$2
    declared_target=$(td_trim "$(td_read_top_level_value "$target_file" "target")")
    [ "$declared_target" = "$target" ] || td_die "target 描述不匹配：文件内 target 为 ${declared_target}，命令参数为 ${target}"
}
```

- [ ] **Step 4: Run helper tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_helpers.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit helper script**

Run:

```bash
git add tools/scripts/target_descriptor.sh tests/host_unit/test_target_descriptor_helpers.py
git commit -m "feat: 增加target描述读取脚本"
```

## Task 4: 更新脚本读取新 schema

**Files:**
- Modify: `tools/scripts/prepare_target_sdk.sh`
- Modify: `tools/scripts/export_target.sh`
- Modify: `tools/scripts/build_target_firmware.sh`
- Modify: `tests/host_unit/test_target_sdk_prepare.py`
- Modify: `tests/host_unit/test_target_descriptor_export.py`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Update test fixtures to grouped schema**

In each test helper that writes `targets/host_rtos_demo.yaml`, replace flat fields with:

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
  repo: <fake repo path>
  ref: HEAD

toolchain:
  source: sdk

output:
  ep_package: out/ep/host_rtos_demo
  firmware: out/firmware/host_rtos_demo
```

For tests that do not need SDK fields, keep the same `platform:` and `toolchain:` sections, and include only the output fields required by that script.

- [ ] **Step 2: Run existing target tests and verify script failures**

Run:

```bash
pytest tests/host_unit/test_target_sdk_prepare.py tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_target_firmware_build.py -v
```

Expected: FAIL in script-related tests if any script still reads old fixture assumptions incorrectly.

- [ ] **Step 3: Update `prepare_target_sdk.sh` to source helper**

Near the top after `SCRIPT_DIR`, add:

```sh
. "$SCRIPT_DIR/target_descriptor.sh"
```

Remove local `trim()`, `read_top_level_value()` and `read_section_value()` functions.

Replace target validation and reads with:

```sh
td_validate_declared_target "$TARGET_FILE" "$TARGET"

sdk_repo=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "repo")")
sdk_ref=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "ref")")
sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")

td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"
td_require_value "$sdk_repo" "target 描述缺少 sdk.repo：$TARGET_FILE"
td_require_value "$sdk_ref" "target 描述缺少 sdk.ref：$TARGET_FILE"
```

- [ ] **Step 4: Update `export_target.sh` to source helper**

Near the top after `SCRIPT_DIR`, add:

```sh
. "$SCRIPT_DIR/target_descriptor.sh"
```

Remove local `trim()`, `read_top_level_value()` and `read_output_ep_package()` functions.

Replace target validation and output read with:

```sh
td_validate_declared_target "$TARGET_FILE" "$TARGET"

ep_package=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "ep_package")")
td_require_value "$ep_package" "target 描述缺少 output.ep_package：$TARGET_FILE"
```

- [ ] **Step 5: Update `build_target_firmware.sh` to source helper**

Near the top after `SCRIPT_DIR`, add:

```sh
. "$SCRIPT_DIR/target_descriptor.sh"
```

Remove local `trim()`, `read_top_level_value()` and `read_section_value()` functions.

Replace target validation and reads with:

```sh
td_validate_declared_target "$TARGET_FILE" "$TARGET"

sdk_name=$(td_trim "$(td_read_section_value "$TARGET_FILE" "sdk" "name")")
ep_package=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "ep_package")")
firmware_output=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "firmware")")

td_require_value "$sdk_name" "target 描述缺少 sdk.name：$TARGET_FILE"
td_require_value "$ep_package" "target 描述缺少 output.ep_package：$TARGET_FILE"
td_require_value "$firmware_output" "target 描述缺少 output.firmware：$TARGET_FILE"
```

- [ ] **Step 6: Run target tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_helpers.py tests/host_unit/test_target_descriptor_schema.py tests/host_unit/test_target_sdk_prepare.py tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_target_firmware_build.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit script migration**

Run:

```bash
git add tools/scripts/prepare_target_sdk.sh tools/scripts/export_target.sh tools/scripts/build_target_firmware.sh tests/host_unit/test_target_sdk_prepare.py tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_target_firmware_build.py
git commit -m "feat: 使用新target描述规范"
```

## Task 5: 更新文档并验证本地 SDK stub 链路

**Files:**
- Modify: `docs/porting/rtos-sdk-library-model.md`
- Modify: `docs/porting/platform-differences.md`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Update RTOS SDK model target example**

In `docs/porting/rtos-sdk-library-model.md`, replace the flat target example with:

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
  ref: main

toolchain:
  source: sdk

sdk_config:
  defconfig: d12x_demo68-nor_rt-thread_ep_app_defconfig

output:
  ep_package: out/ep/artinchip_d12x_lubanlite_demo68_nor
  firmware: out/firmware/artinchip_d12x_lubanlite_demo68_nor
```

- [ ] **Step 2: Update platform differences doc**

In `docs/porting/platform-differences.md`, add this sentence in the vendor SDK section:

```markdown
target 描述文件使用 `platform:` 分组记录 `family`、`vendor`、`sdk_family`、`chip`、`board` 和 `kernel`，构建脚本只读取稳定字段，不把芯片判断写散。
```

- [ ] **Step 3: Update doc assertions**

In `tests/host_unit/test_target_firmware_build.py`, update `test_rtos_sdk_document_describes_build_firmware_entry()` to include:

```python
assert "platform:" in text
assert "toolchain:" in text
assert "sdk_config:" in text
assert "artinchip_d12x_lubanlite_demo68_nor" in text
```

- [ ] **Step 4: Run docs and target tests**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_schema.py tests/host_unit/test_target_sdk_prepare.py tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_target_firmware_build.py tests/host_unit/test_repository_layout.py -v
```

Expected: PASS.

- [ ] **Step 5: Run real local SDK stub integration for both targets**

Run:

```bash
EP_SDK_ROOT=/Users/yuwei/Documents/KitchenIdea/项目/C08 ./build.sh build-firmware host_rtos_demo --clean
EP_SDK_ROOT=/Users/yuwei/Documents/KitchenIdea/项目/C08 ./build.sh build-firmware artinchip_d121_lubanlite_demo --clean
```

Expected:

- Both commands exit `0`.
- Output includes `SDK 准备完成`.
- `out/firmware/host_rtos_demo/build_manifest.txt` exists.
- `out/firmware/artinchip_d121_lubanlite_demo/build_manifest.txt` exists.

- [ ] **Step 6: Run full verification**

Run:

```bash
./build.sh test
git diff --check
```

Expected:

- `./build.sh test` exits `0`.
- `git diff --check` exits `0`.

- [ ] **Step 7: Commit documentation and final verification updates**

Run:

```bash
git add docs/porting/rtos-sdk-library-model.md docs/porting/platform-differences.md tests/host_unit/test_target_firmware_build.py
git commit -m "docs: 同步target描述规范"
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
gh pr create --base main --head <branch> --title "feat: 规范target描述文件" --body "<中文PR内容>"
```

PR 内容必须包含：

- `host_rtos_demo` 已迁移到 `platform:` 分组。
- 新增 `artinchip_d121_lubanlite_demo` 占位 target。
- 构建脚本复用 `target_descriptor.sh` 读取固定字段。
- 验证命令和结果。
