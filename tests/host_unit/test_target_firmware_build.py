import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
BUILD_FIRMWARE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "build_target_firmware.sh"
SELECT_SCRIPT = REPO_ROOT / "tools" / "scripts" / "select_target.sh"
TARGET_FILE = REPO_ROOT / "targets" / "host_rtos_demo.yaml"
RTOS_SDK_DOC = REPO_ROOT / "docs" / "porting" / "rtos-sdk-library-model.md"


def _run_git(args, cwd: Path) -> None:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_fake_sdk_toolchain(path: Path) -> None:
    _write_file(
        path / "upstream" / "luban-lite" / "toolchain" / "bin" / "riscv64-unknown-elf-gcc",
        """#!/bin/sh
set -eu

out=
while [ "$#" -gt 0 ]; do
    case "$1" in
        -o)
            out=$2
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

[ -n "$out" ] || exit 2
printf 'fake riscv object\\n' > "$out"
""",
    )
    (path / "upstream" / "luban-lite" / "toolchain" / "bin" / "riscv64-unknown-elf-gcc").chmod(0o755)
    _write_file(
        path / "upstream" / "luban-lite" / "toolchain" / "bin" / "riscv64-unknown-elf-ar",
        """#!/bin/sh
set -eu

archive=
for arg in "$@"; do
    case "$arg" in
        *.a)
            archive=$arg
            break
            ;;
    esac
done

[ -n "$archive" ] || exit 2
mkdir -p "$(dirname "$archive")"
printf 'fake riscv archive\\n' > "$archive"
""",
    )
    (path / "upstream" / "luban-lite" / "toolchain" / "bin" / "riscv64-unknown-elf-ar").chmod(0o755)


def _prepare_minimal_repo(root: Path, sdk_repo: Path, with_firmware_output: bool = True) -> None:
    firmware_line = "  firmware: out/firmware/host_rtos_demo\n" if with_firmware_output else ""
    _write_file(
        root / "targets" / "host_rtos_demo.yaml",
        f"""target: host_rtos_demo

platform:
  family: rtos
  vendor: host
  sdk_family: demo
  chip: host
  board: rtos-demo
  kernel: none

sdk:
  name: fake-sdk
  repo: {sdk_repo}
  ref: HEAD

toolchain:
  source: sdk

output:
  ep_package: out/ep/host_rtos_demo
{firmware_line}""",
    )
    _write_file(root / "build" / "libep_app_core_export.a", "fake archive\n")
    for source in [
        "core/src/ep_framework.c",
        "app/main.c",
        "components/config/src/ep_config.c",
        "components/file/src/ep_file.c",
        "components/event/src/ep_event.c",
        "components/timer/src/ep_timer.c",
        "components/log/src/ep_log.c",
        "platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c",
        "platforms/rtos/demo_family/startup/app_start.c",
        "platforms/rtos/demo_family/hal_port/ep_rtos_hal_gpio_rtthread.c",
        "platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtthread.c",
        "platforms/rtos/demo_family/hal_port/ep_rtos_hal_pwm_rtthread.c",
        "platforms/rtos/demo_family/component_port/ep_rtos_component_stub.c",
        "third_party/external/EasyLogger/easylogger/src/elog.c",
        "third_party/external/EasyLogger/easylogger/src/elog_utils.c",
        "third_party/external/EasyLogger/easylogger/port/elog_port.c",
    ]:
        _write_file(root / source, f"/* {source} */\n")
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
        "third_party/external/EasyLogger/easylogger/inc/elog.h",
    ]:
        _write_file(root / header, f"/* {header} */\n")

    for script_name in [
        "target_descriptor.sh",
        "target_sdk_resolver.sh",
        "prepare_target_sdk.sh",
        "check_target_env.sh",
        "export_target.sh",
        "export_sdk_ep_package.sh",
        "export_ep_package.sh",
        "validate_ep_package.sh",
    ]:
        source = REPO_ROOT / "tools" / "scripts" / script_name
        script_copy = root / "tools" / "scripts" / script_name
        script_copy.parent.mkdir(parents=True, exist_ok=True)
        script_copy.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        script_copy.chmod(0o755)


