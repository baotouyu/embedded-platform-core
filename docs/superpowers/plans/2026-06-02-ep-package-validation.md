# EP 导出包校验 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `validate-ep-package` 校验入口，并让 `build-firmware` 在进入 SDK 构建前确认 EP 导出包和当前 target 描述一致。

**Architecture:** 新增 `tools/scripts/validate_ep_package.sh`，复用 `target_descriptor.sh` 读取 `targets/<target>.yaml`，用轻量 shell 逻辑读取当前 manifest 的固定字符串字段。`build.sh` 提供手动入口，`build_target_firmware.sh` 在 `export_target.sh` 后、SDK `scripts/build_firmware.sh` 前自动调用校验脚本。

**Tech Stack:** POSIX shell、pytest、现有 target descriptor helper、JSON manifest 固定字段读取。

---

## 文件结构

- 创建 `tools/scripts/validate_ep_package.sh`：EP 导出包校验脚本，只负责读取 target 描述和 manifest 固定字段并比较。
- 修改 `build.sh`：新增 `validate-ep-package` 命令、help 文案和调度函数。
- 修改 `tools/scripts/build_target_firmware.sh`：在 SDK 构建前调用 `validate_ep_package.sh`。
- 创建 `tests/host_unit/test_ep_package_validation.py`：覆盖手动校验入口、成功路径和失败路径。
- 修改 `tests/host_unit/test_target_firmware_build.py`：覆盖 `build-firmware` 会先执行导出包校验，并同步 fixture 脚本列表。
- 修改 `docs/porting/rtos-sdk-library-model.md`：记录手动校验命令和 `build-firmware` 自动校验行为。

## Task 1: 写 EP 导出包校验入口失败测试

**Files:**
- Create: `tests/host_unit/test_ep_package_validation.py`

- [ ] **Step 1: Create test file with fixtures**

Create `tests/host_unit/test_ep_package_validation.py`:

```python
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
VALIDATE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "validate_ep_package.sh"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_target(root: Path, target: str = "host_rtos_demo") -> None:
    _write_file(
        root / "targets" / f"{target}.yaml",
        f"""target: {target}

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
  ep_package: out/ep/{target}
  firmware: out/firmware/{target}
""",
    )


def _write_manifest(
    root: Path,
    target: str = "host_rtos_demo",
    *,
    manifest_target: str | None = None,
    chip: str = "host",
    sdk_name: str = "fake-sdk",
) -> Path:
    package_root = root / "out" / "ep" / target
    package_root.mkdir(parents=True, exist_ok=True)
    _write_file(package_root / "lib" / "libep_app_core.a", "fake archive\n")
    manifest = {
        "package": "ep_app_core",
        "target": manifest_target or target,
        "format": "static-library",
        "library": "lib/libep_app_core.a",
        "platform": {
            "family": "rtos",
            "vendor": "host",
            "sdk_family": "demo",
            "chip": chip,
            "board": "rtos-demo",
            "kernel": "none",
        },
        "sdk": {
            "name": sdk_name,
            "repo": "https://example.com/fake-sdk.git",
            "ref": "main",
        },
        "toolchain": {"source": "sdk"},
        "headers": ["include/ep_framework.h"],
    }
    (package_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return package_root
```

- [ ] **Step 2: Add help and script existence tests**

Append to `tests/host_unit/test_ep_package_validation.py`:

```python
def test_build_help_lists_validate_ep_package_command():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "validate-ep-package" in result.stdout
    assert "校验 EP 导出包 manifest" in result.stdout


def test_validate_ep_package_script_exists_and_uses_descriptor_helper():
    assert VALIDATE_SCRIPT.is_file()

    text = VALIDATE_SCRIPT.read_text(encoding="utf-8")
    assert '. "$SCRIPT_DIR/target_descriptor.sh"' in text
    assert "td_validate_declared_target" in text
```

- [ ] **Step 3: Add successful validation test**

Append:

