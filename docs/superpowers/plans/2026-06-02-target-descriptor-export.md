# Target 描述文件导出 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加第一个 `targets/host_rtos_demo.yaml`，并让 `./build.sh export-target host_rtos_demo` 通过 target 描述文件导出 EP 静态库包。

**Architecture:** 第一版 target 描述只承担“稳定入口”的职责，shell 脚本解析固定字段 `target` 和 `output.ep_package`，再调用现有 `export_ep_package.sh`。不引入通用 YAML 解析器，不接真实 Luban-Lite SDK。

**Tech Stack:** POSIX shell、pytest、YAML 风格文本、CMake 已有导出目标。

---

## 文件结构

- 新增 `targets/host_rtos_demo.yaml`：第一个伪 target 描述文件。
- 新增 `tools/scripts/export_target.sh`：读取 target 描述并调用 `export_ep_package.sh`。
- 修改 `build.sh`：新增 `export-target` 命令。
- 新增 `tests/host_unit/test_target_descriptor_export.py`：覆盖 target 文件、脚本解析、命令调度和错误处理。
- 更新 `docs/development/release-and-packaging.md`：记录 target 驱动导出命令。

## Task 1: 加 target 文件和脚本测试

**Files:**
- Create: `tests/host_unit/test_target_descriptor_export.py`
- Create: `targets/host_rtos_demo.yaml`
- Create: `tools/scripts/export_target.sh`
- Modify: `build.sh`

- [ ] **Step 1: Write failing tests**

Create `tests/host_unit/test_target_descriptor_export.py`:

```python
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
EXPORT_TARGET_SCRIPT = REPO_ROOT / "tools" / "scripts" / "export_target.sh"
TARGET_FILE = REPO_ROOT / "targets" / "host_rtos_demo.yaml"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prepare_minimal_repo(root: Path) -> None:
    _write_file(root / "build" / "libep_app_core_export.a", "fake archive\n")
    _write_file(
        root / "targets" / "host_rtos_demo.yaml",
        """target: host_rtos_demo
os: rtos
vendor: host
sdk_family: demo
chip: host
board: rtos-demo
kernel: none

output:
  ep_package: out/ep/host_rtos_demo
""",
    )
    for header in [
        "core/include/ep_framework.h",
        "app/include/app_main.h",
        "components/log/include/ep_log.h",
        "components/config/include/ep_config.h",
        "components/event/include/ep_event.h",
        "components/timer/include/ep_timer.h",
        "components/file/include/ep_file.h",
        "components/device/include/ep_device.h",
        "components/ui/include/ep_ui.h",
        "osal/include/ep_osal_time.h",
        "hal/include/ep_hal_gpio.h",
        "platforms/include/ep_platform_capability.h",
    ]:
        _write_file(root / header, f"/* {header} */\n")


def test_host_rtos_demo_target_descriptor_exists():
    assert TARGET_FILE.is_file()
    text = TARGET_FILE.read_text(encoding="utf-8")
    assert "target: host_rtos_demo" in text
    assert "os: rtos" in text
    assert "sdk_family: demo" in text
    assert "ep_package: out/ep/host_rtos_demo" in text


def test_build_help_lists_export_target_command():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "export-target" in result.stdout
    assert "targets/<target>.yaml" in result.stdout


def test_export_target_script_reads_descriptor_and_creates_package(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)

    result = subprocess.run(
        [
            str(EXPORT_TARGET_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--clean",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr

    package_root = repo / "out" / "ep" / "host_rtos_demo"
    assert (package_root / "lib" / "libep_app_core.a").read_text(
        encoding="utf-8"
    ) == "fake archive\n"

    manifest = json.loads((package_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["target"] == "host_rtos_demo"
    assert manifest["library"] == "lib/libep_app_core.a"


def test_export_target_script_fails_for_missing_descriptor(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)

    result = subprocess.run(
        [
            str(EXPORT_TARGET_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "missing_target",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "缺少 target 描述文件" in result.stderr
    assert "missing_target.yaml" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py -v
```

Expected: FAIL because `targets/host_rtos_demo.yaml` and `export_target.sh` do not exist.

- [ ] **Step 3: Add `targets/host_rtos_demo.yaml`**

Create:

```yaml
target: host_rtos_demo
os: rtos
vendor: host
sdk_family: demo
chip: host
board: rtos-demo
kernel: none

output:
  ep_package: out/ep/host_rtos_demo
```

- [ ] **Step 4: Add `tools/scripts/export_target.sh`**

Create:

```sh
#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_target.sh --target <名称> [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>     target 名称，对应 targets/<target>.yaml
  --clean            导出前删除已有输出目录
  -h, --help         显示帮助
EOF
}

die() {
    printf '%s\n' "$1" >&2
    exit 1
}

trim() {
    printf '%s' "$1" | sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
}

read_top_level_value() {
    file=$1
    key=$2
    sed -n "s/^${key}:[[:space:]]*//p" "$file" | head -n 1
}

read_output_ep_package() {
    file=$1
    awk '
        /^output:/ { in_output = 1; next }
        /^[^[:space:]].*:/ { in_output = 0 }
        in_output && /^[[:space:]]+ep_package:/ {
            sub(/^[[:space:]]+ep_package:[[:space:]]*/, "")
            print
            exit
        }
    ' "$file"
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
        --clean)
            CLEAN=1
            shift
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

declared_target=$(trim "$(read_top_level_value "$TARGET_FILE" "target")")
[ "$declared_target" = "$TARGET" ] || die "target 描述不匹配：文件内 target 为 $declared_target，命令参数为 $TARGET"

ep_package=$(trim "$(read_output_ep_package "$TARGET_FILE")")
[ -n "$ep_package" ] || die "target 描述缺少 output.ep_package：$TARGET_FILE"

output_parent=${ep_package%/*}

args="--repo-root $REPO_ROOT --target $TARGET --output-dir $output_parent"
if [ "$CLEAN" -eq 1 ]; then
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent" --clean
else
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" --repo-root "$REPO_ROOT" --target "$TARGET" --output-dir "$output_parent"
fi
```

Run:

```bash
chmod +x tools/scripts/export_target.sh
```

- [ ] **Step 5: Update `build.sh`**

Add help line:

```sh
  export-target 通过 targets/<target>.yaml 导出主工程静态库包
```

Add example:

```sh
  ./build.sh export-target host_rtos_demo
```

Add function:

```sh
run_export_target() {
    target=${1:-}
    [ -n "$target" ] || {
        printf '缺少 target 名称\n' >&2
        exit 2
    }
    shift
    "$REPO_ROOT/tools/scripts/export_target.sh" --target "$target" "$@"
}
```

Add case:

```sh
    export-target)
        run_export_target "$@"
        ;;
```

- [ ] **Step 6: Run tests to verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add build.sh targets/host_rtos_demo.yaml tools/scripts/export_target.sh tests/host_unit/test_target_descriptor_export.py docs/superpowers/plans/2026-06-02-target-descriptor-export.md
git commit -m "feat: 增加target描述文件导出入口"
```

## Task 2: 端到端验证和文档

**Files:**
- Modify: `tests/host_unit/test_target_descriptor_export.py`
- Modify: `docs/development/release-and-packaging.md`

- [ ] **Step 1: Add end-to-end build command test**

Append to `tests/host_unit/test_target_descriptor_export.py`:

```python
def test_build_script_export_target_uses_descriptor_after_build():
    configure = subprocess.run(
        [str(BUILD_SCRIPT), "configure"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert configure.returncode == 0, configure.stderr

    build = subprocess.run(
        [
            "cmake",
            "--build",
            str(REPO_ROOT / "build"),
            "--target",
            "ep_app_core_export",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert build.returncode == 0, build.stderr

    result = subprocess.run(
        [str(BUILD_SCRIPT), "export-target", "host_rtos_demo", "--clean"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr

    package_root = REPO_ROOT / "out" / "ep" / "host_rtos_demo"
    assert (package_root / "lib" / "libep_app_core.a").is_file()
    assert (package_root / "manifest.json").is_file()
```

- [ ] **Step 2: Run end-to-end test**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py::test_build_script_export_target_uses_descriptor_after_build -v
```

Expected: PASS.

- [ ] **Step 3: Update release documentation**

In `docs/development/release-and-packaging.md`, update the current first-stage command section to:

```markdown
当前第一阶段先支持伪 target：

```bash
./build.sh configure
cmake --build build --target ep_app_core_export
./build.sh export-target host_rtos_demo --clean
```

`export-target` 会读取：

```text
targets/host_rtos_demo.yaml
```
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_target_descriptor_export.py tests/host_unit/test_ep_static_library_export.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/development/release-and-packaging.md tests/host_unit/test_target_descriptor_export.py
git commit -m "docs: 记录target驱动导出命令"
```

## Task 3: 全量验证和 PR

**Files:**
- No code files.

- [ ] **Step 1: Run full verification**

Run:

```bash
./build.sh configure
./build.sh build
./build.sh test
./build.sh export-target host_rtos_demo --clean
```

Expected:

- CMake configure succeeds.
- Build succeeds.
- pytest suite passes.
- `out/ep/host_rtos_demo/lib/libep_app_core.a` exists.
- `out/ep/host_rtos_demo/manifest.json` exists.

- [ ] **Step 2: Check diff and status**

Run:

```bash
git diff --check main...HEAD
git status --short --branch
```

Expected: no whitespace errors, clean branch.

- [ ] **Step 3: Push and create PR**

Run:

```bash
git push -u origin feature/target-descriptor-export
gh pr create --base main --head feature/target-descriptor-export --title "feat: 增加target描述文件导出入口" --body "<中文 PR 内容>"
```

Expected: PR created.

