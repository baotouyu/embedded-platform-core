import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "package_host.py"


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def _prepare_minimal_repo(root: Path) -> None:
    build_dir = root / "build" / "platforms" / "host" / "posix"
    for name in [
        "ep_platform_host_posix",
        "ep_host_resource_smoke",
        "ep_host_lvgl_demo",
        "ep_host_lvgl_widgets_demo",
    ]:
        _write_executable(build_dir / name)

    (root / "config" / "profiles").mkdir(parents=True, exist_ok=True)
    (root / "config" / "profiles" / "host.cfg").write_text(
        "string device.name=host\n",
        encoding="utf-8",
    )

    (root / "resources" / "host" / "images").mkdir(parents=True, exist_ok=True)
    (root / "resources" / "host" / "images" / "smoke.txt").write_text(
        "host image\n",
        encoding="utf-8",
    )
    (root / "resources" / "host" / "images" / ".gitkeep").write_text(
        "",
        encoding="utf-8",
    )
    (root / "resources" / "common" / "fonts").mkdir(parents=True, exist_ok=True)
    (root / "resources" / "common" / "fonts" / "smoke.txt").write_text(
        "common font\n",
        encoding="utf-8",
    )
    (root / "resources" / "common" / "fonts" / ".gitkeep").write_text(
        "",
        encoding="utf-8",
    )


def test_host_package_script_exists_and_describes_usage():
    assert PACKAGE_SCRIPT.is_file()

    text = PACKAGE_SCRIPT.read_text(encoding="utf-8")
    assert "package_host" in text
    assert "out/packages/host_macos" in text
    assert "manifest.txt" in text
    assert "ep_host_lvgl_widgets_demo" in text


def test_host_package_script_creates_package_from_required_outputs(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)

    output_dir = tmp_path / "package"
    result = subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "--repo-root",
            str(repo),
            "--output-dir",
            str(output_dir),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr

    package_root = output_dir / "host_macos"
    assert (package_root / "bin" / "ep_platform_host_posix").is_file()
    assert (package_root / "bin" / "ep_host_resource_smoke").is_file()
    assert (package_root / "bin" / "ep_host_lvgl_demo").is_file()
    assert (package_root / "bin" / "ep_host_lvgl_widgets_demo").is_file()
    assert (package_root / "config" / "profiles" / "host.cfg").is_file()
    assert (package_root / "resources" / "host" / "images" / "smoke.txt").is_file()
    assert (package_root / "resources" / "common" / "fonts" / "smoke.txt").is_file()

    manifest = (package_root / "manifest.txt").read_text(encoding="utf-8")
    assert "package=host_macos" in manifest
    assert "bin/ep_platform_host_posix" in manifest
    assert "config/profiles/host.cfg" in manifest
    assert "resources/host/images/smoke.txt" in manifest
    assert "resources/common/fonts/smoke.txt" in manifest
    assert ".gitkeep" not in manifest
    assert not (package_root / "resources" / "host" / "images" / ".gitkeep").exists()
    assert not (
        package_root / "resources" / "common" / "fonts" / ".gitkeep"
    ).exists()


def test_host_package_script_fails_when_required_output_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)
    (repo / "build" / "platforms" / "host" / "posix" / "ep_host_lvgl_demo").unlink()

    result = subprocess.run(
        [
            sys.executable,
            str(PACKAGE_SCRIPT),
            "--repo-root",
            str(repo),
            "--output-dir",
            str(tmp_path / "package"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "缺少必需产物" in result.stderr
    assert "ep_host_lvgl_demo" in result.stderr