```python
def test_validate_ep_package_passes_when_manifest_matches_target(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    package_root = _write_manifest(repo)

    result = subprocess.run(
        [
            str(VALIDATE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--ep-package",
            str(package_root),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "EP 导出包校验通过" in result.stdout
    assert str(package_root) in result.stdout
```

- [ ] **Step 4: Add missing manifest failure test**

Append:

```python
def test_validate_ep_package_fails_when_manifest_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    package_root = repo / "out" / "ep" / "host_rtos_demo"
    package_root.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            str(VALIDATE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--ep-package",
            str(package_root),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "缺少 EP 导出包 manifest" in result.stderr
    assert "manifest.json" in result.stderr
```

- [ ] **Step 5: Add mismatch failure tests**

Append:

```python
def test_validate_ep_package_fails_when_manifest_target_mismatches(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    package_root = _write_manifest(repo, manifest_target="wrong_target")

    result = subprocess.run(
        [
            str(VALIDATE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--ep-package",
            str(package_root),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "EP 导出包校验失败" in result.stderr
    assert "manifest target 为 wrong_target，target 描述为 host_rtos_demo" in result.stderr


def test_validate_ep_package_fails_when_platform_chip_mismatches(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    package_root = _write_manifest(repo, chip="d122")

    result = subprocess.run(
        [
            str(VALIDATE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--ep-package",
            str(package_root),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "EP 导出包校验失败" in result.stderr
    assert "manifest platform.chip 为 d122，target 描述为 host" in result.stderr


def test_validate_ep_package_fails_when_sdk_name_mismatches(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    package_root = _write_manifest(repo, sdk_name="other-sdk")

    result = subprocess.run(
        [
            str(VALIDATE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--ep-package",
            str(package_root),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "EP 导出包校验失败" in result.stderr
    assert "manifest sdk.name 为 other-sdk，target 描述为 fake-sdk" in result.stderr
```

- [ ] **Step 6: Add default ep_package path test through build.sh**

Append:

```python
def test_build_script_validate_ep_package_uses_target_default_output(tmp_path):
    repo = tmp_path / "repo"
    _write_target(repo)
    _write_manifest(repo)

    result = subprocess.run(
        [
            str(BUILD_SCRIPT),
            "validate-ep-package",
            "host_rtos_demo",
            "--repo-root",
            str(repo),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "EP 导出包校验通过" in result.stdout
```

- [ ] **Step 7: Run tests and verify they fail**

Run:

```bash
pytest tests/host_unit/test_ep_package_validation.py -v
```

Expected: FAIL because `validate_ep_package.sh` and `validate-ep-package` command do not exist yet.

## Task 2: 实现 validate_ep_package.sh 和 build.sh 入口

**Files:**
- Create: `tools/scripts/validate_ep_package.sh`
- Modify: `build.sh`
- Test: `tests/host_unit/test_ep_package_validation.py`

- [ ] **Step 1: Create validate_ep_package.sh skeleton**

Create `tools/scripts/validate_ep_package.sh`:

