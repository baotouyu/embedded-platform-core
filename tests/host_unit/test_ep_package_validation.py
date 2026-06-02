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
