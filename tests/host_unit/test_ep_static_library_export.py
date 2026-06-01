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
