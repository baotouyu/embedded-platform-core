import os
import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
PREPARE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "prepare_target_sdk.sh"
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


def _create_local_sdk_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(["init"], path)
    _run_git(["config", "user.email", "test@example.com"], path)
    _run_git(["config", "user.name", "Test User"], path)
    _write_file(path / "README.md", "fake sdk\n")
    _run_git(["add", "README.md"], path)
    _run_git(["commit", "-m", "init fake sdk"], path)


def _prepare_repo_with_target(root: Path, sdk_repo: Path) -> None:
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
""",
    )


def test_host_rtos_demo_target_declares_sdk_boundary():
    text = TARGET_FILE.read_text(encoding="utf-8")

    assert "sdk:" in text
    assert "name:" in text
    assert "repo:" in text
    assert "ref:" in text
    assert "path:" not in text
    assert ".sdk" not in text


def test_build_help_lists_prepare_sdk_command():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "help"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0
    assert "prepare-sdk" in result.stdout
    assert "targets/<target>.yaml" in result.stdout
    assert "../sdks" in result.stdout


def test_rtos_sdk_document_keeps_local_sdk_outside_main_repo():
    text = RTOS_SDK_DOC.read_text(encoding="utf-8")

    assert "EP_SDK_ROOT" in text
    assert "../sdks" in text
    assert "path: .sdk" not in text
    assert ".sdk/" not in text


def test_prepare_target_sdk_clones_missing_sdk_from_descriptor(tmp_path):
    sdk_repo = tmp_path / "fake-sdk"
    _create_local_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_repo_with_target(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
        ],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "EP_SDK_ROOT": str(sdk_root)},
    )

    assert result.returncode == 0, result.stderr
    sdk_path = sdk_root / "fake-sdk"
    assert (sdk_path / ".git").is_dir()
    assert (sdk_path / "README.md").read_text(encoding="utf-8") == "fake sdk\n"
    assert not (repo / ".sdk").exists()
    assert "SDK 已准备" in result.stdout


def test_prepare_target_sdk_uses_sibling_sdks_directory_by_default(tmp_path):
    sdk_repo = tmp_path / "fake-sdk"
    _create_local_sdk_repo(sdk_repo)

    repo = tmp_path / "workspace" / "repo"
    _prepare_repo_with_target(repo, sdk_repo)
    env = {key: value for key, value in os.environ.items() if key != "EP_SDK_ROOT"}

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
        ],
        check=False,
        text=True,
        capture_output=True,
        env=env,
    )

    assert result.returncode == 0, result.stderr
    sdk_path = repo.parent / "sdks" / "fake-sdk"
    assert (sdk_path / ".git").is_dir()
    assert not (repo / ".sdk").exists()
    assert "SDK 已准备" in result.stdout


def test_prepare_target_sdk_reuses_existing_sdk_directory(tmp_path):
    sdk_repo = tmp_path / "fake-sdk"
    _create_local_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_repo_with_target(repo, sdk_repo)
    sdk_root = tmp_path / "sdks"
    sdk_path = sdk_root / "fake-sdk"
    sdk_path.mkdir(parents=True)
    _write_file(sdk_path / "marker.txt", "existing\n")

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
        ],
        check=False,
        text=True,
        capture_output=True,
        env={**os.environ, "EP_SDK_ROOT": str(sdk_root)},
    )

    assert result.returncode == 0, result.stderr
    assert (sdk_path / "marker.txt").read_text(encoding="utf-8") == "existing\n"
    assert not (repo / ".sdk").exists()
    assert "SDK 已存在" in result.stdout


def test_prepare_target_sdk_allows_relative_sibling_sdk_root(tmp_path):
    sdk_repo = tmp_path / "fake-sdk"
    _create_local_sdk_repo(sdk_repo)

    workspace = tmp_path / "workspace"
    repo = workspace / "repo"
    _prepare_repo_with_target(repo, sdk_repo)
    sdk_path = workspace / "fake-sdk"
    sdk_path.mkdir(parents=True)
    _write_file(sdk_path / "marker.txt", "existing sibling sdk\n")

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            "..",
        ],
        check=False,
        text=True,
        capture_output=True,
        cwd=repo,
    )

    assert result.returncode == 0, result.stderr
    assert (sdk_path / "marker.txt").read_text(encoding="utf-8") == "existing sibling sdk\n"
    assert "SDK 已存在" in result.stdout


def test_prepare_target_sdk_rejects_sdk_root_inside_main_repo(tmp_path):
    sdk_repo = tmp_path / "fake-sdk"
    _create_local_sdk_repo(sdk_repo)

    repo = tmp_path / "repo"
    _prepare_repo_with_target(repo, sdk_repo)

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
            "--sdk-root",
            str(repo / "sdks"),
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "SDK 本地缓存不能放在主工程目录内" in result.stderr
    assert not (repo / "sdks").exists()


def test_prepare_target_sdk_fails_when_descriptor_lacks_sdk(tmp_path):
    repo = tmp_path / "repo"
    _write_file(
        repo / "targets" / "host_rtos_demo.yaml",
        """target: host_rtos_demo
platform:
  family: rtos
  vendor: host
  sdk_family: demo
  chip: host
  board: rtos-demo
  kernel: none

toolchain:
  source: sdk

output:
  ep_package: out/ep/host_rtos_demo
""",
    )

    result = subprocess.run(
        [
            str(PREPARE_SCRIPT),
            "--repo-root",
            str(repo),
            "--target",
            "host_rtos_demo",
        ],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert "target 描述缺少 sdk.name" in result.stderr
