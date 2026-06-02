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
