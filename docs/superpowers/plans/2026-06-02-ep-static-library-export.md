# 主工程静态库导出包 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加主工程 `out/ep/<target>` 静态库导出包，为后续 RTOS SDK 链接打包做准备。

**Architecture:** 第一阶段只支持伪 target `host_rtos_demo`，不接真实 Luban-Lite 工具链。CMake 负责生成 `ep_app_core_export` 静态库，shell 脚本负责复制库、导出公共头文件并写 manifest，`build.sh export-ep` 负责调度。

**Tech Stack:** C、CMake、POSIX shell、pytest、GitHub PR 流程。

---

## 文件结构

- 新增 `cmake/modules/ep_export_targets.cmake`：定义 `ep_app_core_export` 静态库目标，第一版复用当前源码和 RTOS demo stub。
- 修改 `CMakeLists.txt`：include 新模块，让导出库目标参与配置。
- 新增 `tools/scripts/export_ep_package.sh`：生成 `out/ep/<target>` 导出包。
- 修改 `build.sh`：新增 `export-ep` 命令。
- 新增 `tests/host_unit/test_ep_static_library_export.py`：覆盖脚本、help、包格式、manifest 和构建目标。
- 更新 `docs/development/release-and-packaging.md`：记录当前导出命令。

## Task 1: 写导出脚本和 build.sh 入口测试

**Files:**
- Create: `tests/host_unit/test_ep_static_library_export.py`
- Modify: `build.sh`
- Create: `tools/scripts/export_ep_package.sh`

- [ ] **Step 1: Write the failing tests**

Create `tests/host_unit/test_ep_static_library_export.py`:

```python
import json
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
EXPORT_SCRIPT = REPO_ROOT / "tools" / "scripts" / "export_ep_package.sh"


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _prepare_minimal_repo(root: Path) -> None:
    _write_file(
        root / "build" / "libep_app_core_export.a",
        "fake archive\n",
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


def test_export_script_exists_and_build_help_lists_command():
    assert EXPORT_SCRIPT.is_file()

    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "export-ep" in result.stdout
    assert "out/ep/<target>" in result.stdout


def test_export_script_creates_standard_package_from_existing_archive(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)

    result = subprocess.run(
        [
            str(EXPORT_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--output-dir",
            str(tmp_path / "out" / "ep"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr

    package_root = tmp_path / "out" / "ep" / "host_rtos_demo"
    assert (package_root / "lib" / "libep_app_core.a").read_text(
        encoding="utf-8"
    ) == "fake archive\n"
    assert (package_root / "include" / "ep_framework.h").is_file()
    assert (package_root / "include" / "ep_log.h").is_file()
    assert (package_root / "include" / "ep_hal_gpio.h").is_file()

    manifest = json.loads((package_root / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["package"] == "ep_app_core"
    assert manifest["target"] == "host_rtos_demo"
    assert manifest["format"] == "static-library"
    assert manifest["library"] == "lib/libep_app_core.a"
    assert "include/ep_framework.h" in manifest["headers"]
    assert "include/ep_platform_capability.h" in manifest["headers"]


def test_export_script_fails_when_archive_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)
    (repo / "build" / "libep_app_core_export.a").unlink()

    result = subprocess.run(
        [
            str(EXPORT_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--output-dir",
            str(tmp_path / "out" / "ep"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "缺少静态库产物" in result.stderr
    assert "libep_app_core_export.a" in result.stderr
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py -v
```

Expected: FAIL because `tools/scripts/export_ep_package.sh` does not exist and `build.sh help` does not list `export-ep`.

- [ ] **Step 3: Implement `tools/scripts/export_ep_package.sh`**

Create `tools/scripts/export_ep_package.sh`:

```sh
#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPO_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
TARGET=host_rtos_demo
OUTPUT_DIR=out/ep
CLEAN=0

print_help() {
    cat <<EOF
用法:
  tools/scripts/export_ep_package.sh [参数]

参数:
  --repo-root <路径>   仓库根目录，默认自动使用当前脚本所在仓库
  --target <名称>      导出目标名称，默认 host_rtos_demo
  --output-dir <路径>  输出父目录，脚本会生成 <路径>/<target>
  --clean             导出前删除已有 target 输出目录
  -h, --help          显示帮助

默认输出:
  out/ep/<target>
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

json_escape() {
    printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
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
        --output-dir)
            [ "$#" -ge 2 ] || die "缺少 --output-dir 参数值"
            OUTPUT_DIR=$2
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

REPO_ROOT=$(CDPATH= cd -- "$REPO_ROOT" && pwd)
OUTPUT_DIR=$(resolve_path "$OUTPUT_DIR" "$REPO_ROOT")
PACKAGE_ROOT=$OUTPUT_DIR/$TARGET
ARCHIVE=$REPO_ROOT/build/libep_app_core_export.a

[ -f "$ARCHIVE" ] || die "缺少静态库产物：$ARCHIVE，请先执行 ./build.sh build"

HEADER_DIRS="
core/include
app/include
components/log/include
components/config/include
components/event/include
components/timer/include
components/file/include
components/device/include
components/ui/include
osal/include
hal/include
platforms/include
"

missing=""
for dir in $HEADER_DIRS; do
    [ -d "$REPO_ROOT/$dir" ] || missing="${missing}
- $REPO_ROOT/$dir"
done

[ -z "$missing" ] || die "缺少头文件目录：$missing"

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$PACKAGE_ROOT"
fi

mkdir -p "$PACKAGE_ROOT/lib" "$PACKAGE_ROOT/include"
cp -p "$ARCHIVE" "$PACKAGE_ROOT/lib/libep_app_core.a"

for dir in $HEADER_DIRS; do
    find "$REPO_ROOT/$dir" -type f -name '*.h' -print | while IFS= read -r header; do
        cp -p "$header" "$PACKAGE_ROOT/include/$(basename -- "$header")"
    done
done

MANIFEST=$PACKAGE_ROOT/manifest.json
{
    printf '{\n'
    printf '  "package": "ep_app_core",\n'
    printf '  "target": "%s",\n' "$(json_escape "$TARGET")"
    printf '  "format": "static-library",\n'
    printf '  "library": "lib/libep_app_core.a",\n'
    printf '  "headers": [\n'

    first=1
    find "$PACKAGE_ROOT/include" -type f -name '*.h' -print | sort | while IFS= read -r header; do
        relative=${header#"$PACKAGE_ROOT"/}
        if [ "$first" -eq 1 ]; then
            first=0
        else
            printf ',\n'
        fi
        printf '    "%s"' "$(json_escape "$relative")"
    done

    printf '\n  ]\n'
    printf '}\n'
} > "$MANIFEST"

file_count=$(find "$PACKAGE_ROOT" -type f | wc -l | tr -d ' ')

printf 'EP 静态库导出包已生成：%s\n' "$PACKAGE_ROOT"
printf '文件数量：%s\n' "$file_count"
printf '清单文件：%s\n' "$MANIFEST"
```

Run:

```bash
chmod +x tools/scripts/export_ep_package.sh
```

- [ ] **Step 4: Update `build.sh`**

Modify `build.sh`:

```sh
  export-ep    生成主工程静态库导出包 out/ep/<target>
```

Add function:

```sh
run_export_ep() {
    "$REPO_ROOT/tools/scripts/export_ep_package.sh" "$@"
}
```

Add case:

```sh
    export-ep)
        run_export_ep "$@"
        ;;
```

Add help example:

```sh
  ./build.sh export-ep --clean
```

