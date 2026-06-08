import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
PACKAGE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "package_host.sh"


def _write_executable(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    path.chmod(0o755)


def _prepare_minimal_repo(root: Path) -> None:
    build_dir = root / "build" / "platforms" / "host" / "posix"
    for name in [
        "ep_platform_host_posix",
        "ep_host_app",
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
    assert BUILD_SCRIPT.is_file()
    assert PACKAGE_SCRIPT.is_file()
    assert not (REPO_ROOT / "tools" / "scripts" / "package_host.py").exists()

    build_text = BUILD_SCRIPT.read_text(encoding="utf-8")
    assert "package-host" in build_text
    assert "build-host" in build_text
    assert "host)" in build_text
    assert "run-host-app" in build_text
    assert "help" in build_text

    text = PACKAGE_SCRIPT.read_text(encoding="utf-8")
    assert "package_host.sh" in text
    assert "out/packages/host_macos" in text
    assert "manifest.txt" in text
    assert "ep_host_app" in text
    assert "ep_host_lvgl_widgets_demo" in text


def test_build_script_help_lists_supported_commands():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "用法" in result.stdout
    assert "configure" in result.stdout
    assert "build" in result.stdout
    assert "test" in result.stdout
    assert "host" in result.stdout
    assert "build-host" in result.stdout
    assert "run-host-app" in result.stdout
    assert "package-host" in result.stdout
    assert "clean" in result.stdout
    assert "all" in result.stdout


def test_build_script_run_host_app_builds_and_runs_host_app_target():
    build_text = BUILD_SCRIPT.read_text(encoding="utf-8")

    assert "run_host_app()" in build_text
    assert "host|build-host|run-host-app" in build_text
    assert "uname -s" in build_text
    assert "uname -m" in build_text
    assert "run-host-app 目前只支持 macOS arm64" in build_text
    assert 'cmake --build "$BUILD_DIR" --target ep_host_app' in build_text
    assert '"$BUILD_DIR/platforms/host/posix/ep_host_app"' in build_text


def test_build_script_run_host_app_fails_clearly_on_non_macos_arm64():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "run-host-app"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    assert "run-host-app 目前只支持 macOS arm64" in result.stderr
    assert "没有规则可制作目标" not in result.stderr


def test_host_package_script_creates_package_from_required_outputs(tmp_path):
    repo = tmp_path / "repo"
    _prepare_minimal_repo(repo)

    output_dir = tmp_path / "package"
    result = subprocess.run(
        [
            str(BUILD_SCRIPT),
            "package-host",
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
    assert (package_root / "bin" / "ep_host_app").is_file()
    assert (package_root / "bin" / "ep_host_resource_smoke").is_file()
    assert (package_root / "bin" / "ep_host_lvgl_demo").is_file()
    assert (package_root / "bin" / "ep_host_lvgl_widgets_demo").is_file()
    assert (package_root / "config" / "profiles" / "host.cfg").is_file()
    assert (package_root / "resources" / "host" / "images" / "smoke.txt").is_file()
    assert (package_root / "resources" / "common" / "fonts" / "smoke.txt").is_file()

    manifest = (package_root / "manifest.txt").read_text(encoding="utf-8")
    assert "package=host_macos" in manifest
    assert "bin/ep_platform_host_posix" in manifest
    assert "bin/ep_host_app" in manifest
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