```sh
#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
EP_PACKAGE=

print_help() {
    cat <<EOF
用法:
  tools/scripts/validate_ep_package.sh --target <名称> [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      target 名称，对应 targets/<target>.yaml
  --ep-package <路径>  EP 导出包目录，默认读取 target 描述的 output.ep_package
  -h, --help           显示帮助
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

resolve_path() {
    path=$1
    base=$2

    case "$path" in
        /*) printf '%s\n' "$path" ;;
        *) printf '%s\n' "$base/$path" ;;
    esac
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repo-root)
            [ "$#" -ge 2 ] || die "缺少 --repo-root 参数值"
            REPO_ROOT=$2
            shift 2
            ;;
        --target)
            [ "$#" -ge 2 ] || die "缺少 --target 参数值"
            TARGET=$2
            shift 2
            ;;
        --ep-package)
            [ "$#" -ge 2 ] || die "缺少 --ep-package 参数值"
            EP_PACKAGE=$2
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            die "未知参数：$1"
            ;;
    esac
done

[ -n "$TARGET" ] || die "缺少 --target 参数"

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
TARGET_FILE=$REPO_ROOT/targets/$TARGET.yaml

[ -f "$TARGET_FILE" ] || die "缺少 target 描述文件：$TARGET_FILE"

td_validate_declared_target "$TARGET_FILE" "$TARGET"

if [ -z "$EP_PACKAGE" ]; then
    EP_PACKAGE=$(td_trim "$(td_read_section_value "$TARGET_FILE" "output" "ep_package")")
    td_require_value "$EP_PACKAGE" "target 描述缺少 output.ep_package：$TARGET_FILE"
fi

EP_PACKAGE=$(resolve_path "$EP_PACKAGE" "$REPO_ROOT")
MANIFEST=$EP_PACKAGE/manifest.json

[ -d "$EP_PACKAGE" ] || die "缺少 EP 导出包目录：$EP_PACKAGE"
[ -f "$MANIFEST" ] || die "缺少 EP 导出包 manifest：$MANIFEST"
```

Run:

```bash
chmod +x tools/scripts/validate_ep_package.sh
```

- [ ] **Step 2: Add fixed-field manifest reader and comparison helpers**

Append before the final success message:

```sh
manifest_read() {
    section=$1
    key=$2

    if [ "$section" = "." ]; then
        awk -v key="$key" '
            $0 ~ "^[[:space:]]*\"" key "\"[[:space:]]*:" {
                sub("^[[:space:]]*\"" key "\"[[:space:]]*:[[:space:]]*\"", "")
                sub("\"[[:space:]]*,?[[:space:]]*$", "")
                print
                exit
            }
        ' "$MANIFEST"
        return
    fi

    awk -v section="$section" -v key="$key" '
        $0 ~ "^[[:space:]]*\"" section "\"[[:space:]]*:" { in_section = 1; next }
        in_section && /^[[:space:]]*}/ { in_section = 0 }
        in_section && $0 ~ "^[[:space:]]*\"" key "\"[[:space:]]*:" {
            sub("^[[:space:]]*\"" key "\"[[:space:]]*:[[:space:]]*\"", "")
            sub("\"[[:space:]]*,?[[:space:]]*$", "")
            print
            exit
        }
    ' "$MANIFEST"
}

target_value() {
    section=$1
    key=$2
    td_trim "$(td_read_section_value "$TARGET_FILE" "$section" "$key")"
}

require_match() {
    label=$1
    manifest_value=$2
    expected_value=$3

    [ -n "$manifest_value" ] || die "EP 导出包校验失败：manifest 缺少 $label：$MANIFEST"
    [ "$manifest_value" = "$expected_value" ] || die "EP 导出包校验失败：manifest $label 为 $manifest_value，target 描述为 $expected_value"
}
```

- [ ] **Step 3: Add required field comparisons**

Append after helpers:

```sh
manifest_target=$(td_trim "$(manifest_read "." "target")")
require_match "target" "$manifest_target" "$TARGET"

for key in family vendor sdk_family chip board kernel; do
    require_match "platform.$key" \
        "$(td_trim "$(manifest_read "platform" "$key")")" \
        "$(target_value "platform" "$key")"
done

for key in name repo ref; do
    require_match "sdk.$key" \
        "$(td_trim "$(manifest_read "sdk" "$key")")" \
        "$(target_value "sdk" "$key")"
done

require_match "toolchain.source" \
    "$(td_trim "$(manifest_read "toolchain" "source")")" \
    "$(target_value "toolchain" "source")"

printf 'EP 导出包校验通过：%s\n' "$EP_PACKAGE"
```

- [ ] **Step 4: Add build.sh command dispatch**

In `build.sh`, update help command list to include:

```text
  validate-ep-package 校验 EP 导出包 manifest 是否匹配 target
```