- [ ] **Step 5: Run tests to verify they pass**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add build.sh tools/scripts/export_ep_package.sh tests/host_unit/test_ep_static_library_export.py
git commit -m "feat: 增加EP静态库导出脚本"
```

## Task 2: 增加 CMake 导出库目标

**Files:**
- Create: `cmake/modules/ep_export_targets.cmake`
- Modify: `CMakeLists.txt`
- Modify: `tests/host_unit/test_ep_static_library_export.py`

- [ ] **Step 1: Add failing build target test**

Append to `tests/host_unit/test_ep_static_library_export.py`:

```python
def test_ep_static_library_export_target_builds(tmp_path):
    build_dir = tmp_path / "build"

    configure = subprocess.run(
        ["cmake", "-S", str(REPO_ROOT), "-B", str(build_dir)],
        check=False,
        text=True,
        capture_output=True,
    )
    assert configure.returncode == 0, configure.stderr

    build = subprocess.run(
        [
            "cmake",
            "--build",
            str(build_dir),
            "--target",
            "ep_app_core_export",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert build.returncode == 0, build.stderr
    assert (build_dir / "libep_app_core_export.a").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py::test_ep_static_library_export_target_builds -v
```

Expected: FAIL because CMake target `ep_app_core_export` does not exist.

- [ ] **Step 3: Create `cmake/modules/ep_export_targets.cmake`**

Create file:

```cmake
add_library(ep_app_core_export STATIC
  ${CMAKE_SOURCE_DIR}/core/src/ep_framework.c
  ${CMAKE_SOURCE_DIR}/app/main.c
  ${CMAKE_SOURCE_DIR}/components/config/src/ep_config.c
  ${CMAKE_SOURCE_DIR}/components/event/src/ep_event.c
  ${CMAKE_SOURCE_DIR}/components/file/src/ep_file.c
  ${CMAKE_SOURCE_DIR}/components/log/src/ep_log.c
  ${CMAKE_SOURCE_DIR}/components/timer/src/ep_timer.c
  ${CMAKE_SOURCE_DIR}/components/device/src/ep_device.c
  ${CMAKE_SOURCE_DIR}/components/ui/src/ep_ui.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/startup/app_start.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/osal_port/ep_rtos_osal_stub.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/hal_port/ep_rtos_hal_stub.c
  ${CMAKE_SOURCE_DIR}/platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/src/elog_utils.c
  ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/port/elog_port.c
)

set_target_properties(ep_app_core_export
  PROPERTIES
    OUTPUT_NAME ep_app_core_export
)

target_include_directories(ep_app_core_export
  PUBLIC
    ${CMAKE_SOURCE_DIR}/core/include
    ${CMAKE_SOURCE_DIR}/app/include
    ${CMAKE_SOURCE_DIR}/components/config/include
    ${CMAKE_SOURCE_DIR}/components/device/include
    ${CMAKE_SOURCE_DIR}/components/event/include
    ${CMAKE_SOURCE_DIR}/components/file/include
    ${CMAKE_SOURCE_DIR}/components/log/include
    ${CMAKE_SOURCE_DIR}/components/timer/include
    ${CMAKE_SOURCE_DIR}/components/ui/include
    ${CMAKE_SOURCE_DIR}/osal/include
    ${CMAKE_SOURCE_DIR}/hal/include
    ${CMAKE_SOURCE_DIR}/platforms/include
  PRIVATE
    ${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc
    ${EP_LVGL_INCLUDE_DIR}
)

target_link_libraries(ep_app_core_export
  PRIVATE
    ep_thirdparty_lvgl
)
```

- [ ] **Step 4: Include module in top-level CMake**

Modify `CMakeLists.txt` after third_party/components are available:

```cmake
include(ep_export_targets)
```

Place it after `add_subdirectory(components/ui)` so `ep_thirdparty_lvgl` is already defined.

- [ ] **Step 5: Run target build test**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py::test_ep_static_library_export_target_builds -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add CMakeLists.txt cmake/modules/ep_export_targets.cmake tests/host_unit/test_ep_static_library_export.py
git commit -m "feat: 增加EP应用核心导出库目标"
```

## Task 3: 串通 build.sh export-ep 和文档

**Files:**
- Modify: `tests/host_unit/test_ep_static_library_export.py`
- Modify: `docs/development/release-and-packaging.md`

- [ ] **Step 1: Add end-to-end export test**

Append to `tests/host_unit/test_ep_static_library_export.py`:

```python
def test_build_script_export_ep_creates_package_after_build():
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

    export = subprocess.run(
        [str(BUILD_SCRIPT), "export-ep", "--clean", "--target", "host_rtos_demo"],
        check=False,
        text=True,
        capture_output=True,
    )
    assert export.returncode == 0, export.stderr

    package_root = REPO_ROOT / "out" / "ep" / "host_rtos_demo"
    assert (package_root / "lib" / "libep_app_core.a").is_file()
    assert (package_root / "include" / "ep_framework.h").is_file()
    assert (package_root / "manifest.json").is_file()
```

- [ ] **Step 2: Run end-to-end test**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py::test_build_script_export_ep_creates_package_after_build -v
```

Expected: PASS.

- [ ] **Step 3: Update release documentation**

In `docs/development/release-and-packaging.md`, add a small section under RTOS/Luban-Lite product boundary:

```markdown
当前第一阶段先支持伪 target：

```bash
./build.sh configure
cmake --build build --target ep_app_core_export
./build.sh export-ep --clean --target host_rtos_demo
```

输出目录：

```text
out/ep/host_rtos_demo/
  lib/libep_app_core.a
  include/
  manifest.json
```

这个 target 只用于验证主工程导出包格式，不代表已经完成真实 Luban-Lite 适配。
```

- [ ] **Step 4: Run focused tests**

Run:

```bash
pytest tests/host_unit/test_ep_static_library_export.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add docs/development/release-and-packaging.md tests/host_unit/test_ep_static_library_export.py
git commit -m "docs: 记录EP静态库导出命令"
```

## Task 4: 全量验证和 PR

**Files:**
- No code files.

- [ ] **Step 1: Run full verification**

Run:

```bash
./build.sh configure
./build.sh build
./build.sh test
./build.sh export-ep --clean --target host_rtos_demo
```

Expected:

- CMake configure succeeds.
- Build succeeds.
- pytest suite passes.
- `out/ep/host_rtos_demo/lib/libep_app_core.a` exists.
- `out/ep/host_rtos_demo/manifest.json` exists.

- [ ] **Step 2: Check git status**

Run:

```bash
git status --short --branch
```

Expected: clean branch, ahead of origin only by planned commits.

- [ ] **Step 3: Push and create PR**

Run:

```bash
git push -u origin feature/ep-static-library-export
gh pr create --base main --head feature/ep-static-library-export --title "feat: 增加主工程静态库导出包" --body "<中文 PR 内容>"
```

Expected: PR created.