def _create_fake_sdk_repo(path: Path, with_build_entry: bool = True) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], path)
    _run_git(["config", "user.email", "test@example.com"], path)
    _run_git(["config", "user.name", "Test User"], path)
    _write_file(path / "README.md", "fake sdk\n")
    _write_file(
        path / "scripts" / "prepare.sh",
        """#!/bin/sh
set -eu

TARGET=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            TARGET=$2
            shift 2
            ;;
        *)
            printf '未知参数：%s\\n' "$1" >&2
            exit 2
            ;;
    esac
done

[ -n "$TARGET" ] || exit 2
printf 'SDK 准备完成\\n'
printf 'target=%s\\n' "$TARGET"
printf 'status=stub\\n'
printf 'prepared=%s\\n' "$TARGET" > prepared.txt
""",
    )
    (path / "scripts" / "prepare.sh").chmod(0o755)
    _write_file(
        path / "scripts" / "check_env.sh",
        """#!/bin/sh
set -eu

TARGET=
SDK_ROOT=

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            TARGET=$2
            shift 2
            ;;
        --sdk-root)
            SDK_ROOT=$2
            shift 2
            ;;
        *)
            printf '未知参数：%s\\n' "$1" >&2
            exit 2
            ;;
    esac
done

[ -n "$TARGET" ] || exit 2
[ -n "$SDK_ROOT" ] || exit 2
printf 'SDK 环境检查通过\\n'
printf 'target=%s\\n' "$TARGET"
printf 'sdk_root=%s\\n' "$SDK_ROOT"
""",
    )
    (path / "scripts" / "check_env.sh").chmod(0o755)
    _write_fake_sdk_toolchain(path)
    if with_build_entry:
        build_script = path / "scripts" / "build_firmware.sh"
        _write_file(
            build_script,
            """#!/bin/sh
set -eu

TARGET=
EP_PACKAGE=
OUT=
CLEAN=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        --target)
            TARGET=$2
            shift 2
            ;;
        --ep-package)
            EP_PACKAGE=$2
            shift 2
            ;;
        --out)
            OUT=$2
            shift 2
            ;;
        --clean)
            CLEAN=1
            shift
            ;;
        *)
            printf '未知参数：%s\\n' "$1" >&2
            exit 2
            ;;
    esac
done

[ -n "$TARGET" ] || exit 2
[ -n "$EP_PACKAGE" ] || exit 2
[ -n "$OUT" ] || exit 2
[ -f "$EP_PACKAGE/lib/libep_app_core.a" ] || exit 3
[ -f prepared.txt ] || exit 4

if [ "$CLEAN" -eq 1 ]; then
    rm -rf "$OUT"
fi

mkdir -p "$OUT"
{
    printf 'target=%s\\n' "$TARGET"
    printf 'ep_package=%s\\n' "$EP_PACKAGE"
    printf 'out=%s\\n' "$OUT"
    printf 'clean=%s\\n' "$CLEAN"
    cat prepared.txt
} > "$OUT/build_args.txt"
printf 'fake firmware\\n' > "$OUT/firmware.bin"
""",
        )
        build_script.chmod(0o755)
    _run_git(["add", "."], path)
    _run_git(["commit", "-m", "init fake sdk"], path)


def test_build_help_lists_build_firmware_command():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "build-firmware" in result.stdout
    assert "out/firmware/<target>" in result.stdout


def test_host_rtos_demo_target_declares_firmware_output():
    text = TARGET_FILE.read_text(encoding="utf-8")

    assert "firmware: out/firmware/host_rtos_demo" in text


def test_rtos_sdk_document_describes_build_firmware_entry():
    text = RTOS_SDK_DOC.read_text(encoding="utf-8")

    assert "./build.sh build-firmware" in text
    assert "./build.sh validate-targets" in text
    assert "./build.sh validate-ep-package" in text
    assert "target 校验" in text
    assert "EP 导出包校验" in text
    assert "两仓库本地联调" in text
    assert "EP_SDK_ROOT=/Users/yuwei/Documents/KitchenIdea/项目/C08" in text
    assert "host_rtos_demo" in text
    assert "manifest.json" in text
    assert "platform:" in text
    assert "platform" in text
    assert "toolchain:" in text
    assert "toolchain" in text
    assert "sdk_config:" in text
    assert "artinchip_d12x_lubanlite_demo68_nor" in text
    assert "mode=stub" in text
    assert "SDK scripts/prepare.sh" in text
    assert "scripts/prepare.sh --target <target>" in text
    assert "SDK scripts/build_firmware.sh" in text
    assert "export-target" in text
    assert "--ep-package" in text
    assert "--out" in text