Update examples to include:

```text
  ./build.sh validate-ep-package host_rtos_demo
```

Add function after `run_validate_targets()`:

```sh
run_validate_ep_package() {
    target=${1:-}
    if [ -z "$target" ]; then
        printf '缺少 target 名称\n' >&2
        exit 2
    fi
    shift
    "$REPO_ROOT/tools/scripts/validate_ep_package.sh" --target "$target" "$@"
}
```

Add case branch before `clean)`:

```sh
    validate-ep-package)
        run_validate_ep_package "$@"
        ;;
```

- [ ] **Step 5: Run validation tests**

Run:

```bash
pytest tests/host_unit/test_ep_package_validation.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit manual validation entry**

Run:

```bash
git add build.sh tools/scripts/validate_ep_package.sh tests/host_unit/test_ep_package_validation.py
git commit -m "feat: 增加EP导出包校验入口"
```

## Task 3: build-firmware 接入导出包校验

**Files:**
- Modify: `tools/scripts/build_target_firmware.sh`
- Modify: `tests/host_unit/test_target_firmware_build.py`
- Test: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Update fixture to copy validation script**

In `tests/host_unit/test_target_firmware_build.py`, update `_prepare_minimal_repo()` script list from:

```python
    for script_name in [
        "target_descriptor.sh",
        "prepare_target_sdk.sh",
        "export_target.sh",
        "export_ep_package.sh",
    ]:
```

to:

```python
    for script_name in [
        "target_descriptor.sh",
        "prepare_target_sdk.sh",
        "export_target.sh",
        "export_ep_package.sh",
        "validate_ep_package.sh",
    ]:
```

- [ ] **Step 2: Add build-firmware validation behavior assertion**

In `test_build_target_firmware_runs_ep_export_and_sdk_build()`, after reading `args_text`, add:

```python
    assert "EP 导出包校验通过" in result.stdout
```

- [ ] **Step 3: Add failure test for mismatched exported package**

Append to `tests/host_unit/test_target_firmware_build.py`:

```python
def test_build_target_firmware_fails_before_sdk_build_when_ep_package_mismatches(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"

    export_script = repo / "tools" / "scripts" / "export_target.sh"
    export_script.write_text(
        """#!/bin/sh
set -eu

REPO_ROOT=
TARGET=
CLEAN=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repo-root)
            REPO_ROOT=$2
            shift 2
            ;;
        --target)
            TARGET=$2
            shift 2
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        *)
            shift
            ;;
    esac
done

[ -n "$REPO_ROOT" ] || exit 2
[ -n "$TARGET" ] || exit 2

PACKAGE_ROOT="$REPO_ROOT/out/ep/$TARGET"
if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT"
fi
mkdir -p "$PACKAGE_ROOT/lib"
printf 'fake archive\\n' > "$PACKAGE_ROOT/lib/libep_app_core.a"
cat > "$PACKAGE_ROOT/manifest.json" <<EOF
{
  "package": "ep_app_core",
  "target": "$TARGET",
  "format": "static-library",
  "library": "lib/libep_app_core.a",
  "platform": {
    "family": "rtos",
    "vendor": "host",
    "sdk_family": "demo",
    "chip": "wrong-chip",
    "board": "rtos-demo",
    "kernel": "none"
  },
  "sdk": {
    "name": "fake-sdk",
    "repo": "$sdk_repo",
    "ref": "HEAD"
  },
  "toolchain": {
    "source": "sdk"
  },
  "headers": []
}
EOF
""",
        encoding="utf-8",
    )
    export_script.chmod(0o755)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--clean",
        ],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "EP_SDK_ROOT": str(sdk_root)},
    )

    assert result.returncode != 0
    assert "EP 导出包校验失败" in result.stderr
    assert "manifest platform.chip 为 wrong-chip，target 描述为 host" in result.stderr
    assert not (repo / "out" / "firmware" / "host_rtos_demo" / "firmware.bin").exists()
