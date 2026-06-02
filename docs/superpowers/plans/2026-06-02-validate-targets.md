# Target 校验入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增 `./build.sh validate-targets`，统一校验 `targets/*.yaml` 是否符合当前 target 描述规范。

**Architecture:** 新增 POSIX shell 脚本 `tools/scripts/validate_targets.sh`，复用 `tools/scripts/target_descriptor.sh` 读取固定字段。`build.sh` 只负责命令分发，校验逻辑集中在脚本里；测试用临时 repo 构造合法和非法 target，不依赖真实 SDK。

**Tech Stack:** POSIX shell、pytest、现有 target descriptor helper、现有 `build.sh` 命令分发。

---

## 文件结构

- 新增 `tools/scripts/validate_targets.sh`：校验 `targets/*.yaml`。
- 修改 `build.sh`：新增 `validate-targets` 帮助文案和命令分发。
- 新增 `tests/host_unit/test_target_validation.py`：覆盖命令入口、合法 target 和非法 target 错误。
- 修改 `docs/porting/rtos-sdk-library-model.md`：记录 `./build.sh validate-targets`。
- 可选修改 `.github/workflows/ci.yml`：如果当前 CI 只跑 `./build.sh test`，本次先不改 CI；因为完整测试里已经覆盖命令入口。后续单独 PR 再把 validate 明确放进 CI。

## Task 1: 增加 validate-targets 命令入口测试

**Files:**
- Create: `tests/host_unit/test_target_validation.py`
- Modify: `build.sh`

- [ ] **Step 1: Write failing command tests**

Create `tests/host_unit/test_target_validation.py`:

```python
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
VALIDATE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "validate_targets.sh"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_build_help_lists_validate_targets_command():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "validate-targets" in result.stdout
    assert "校验 targets/*.yaml" in result.stdout


def test_validate_targets_script_exists_and_uses_descriptor_helper():
    assert VALIDATE_SCRIPT.is_file()
    text = VALIDATE_SCRIPT.read_text(encoding="utf-8")

    assert '. "$SCRIPT_DIR/target_descriptor.sh"' in text
    assert "td_read_section_value" in text
    assert "td_validate_declared_target" in text
```

- [ ] **Step 2: Run command tests and verify they fail**

Run:

```bash
pytest tests/host_unit/test_target_validation.py::test_build_help_lists_validate_targets_command tests/host_unit/test_target_validation.py::test_validate_targets_script_exists_and_uses_descriptor_helper -v
```

Expected: FAIL because `validate-targets` is not in help and `tools/scripts/validate_targets.sh` does not exist.

- [ ] **Step 3: Add `validate-targets` help and dispatch to `build.sh`**

In `print_help()`, add command:

```text
  validate-targets 校验 targets/*.yaml 描述文件
```

In examples, add:

```text
  ./build.sh validate-targets
```

Add function:

```sh
run_validate_targets() {
    "$REPO_ROOT/tools/scripts/validate_targets.sh" "$@"
}
```

Add case branch:

```sh
    validate-targets)
        run_validate_targets "$@"
        ;;
```

- [ ] **Step 4: Add minimal `tools/scripts/validate_targets.sh`**

Create:

```sh
#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
. "$SCRIPT_DIR/target_descriptor.sh"

REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)

print_help() {
    cat <<EOF
用法:
  tools/scripts/validate_targets.sh [参数]

参数:
  --repo-root <路径>  仓库根目录，默认自动使用当前脚本所在仓库
  -h, --help         显示帮助
EOF
}

while [ "$#" -gt 0 ]; do
    case "$1" in
        --repo-root)
            [ "$#" -ge 2 ] || td_die "缺少 --repo-root 参数值"
            REPO_ROOT=$2
            shift 2
            ;;
        -h|--help)
            print_help
            exit 0
            ;;
        *)
            td_die "未知参数：$1"
            ;;
    esac
done

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)

printf 'target 校验通过：0\n'
```

Make it executable:

```bash
chmod +x tools/scripts/validate_targets.sh
```