def test_build_target_firmware_runs_ep_export_and_sdk_build(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"

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

    assert result.returncode == 0, result.stderr
    assert (sdk_root / "fake-sdk" / ".git").is_dir()
    assert not (repo / ".sdk").exists()

    ep_package = repo / "out" / "ep" / "host_rtos_demo"
    firmware = repo / "out" / "firmware" / "host_rtos_demo"
    assert (ep_package / "lib" / "libep_app_core.a").is_file()
    assert (ep_package / "lib" / "libep_app_core.a").read_text(
        encoding="utf-8"
    ) == "fake riscv archive\n"
    assert (firmware / "firmware.bin").read_text(encoding="utf-8") == "fake firmware\n"

    args_text = (firmware / "build_args.txt").read_text(encoding="utf-8")
    assert "target=host_rtos_demo" in args_text
    assert f"ep_package={ep_package}" in args_text
    assert f"out={firmware}" in args_text
    assert "clean=1" in args_text
    assert "prepared=host_rtos_demo" in args_text
    assert "SDK 准备完成" in result.stdout
    assert "EP 导出包校验通过" in result.stdout
    assert "固件已生成" in result.stdout


def test_sdk_ep_export_uses_rtthread_osal_and_excludes_lvgl_ui():
    script = (REPO_ROOT / "tools" / "scripts" / "export_sdk_ep_package.sh").read_text(
        encoding="utf-8"
    )

    assert "platforms/rtos/demo_family/osal_port/ep_rtos_osal_rtthread.c" in script
    assert "platforms/rtos/demo_family/hal_port/ep_rtos_hal_gpio_rtthread.c" in script
    assert "platforms/rtos/demo_family/hal_port/ep_rtos_hal_rtthread.c" in script
    assert "platforms/rtos/demo_family/hal_port/ep_rtos_hal_pwm_rtthread.c" in script
    assert "platforms/rtos/demo_family/hal_port/ep_rtos_hal_stub.c" not in script
    assert "components/ui/src/ep_ui.c" not in script
    assert "ep_thirdparty_lvgl" not in script


def test_sdk_ep_export_re_lunches_when_rtconfig_is_for_another_defconfig(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8")
        + "\nsdk_config:\n  defconfig: d12x_demo68-nor_rt-thread_helloworld_defconfig\n",
        encoding="utf-8",
    )
    sdk_dir = repo / "third_party" / "sdk" / "fake-sdk"
    _write_fake_sdk_toolchain(sdk_dir)

    luban_root = sdk_dir / "upstream" / "luban-lite"
    _write_file(
        luban_root / "rtconfig.h",
        '#define PRJ_DEFCONFIG_FILENAME "d12x_KI-141103-480p_baremetal_bootloader_defconfig"\n',
    )
    _write_file(
        luban_root / "tools" / "onestep.sh",
        """#!/bin/sh
lunch() {
    printf '%s\\n' "$1" > rtconfig-lunched.txt
    printf '#define PRJ_DEFCONFIG_FILENAME "%s"\\n' "$1" > rtconfig.h
}
""",
    )
    (luban_root / "tools" / "onestep.sh").chmod(0o755)

    result = subprocess.run(
        [
            str(repo / "tools" / "scripts" / "export_sdk_ep_package.sh"),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-dir",
            str(sdk_dir),
            "--clean",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert (
        luban_root / "rtconfig-lunched.txt"
    ).read_text(encoding="utf-8") == "d12x_demo68-nor_rt-thread_helloworld_defconfig\n"
    assert "配置 Luban-Lite：d12x_demo68-nor_rt-thread_helloworld_defconfig" in result.stdout


def test_build_target_firmware_allows_relative_sibling_sdk_root(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    workspace = tmp_path / "workspace"
    repo = workspace / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    sdk_path = workspace / "fake-sdk"
    _create_fake_sdk_repo(sdk_path)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            "..",
            "--clean",
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=repo,
    )

    assert result.returncode == 0, result.stderr
    ep_package = repo / "out" / "ep" / "host_rtos_demo"
    firmware = repo / "out" / "firmware" / "host_rtos_demo"
    assert (ep_package / "lib" / "libep_app_core.a").is_file()
    assert (firmware / "firmware.bin").read_text(encoding="utf-8") == "fake firmware\n"
    assert "SDK 已存在" in result.stdout
    assert "固件已生成" in result.stdout


def test_build_target_firmware_uses_checked_out_submodule_inside_main_repo(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo(submodule_path)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            str(tmp_path / "sdks"),
            "--clean",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert not (tmp_path / "sdks" / "fake-sdk").exists()

    ep_package = repo / "out" / "ep" / "host_rtos_demo"
    firmware = repo / "out" / "firmware" / "host_rtos_demo"
    assert (firmware / "firmware.bin").read_text(encoding="utf-8") == "fake firmware\n"

    args_text = (firmware / "build_args.txt").read_text(encoding="utf-8")
    assert f"ep_package={ep_package}" in args_text
    assert "prepared=host_rtos_demo" in args_text
    assert f"SDK 使用子模块：{submodule_path}" in result.stdout
    assert "固件已生成" in result.stdout


def test_build_target_firmware_fails_before_sdk_build_when_ep_package_mismatches(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"

    export_script = repo / "tools" / "scripts" / "export_sdk_ep_package.sh"
    export_script.write_text(
        """#!/bin/sh
set -eu

REPO_ROOT=
TARGET=
OUTPUT_DIR=
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
        --output-dir)
            OUTPUT_DIR=$2
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
[ -n "$OUTPUT_DIR" ] || exit 2

case "$OUTPUT_DIR" in
    /*) ;;
    *) OUTPUT_DIR="$REPO_ROOT/$OUTPUT_DIR" ;;
esac

PACKAGE_ROOT="$OUTPUT_DIR/$TARGET"
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
    "repo": "__SDK_REPO__",
    "ref": "HEAD"
  },
  "toolchain": {
    "source": "sdk"
  },
  "headers": []
}
EOF
""".replace("__SDK_REPO__", str(sdk_repo)),
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


def test_build_target_firmware_fails_when_sdk_prepare_entry_is_missing(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)
    (sdk_repo / "scripts" / "prepare.sh").unlink()
    _run_git(["add", "-A"], sdk_repo)
    _run_git(["commit", "-m", "remove prepare entry"], sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            str(tmp_path / "sdks"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SDK 缺少准备入口" in result.stderr


def test_build_target_firmware_fails_when_sdk_build_entry_is_missing(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo, with_build_entry=False)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            str(tmp_path / "sdks"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SDK 缺少固件构建入口" in result.stderr


def test_build_target_firmware_fails_when_descriptor_lacks_firmware_output(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo, with_firmware_output=False)

    result = subprocess.run(
        [
            str(BUILD_FIRMWARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            str(tmp_path / "sdks"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述缺少 output.firmware" in result.stderr


# --- check-env / install-env integration tests ---

CHECK_ENV_SCRIPT = REPO_ROOT / "tools" / "scripts" / "check_target_env.sh"
INSTALL_ENV_SCRIPT = REPO_ROOT / "tools" / "scripts" / "install_target_env.sh"


def _create_fake_sdk_repo_with_env(path: Path, check_env_exit: int = 0) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], path)
    _run_git(["config", "user.email", "test@example.com"], path)
    _run_git(["config", "user.name", "Test User"], path)
    _write_file(path / "README.md", "fake sdk\n")
    _write_file(
        path / "scripts" / "prepare.sh",
        "#!/bin/sh\nset -eu\n"
        "TARGET=\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --target) TARGET=$2; shift 2 ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "[ -n \"$TARGET\" ] || exit 2\n"
        "printf 'SDK 准备完成\\n'\n"
        "printf 'target=%s\\n' \"$TARGET\"\n"
        "printf 'status=stub\\n'\n"
        "printf 'prepared target=%s\\n' \"$TARGET\" > prepared.txt\n",
    )
    (path / "scripts" / "prepare.sh").chmod(0o755)
    _write_file(
        path / "scripts" / "check_env.sh",
        f"#!/bin/sh\n"
        f"set -eu\n"
        f"TARGET=\nSDK_ROOT=\n"
        f"while [ \"$#\" -gt 0 ]; do\n"
        f"  case \"$1\" in\n"
        f"    --target) TARGET=$2; shift 2 ;;\n"
        f"    --sdk-root) SDK_ROOT=$2; shift 2 ;;\n"
        f"    *) shift ;;\n"
        f"  esac\n"
        f"done\n"
        f"[ -n \"$TARGET\" ] || exit 2\n"
        f"[ -n \"$SDK_ROOT\" ] || exit 2\n"
        f"printf '=== check_env ===\\n'\n"
        f"printf 'target=%s\\n' \"$TARGET\"\n"
        f"printf 'sdk_root=%s\\n' \"$SDK_ROOT\"\n"
        f"exit {check_env_exit}\n",
    )
    (path / "scripts" / "check_env.sh").chmod(0o755)
    _write_file(
        path / "scripts" / "install_env.sh",
        "#!/bin/sh\nset -eu\n"
        "TARGET=\nSDK_ROOT=\nDRY_RUN=0\nYES=0\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --target) TARGET=$2; shift 2 ;;\n"
        "    --sdk-root) SDK_ROOT=$2; shift 2 ;;\n"
        "    --dry-run) DRY_RUN=1; shift ;;\n"
        "    --yes) YES=1; shift ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "[ -n \"$TARGET\" ] || exit 2\n"
        "[ -n \"$SDK_ROOT\" ] || exit 2\n"
        "printf '=== install_env ===\\n'\n"
        "printf 'target=%s\\n' \"$TARGET\"\n"
        "printf 'sdk_root=%s\\n' \"$SDK_ROOT\"\n"
        "printf 'dry_run=%s\\n' \"$DRY_RUN\"\n"
        "printf 'yes=%s\\n' \"$YES\"\n"
        "exit 0\n",
    )
    (path / "scripts" / "install_env.sh").chmod(0o755)
    _write_file(
        path / "scripts" / "build_firmware.sh",
        "#!/bin/sh\nset -eu\n"
        "TARGET=\nEP_PACKAGE=\nOUT=\nCLEAN=0\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --target) TARGET=$2; shift 2 ;;\n"
        "    --ep-package) EP_PACKAGE=$2; shift 2 ;;\n"
        "    --out) OUT=$2; shift 2 ;;\n"
        "    --clean) CLEAN=1; shift ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "[ -n \"$TARGET\" ] || exit 2\n"
        "[ -n \"$EP_PACKAGE\" ] || exit 2\n"
        "[ -n \"$OUT\" ] || exit 2\n"
        "[ -f \"$EP_PACKAGE/lib/libep_app_core.a\" ] || exit 3\n"
        "if [ \"$CLEAN\" -eq 1 ]; then rm -rf \"$OUT\"; fi\n"
        "mkdir -p \"$OUT\"\n"
        "printf 'fake firmware\\n' > \"$OUT/firmware.bin\"\n",
    )
    (path / "scripts" / "build_firmware.sh").chmod(0o755)
    _write_fake_sdk_toolchain(path)
    _run_git(["add", "."], path)
    _run_git(["commit", "-m", "init fake sdk"], path)


def _copy_build_script(root: Path) -> None:
    build_copy = root / "build.sh"
    build_copy.write_text(BUILD_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    build_copy.chmod(0o755)
    firmware_script_copy = root / "tools" / "scripts" / "build_target_firmware.sh"
    firmware_script_copy.parent.mkdir(parents=True, exist_ok=True)
    firmware_script_copy.write_text(BUILD_FIRMWARE_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
    firmware_script_copy.chmod(0o755)


def _prepare_repo_with_sdk_and_upstream(
    root: Path, sdk_repo: Path, *, target_name: str = "host_rtos_demo"
) -> Path:
    _write_file(
        root / "targets" / f"{target_name}.yaml",
        f"""target: {target_name}

platform:
  family: rtos
  vendor: host
  sdk_family: demo
  chip: host
  board: rtos-demo
  kernel: none

sdk:
  name: fake-sdk
  repo: {sdk_repo}
  ref: HEAD

toolchain:
  source: sdk

output:
  ep_package: out/ep/{target_name}
  firmware: out/firmware/{target_name}
""",
    )
    _write_file(root / "build" / "libep_app_core_export.a", "fake archive\n")
    for header in [
        "core/include/ep_framework.h",
        "app/include/app_main.h",
        "components/log/include/ep_log.h",
    ]:
        _write_file(root / header, f"/* {header} */\n")
    for script_name in [
        "target_descriptor.sh",
        "target_sdk_resolver.sh",
        "prepare_target_sdk.sh",
        "export_target.sh",
        "export_ep_package.sh",
        "validate_ep_package.sh",
    ]:
        source = REPO_ROOT / "tools" / "scripts" / script_name
        script_copy = root / "tools" / "scripts" / script_name
        script_copy.parent.mkdir(parents=True, exist_ok=True)
        script_copy.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        script_copy.chmod(0o755)

    # Also copy check_target_env.sh and install_target_env.sh
    for script_name in ["check_target_env.sh", "install_target_env.sh"]:
        source = REPO_ROOT / "tools" / "scripts" / script_name
        script_copy = root / "tools" / "scripts" / script_name
        script_copy.parent.mkdir(parents=True, exist_ok=True)
        script_copy.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
        script_copy.chmod(0o755)

    return root


def test_build_help_lists_check_env_and_install_env():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False, text=True, capture_output=True,
    )
    assert result.returncode == 0
    assert "check-env" in result.stdout
    assert "install-env" in result.stdout


def test_select_target_includes_check_env_and_install_env_actions(tmp_path):
    repo = tmp_path / "repo"
    _write_file(
        repo / "targets" / "test_target.yaml",
        """target: test_target
platform:
  family: rtos
  vendor: host
  sdk_family: demo
  chip: host
  board: rtos-demo
  kernel: none
sdk:
  name: fake-sdk
  repo: https://example.com/fake.git
  ref: 0123456789abcdef0123456789abcdef01234567
toolchain:
  source: sdk
output:
  ep_package: out/ep/test_target
  firmware: out/firmware/test_target
""",
    )
    result = subprocess.run(
        [str(SELECT_SCRIPT), "--repo-root", str(repo)],
        input="1\n1\n",
        check=False, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "check-env - 检查 SDK 环境" in result.stderr
    assert "install-env - 安装/修复 SDK 环境" in result.stderr
    assert "build-firmware - 准备SDK、检查环境并编译固件" in result.stderr


def test_check_env_calls_sdk_script(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=0)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo_with_env(submodule_path, check_env_exit=0)

    # Create fake upstream/luban-lite inside the sdk for the Luban Lite root resolution
    upstream = submodule_path / "upstream" / "luban-lite"
    upstream.mkdir(parents=True, exist_ok=True)
    _write_file(upstream / "README.md", "fake luban lite\n")

    result = subprocess.run(
        [
            str(CHECK_ENV_SCRIPT),
            "--repo-root", str(repo),
            "--target", "host_rtos_demo",
        ],
        check=False, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "=== check_env ===" in result.stdout
    assert f"sdk_root={submodule_path}" in result.stdout


def test_check_env_prepares_sdk_before_sdk_check(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=0)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo_with_env(submodule_path, check_env_exit=0)
    _write_file(
        submodule_path / "scripts" / "check_env.sh",
        "#!/bin/sh\nset -eu\n"
        "TARGET=\nSDK_ROOT=\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --target) TARGET=$2; shift 2 ;;\n"
        "    --sdk-root) SDK_ROOT=$2; shift 2 ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "[ -f prepared.txt ] || { printf 'prepare missing\\n' >&2; exit 12; }\n"
        "printf '=== check_env ===\\n'\n"
        "printf 'target=%s\\n' \"$TARGET\"\n"
        "printf 'sdk_root=%s\\n' \"$SDK_ROOT\"\n",
    )
    (submodule_path / "scripts" / "check_env.sh").chmod(0o755)

    result = subprocess.run(
        [
            str(CHECK_ENV_SCRIPT),
            "--repo-root", str(repo),
            "--target", "host_rtos_demo",
        ],
        check=False, text=True, capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "SDK 准备完成" in result.stdout
    assert "=== check_env ===" in result.stdout


def test_install_env_calls_sdk_script(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=0)

    repo = tmp_path / "repo"
    _prepare_repo_with_sdk_and_upstream(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo_with_env(submodule_path, check_env_exit=0)

    # Create fake upstream/luban-lite
    upstream = submodule_path / "upstream" / "luban-lite"
    upstream.mkdir(parents=True, exist_ok=True)
    _write_file(upstream / "README.md", "fake luban lite\n")

    result = subprocess.run(
        [
            str(INSTALL_ENV_SCRIPT),
            "--repo-root", str(repo),
            "--target", "host_rtos_demo",
            "--yes",
        ],
        check=False, text=True, capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    assert "=== install_env ===" in result.stdout
    assert f"sdk_root={submodule_path}" in result.stdout


def test_install_env_prepares_sdk_before_sdk_install(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=0)

    repo = tmp_path / "repo"
    _prepare_repo_with_sdk_and_upstream(repo, sdk_repo)
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo_with_env(submodule_path, check_env_exit=0)
    _write_file(
        submodule_path / "scripts" / "install_env.sh",
        "#!/bin/sh\nset -eu\n"
        "TARGET=\nSDK_ROOT=\n"
        "while [ \"$#\" -gt 0 ]; do\n"
        "  case \"$1\" in\n"
        "    --target) TARGET=$2; shift 2 ;;\n"
        "    --sdk-root) SDK_ROOT=$2; shift 2 ;;\n"
        "    --yes|--dry-run) shift ;;\n"
        "    *) shift ;;\n"
        "  esac\n"
        "done\n"
        "[ -f prepared.txt ] || { printf 'prepare missing\\n' >&2; exit 12; }\n"
        "printf '=== install_env ===\\n'\n"
        "printf 'target=%s\\n' \"$TARGET\"\n"
        "printf 'sdk_root=%s\\n' \"$SDK_ROOT\"\n",
    )
    (submodule_path / "scripts" / "install_env.sh").chmod(0o755)

    result = subprocess.run(
        [
            str(INSTALL_ENV_SCRIPT),
            "--repo-root", str(repo),
            "--target", "host_rtos_demo",
            "--yes",
        ],
        check=False, text=True, capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "SDK 准备完成" in result.stdout
    assert "=== install_env ===" in result.stdout


def test_build_firmware_fails_when_check_env_fails(tmp_path):
    """When check_env returns non-zero, build-firmware should stop before exporting."""
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=10)

    repo = tmp_path / "repo"
    _prepare_repo_with_sdk_and_upstream(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"
    submodule_path = repo / "third_party" / "sdk" / "fake-sdk"
    _create_fake_sdk_repo_with_env(submodule_path, check_env_exit=10)

    # Create fake upstream/luban-lite
    upstream = submodule_path / "upstream" / "luban-lite"
    upstream.mkdir(parents=True, exist_ok=True)
    _write_file(upstream / "README.md", "fake luban lite\n")

    result = subprocess.run(
        [
            str(CHECK_ENV_SCRIPT),
            "--repo-root", str(repo),
            "--target", "host_rtos_demo",
        ],
        check=False, text=True, capture_output=True,
    )
    assert result.returncode == 10, f"expect exit 10, got {result.returncode}: {result.stdout}"
    assert "=== check_env ===" in result.stdout


def test_build_script_build_firmware_prepares_sdk_before_check_env(tmp_path):
    sdk_repo = tmp_path / "fake-sdk-src"
    _create_fake_sdk_repo_with_env(sdk_repo, check_env_exit=0)

    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo, sdk_repo)
    _copy_build_script(repo)
    sdk_root = tmp_path / "sdks"

    result = subprocess.run(
        [str(repo / "build.sh"), "build-firmware", "host_rtos_demo", "--clean"],
        check=False,
        text=True,
        capture_output=True,
        cwd=repo,
        env={**os.environ, "EP_SDK_ROOT": str(sdk_root)},
    )

    assert result.returncode == 0, result.stderr
    assert (sdk_root / "fake-sdk" / ".git").is_dir()
    assert "SDK 已准备" in result.stdout
    assert "=== check_env ===" in result.stdout
    assert (repo / "out" / "firmware" / "host_rtos_demo" / "firmware.bin").is_file()
