import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
BUILD_FIRMWARE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "build_target_firmware.sh"
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

    for script_name in [
        "target_descriptor.sh",
        "prepare_target_sdk.sh",
        "export_target.sh",
        "export_ep_package.sh",
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
    assert "target 校验" in text
    assert "两仓库本地联调" in text
    assert "EP_SDK_ROOT=/Users/yuwei/Documents/KitchenIdea/项目/C08" in text
    assert "host_rtos_demo" in text
    assert "platform:" in text
    assert "toolchain:" in text
    assert "sdk_config:" in text
    assert "artinchip_d12x_lubanlite_demo68_nor" in text
    assert "mode=stub" in text
    assert "SDK scripts/prepare.sh" in text
    assert "scripts/prepare.sh --target <target>" in text
    assert "SDK scripts/build_firmware.sh" in text
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
    assert (firmware / "firmware.bin").read_text(encoding="utf-8") == "fake firmware\n"

    args_text = (firmware / "build_args.txt").read_text(encoding="utf-8")
    assert "target=host_rtos_demo" in args_text
    assert f"ep_package={ep_package}" in args_text
    assert f"out={firmware}" in args_text
    assert "clean=1" in args_text
    assert "prepared=host_rtos_demo" in args_text
    assert "SDK 准备完成" in result.stdout
    assert "固件已生成" in result.stdout


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