- [ ] **Step 5: Run command tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_validation.py::test_build_help_lists_validate_targets_command tests/host_unit/test_target_validation.py::test_validate_targets_script_exists_and_uses_descriptor_helper -v
```

Expected: PASS.

- [ ] **Step 6: Commit command entry**

Run:

```bash
git add build.sh tools/scripts/validate_targets.sh tests/host_unit/test_target_validation.py
git commit -m "feat: 增加target校验命令入口"
```

## Task 2: 校验合法 target 和目录存在

**Files:**
- Modify: `tools/scripts/validate_targets.sh`
- Modify: `tests/host_unit/test_target_validation.py`

- [ ] **Step 1: Add passing target validation tests**

Append to `tests/host_unit/test_target_validation.py`:

```python
def _write_valid_target(root: Path, name: str = "host_rtos_demo") -> None:
    _write_file(
        root / "targets" / f"{name}.yaml",
        f"""target: {name}

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
  ep_package: out/ep/{name}
  firmware: out/firmware/{name}
""",
    )


def test_validate_targets_passes_for_current_repository_targets():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "validate-targets"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "target 校验通过：" in result.stdout


def test_validate_targets_passes_for_valid_temp_repo(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "target 校验通过：1" in result.stdout
```

- [ ] **Step 2: Run tests and verify temp repo test fails**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: FAIL because script still always prints `target 校验通过：0`.

- [ ] **Step 3: Implement target iteration and count**

Replace the final `printf` in `tools/scripts/validate_targets.sh` with:

```sh
TARGET_DIR=$REPO_ROOT/targets
[ -d "$TARGET_DIR" ] || td_die "缺少 targets 目录：$TARGET_DIR"

count=0
for target_file in "$TARGET_DIR"/*.yaml; do
    [ -e "$target_file" ] || td_die "没有 target 描述文件：$TARGET_DIR/*.yaml"
    count=$((count + 1))

    target_name=$(basename "$target_file" .yaml)
    td_validate_declared_target "$target_file" "$target_name"
done

printf 'target 校验通过：%s\n' "$count"
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: PASS for command entry and valid target tests.

- [ ] **Step 5: Commit valid target validation**

Run:

```bash
git add tools/scripts/validate_targets.sh tests/host_unit/test_target_validation.py
git commit -m "feat: 校验target文件入口"
```

## Task 3: 校验必填字段和 RTOS 字段

**Files:**
- Modify: `tools/scripts/validate_targets.sh`
- Modify: `tests/host_unit/test_target_validation.py`

- [ ] **Step 1: Add required field failure tests**

Append:

```python
def test_validate_targets_fails_when_file_name_mismatches_target(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo, name="real_target")
    (repo / "targets" / "real_target.yaml").rename(repo / "targets" / "wrong_name.yaml")

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述不匹配" in result.stderr


def test_validate_targets_fails_when_platform_family_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace("  family: rtos\n", ""),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述缺少 platform.family" in result.stderr


def test_validate_targets_fails_when_rtos_sdk_name_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace("  name: fake-sdk\n", ""),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述缺少 sdk.name" in result.stderr


def test_validate_targets_fails_when_rtos_firmware_output_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "  firmware: out/firmware/host_rtos_demo\n", ""
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述缺少 output.firmware" in result.stderr
```

- [ ] **Step 2: Run tests and verify required field tests fail**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: FAIL because script only checks target name so far.

- [ ] **Step 3: Implement required field checks**

Add helper functions before target iteration:

```sh
require_section_value() {
    target_file=$1
    section=$2
    key=$3
    value=$(td_trim "$(td_read_section_value "$target_file" "$section" "$key")")
    td_require_value "$value" "target 描述缺少 ${section}.${key}：$target_file"
    printf '%s\n' "$value"
}
```

Inside the loop after `td_validate_declared_target`:

```sh
platform_family=$(require_section_value "$target_file" "platform" "family")
require_section_value "$target_file" "platform" "vendor" >/dev/null
require_section_value "$target_file" "platform" "sdk_family" >/dev/null
require_section_value "$target_file" "platform" "chip" >/dev/null
require_section_value "$target_file" "platform" "board" >/dev/null
require_section_value "$target_file" "platform" "kernel" >/dev/null
require_section_value "$target_file" "toolchain" "source" >/dev/null
require_section_value "$target_file" "output" "ep_package" >/dev/null

if [ "$platform_family" = "rtos" ]; then
    require_section_value "$target_file" "sdk" "name" >/dev/null
    require_section_value "$target_file" "sdk" "repo" >/dev/null
    require_section_value "$target_file" "sdk" "ref" >/dev/null
    require_section_value "$target_file" "output" "firmware" >/dev/null
fi
```

- [ ] **Step 4: Run tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit required field checks**

Run:

```bash
git add tools/scripts/validate_targets.sh tests/host_unit/test_target_validation.py
git commit -m "feat: 校验target必填字段"
```

## Task 4: 禁止旧字段和本地 SDK 路径

**Files:**
- Modify: `tools/scripts/validate_targets.sh`
- Modify: `tests/host_unit/test_target_validation.py`

- [ ] **Step 1: Add forbidden content tests**

Append:

```python
def test_validate_targets_fails_when_old_top_level_os_is_used(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "target: host_rtos_demo\n",
            "target: host_rtos_demo\nos: rtos\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述禁止使用旧顶层字段 os" in result.stderr


def test_validate_targets_fails_when_local_sdk_path_is_used(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "  ref: main\n",
            "  ref: main\n  path: .sdk/fake-sdk\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述不能写本地 SDK 路径" in result.stderr
```

- [ ] **Step 2: Run tests and verify forbidden content tests fail**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: FAIL because script does not scan forbidden content yet.

- [ ] **Step 3: Implement forbidden old top-level field checks**

Add before required field checks inside the loop:

```sh
for old_key in os vendor sdk_family chip board kernel; do
    if grep -q "^${old_key}:" "$target_file"; then
        td_die "target 描述禁止使用旧顶层字段 ${old_key}：$target_file"
    fi
done
```

- [ ] **Step 4: Implement local SDK path checks**

Add after old field checks:

```sh
if grep -q '\.sdk\|/Users/\|/opt/' "$target_file"; then
    td_die "target 描述不能写本地 SDK 路径：$target_file"
fi
```

- [ ] **Step 5: Run tests and verify they pass**

Run:

```bash
pytest tests/host_unit/test_target_validation.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit forbidden content checks**

Run:

```bash
git add tools/scripts/validate_targets.sh tests/host_unit/test_target_validation.py
git commit -m "feat: 校验target禁止字段"
```

## Task 5: 更新文档和完整验证

**Files:**
- Modify: `docs/porting/rtos-sdk-library-model.md`
- Modify: `tests/host_unit/test_target_firmware_build.py`

- [ ] **Step 1: Update RTOS SDK model document**

In `docs/porting/rtos-sdk-library-model.md`, add a short section after target descriptor example with this content:

Section title:

```markdown
## target 校验
```

Body:

```markdown
新增或修改 target 后，先运行：

```
./build.sh validate-targets
```

这个命令只校验 `targets/*.yaml` 的结构和约定，不拉取 SDK，也不执行编译。它会检查 target 名、`platform:` 分组、SDK 来源字段、输出目录和禁止的本地 SDK 路径。
```

- [ ] **Step 2: Update doc assertion**

In `tests/host_unit/test_target_firmware_build.py`, update `test_rtos_sdk_document_describes_build_firmware_entry()` to include:

```python
assert "./build.sh validate-targets" in text
assert "target 校验" in text
```

- [ ] **Step 3: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_target_validation.py tests/host_unit/test_target_firmware_build.py tests/host_unit/test_target_descriptor_schema.py -v
```

Expected: PASS.

- [ ] **Step 4: Run command manually**

Run:

```bash
./build.sh validate-targets
```

Expected:

```text
target 校验通过：2
```

- [ ] **Step 5: Run full verification**

Run:

```bash
./build.sh test
git diff --check
```

Expected:

- `./build.sh test` exits `0`.
- `git diff --check` exits `0`.

- [ ] **Step 6: Commit documentation**

Run:

```bash
git add docs/porting/rtos-sdk-library-model.md tests/host_unit/test_target_firmware_build.py
git commit -m "docs: 记录target校验命令"
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
gh pr create --base main --head <branch> --title "feat: 增加target校验入口" --body "<中文PR内容>"
```

PR 内容必须包含：

- 新增 `./build.sh validate-targets`。
- 校验规则摘要。
- 测试和手动命令结果。