```

- [ ] **Step 4: Run target firmware test and verify failure**

Run:

```bash
pytest tests/host_unit/test_target_firmware_build.py::test_build_target_firmware_runs_ep_export_and_sdk_build tests/host_unit/test_target_firmware_build.py::test_build_target_firmware_fails_before_sdk_build_when_ep_package_mismatches -v
```

Expected: FAIL because `build_target_firmware.sh` does not call `validate_ep_package.sh` yet.

- [ ] **Step 5: Add validation call before SDK build**

In `tools/scripts/build_target_firmware.sh`, after the `export_target.sh` clean/non-clean block and before `SDK_BUILD_SCRIPT=...`, add:

```sh
"$REPO_ROOT/tools/scripts/validate_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --ep-package "$EP_PACKAGE_DIR"
```

- [ ] **Step 6: Run target firmware focused tests**

Run:

```bash
pytest tests/host_unit/test_target_firmware_build.py::test_build_target_firmware_runs_ep_export_and_sdk_build tests/host_unit/test_target_firmware_build.py::test_build_target_firmware_fails_before_sdk_build_when_ep_package_mismatches -v
```

Expected: PASS.

- [ ] **Step 7: Commit build-firmware integration**

Run:

```bash
git add tools/scripts/build_target_firmware.sh tests/host_unit/test_target_firmware_build.py
git commit -m "feat: 固件构建前校验EP导出包"
```

## Task 4: 文档和完整验证

**Files:**
- Modify: `docs/porting/rtos-sdk-library-model.md`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Update RTOS SDK model document**

In `docs/porting/rtos-sdk-library-model.md`, add a short section near the `manifest.json` explanation:

````markdown
## EP 导出包校验

进入 SDK 固件构建前，主工程会校验 EP 导出包是否匹配当前 target：

```sh
./build.sh validate-ep-package <target>
```

`build-firmware` 会在 `export-target` 之后、调用 SDK `scripts/build_firmware.sh` 之前自动执行这一步。校验内容包括 `manifest.json` 里的 `target`、`platform`、`sdk` 和 `toolchain` 是否与 `targets/<target>.yaml` 一致。
````

- [ ] **Step 2: Update doc assertion**

In `test_rtos_sdk_document_describes_build_firmware_entry()`, add:

```python
    assert "./build.sh validate-ep-package" in text
    assert "EP 导出包校验" in text
    assert "export-target" in text
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_ep_package_validation.py tests/host_unit/test_target_firmware_build.py -v
```

Expected: PASS.

- [ ] **Step 4: Run manual command flow**

Run:

```bash
./build.sh configure
cmake --build build --target ep_app_core_export
./build.sh export-target artinchip_d12x_lubanlite_demo --clean
./build.sh validate-ep-package artinchip_d12x_lubanlite_demo
```

Expected:

- `configure` exits `0`.
- `ep_app_core_export` target builds.
- `export-target` prints `EP 静态库导出包已生成`.
- `validate-ep-package` prints `EP 导出包校验通过`.

- [ ] **Step 5: Run full verification**

Run:

```bash
./build.sh test
git diff --check
```

Expected:

- `./build.sh test` exits `0`.
- `git diff --check` exits `0`.

- [ ] **Step 6: Commit docs and final verification coverage**

Run:

```bash
git add docs/porting/rtos-sdk-library-model.md tests/host_unit/test_target_firmware_build.py
git commit -m "docs: 记录EP导出包校验流程"
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
gh pr create --base main --head <branch> --title "feat: 增加EP导出包校验" --body "<中文PR内容>"
```

PR 内容必须包含：

- 新增 `validate-ep-package` 手动校验入口。
- `build-firmware` 在进入 SDK 构建前自动校验 EP 导出包。
- 校验字段包括 `target`、`platform`、`sdk`、`toolchain`。
- 直接 `export-ep` 行为不变。
- 测试和手动命令结果。
