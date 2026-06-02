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

    for script_name in ["target_descriptor.sh", "export_ep_package.sh"]:
        script = REPO_ROOT / "tools" / "scripts" / script_name
        script_copy = root / "tools" / "scripts" / script_name
        script_copy.parent.mkdir(parents=True, exist_ok=True)
        script_copy.write_text(script.read_text(encoding="utf-8"), encoding="utf-8")
        script_copy.chmod(0o755)


def test_host_rtos_demo_target_descriptor_exists():
    assert TARGET_FILE.is_file()
    text = TARGET_FILE.read_text(encoding="utf-8")
    assert "target: host_rtos_demo" in text
    assert "platform:" in text
    assert "family: rtos" in text
    assert "sdk_family: demo" in text
    assert "toolchain:" in text
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
