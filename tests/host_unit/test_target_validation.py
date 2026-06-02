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
  ref: 0123456789abcdef0123456789abcdef01234567

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


def test_validate_targets_ignores_uninitialized_submodule_placeholder(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    placeholder = repo / "third_party" / "sdk" / "fake-sdk"
    placeholder.mkdir(parents=True)

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
            "  ref: 0123456789abcdef0123456789abcdef01234567\n",
            "  ref: 0123456789abcdef0123456789abcdef01234567\n  path: .sdk/fake-sdk\n",
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


def test_validate_targets_fails_when_sdk_ref_is_floating(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "  ref: 0123456789abcdef0123456789abcdef01234567\n",
            "  ref: main\n",
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
    assert "target 描述不能使用浮动 sdk.ref" in result.stderr


def test_validate_targets_fails_when_submodule_head_mismatches_sdk_ref(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    submodule = repo / "third_party" / "sdk" / "fake-sdk"
    submodule.mkdir(parents=True)
    subprocess.run(["git", "init"], cwd=submodule, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=submodule,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=submodule,
        check=True,
        capture_output=True,
    )
    (submodule / "README.md").write_text("fake sdk\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=submodule, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init fake sdk"],
        cwd=submodule,
        check=True,
        capture_output=True,
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SDK 子模块 HEAD 与 target sdk.ref 不一致" in result.stderr


def test_validate_targets_fails_when_gitlink_mismatches_sdk_ref_without_checkout(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)

    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "add", "targets/host_rtos_demo.yaml"], cwd=repo, check=True)
    subprocess.run(
        [
            "git",
            "update-index",
            "--add",
            "--cacheinfo",
            "160000,ffffffffffffffffffffffffffffffffffffffff,third_party/sdk/fake-sdk",
        ],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(["git", "commit", "-m", "add target and sdk gitlink"], cwd=repo, check=True)

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SDK 子模块 gitlink 与 target sdk.ref 不一致" in result.stderr
