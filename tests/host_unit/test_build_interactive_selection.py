import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
SELECT_SCRIPT = REPO_ROOT / "tools" / "scripts" / "select_target.sh"


def _write_target(
    root: Path,
    name: str,
    *,
    vendor: str,
    sdk_family: str,
    chip: str,
    board: str,
) -> None:
    target_file = root / "targets" / f"{name}.yaml"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text(
        f"""target: {name}

platform:
  family: rtos
  vendor: {vendor}
  sdk_family: {sdk_family}
  chip: {chip}
  board: {board}
  kernel: rt-thread

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
        encoding="utf-8",
    )


def test_select_target_filters_targets_by_hierarchical_choices(tmp_path):
    repo = tmp_path / "repo"
    _write_target(
        repo,
        "artinchip_d12x_demo68",
        vendor="artinchip",
        sdk_family="luban-lite",
        chip="d12x",
        board="demo68-nor",
    )
    _write_target(
        repo,
        "artinchip_d12x_custom",
        vendor="artinchip",
        sdk_family="luban-lite",
        chip="d12x",
        board="custom-board",
    )
    _write_target(
        repo,
        "host_rtos_demo",
        vendor="host",
        sdk_family="demo",
        chip="host",
        board="rtos-demo",
    )

    result = subprocess.run(
        [str(SELECT_SCRIPT), "--repo-root", str(repo)],
        input="1\n2\n1\n",
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == "target=artinchip_d12x_demo68\naction=show-target\n"
    assert "已选平台类型：rtos" not in result.stderr
    assert "选择厂商" in result.stderr
    assert "选择板级方案" in result.stderr
    assert "选择动作" in result.stderr
    assert "1) show-target - 只显示选择结果" in result.stderr
    assert "2) check-env - 检查 SDK 环境" in result.stderr
    assert "3) install-env - 安装/修复 SDK 环境" in result.stderr
    assert "4) prepare-sdk - 准备外部SDK" in result.stderr
    assert "5) export-target - 导出EP静态库包" in result.stderr
    assert "6) build-firmware - 准备SDK、检查环境并编译固件" in result.stderr
    assert "7) full - 准备SDK、检查环境、导出EP包并编译固件" in result.stderr


def test_build_script_interactive_can_preview_selected_target():
    result = subprocess.run(
        [str(BUILD_SCRIPT), "interactive"],
        input="1\n4\n1\n",
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "已选平台类型：rtos" in result.stderr
    assert "已选SDK：luban-lite" in result.stderr
    assert "选择板级方案" in result.stderr
    assert "1) KI-141103-480p" in result.stderr
    assert "2) demo68-mmc" in result.stderr
    assert "3) demo68-nand" in result.stderr
    assert "4) demo68-nor" in result.stderr
    assert "5) hmi-nor" in result.stderr
    assert "已选板级方案：demo68-nor" in result.stderr
    assert "1) show-target - 只显示选择结果" in result.stderr
    assert "2) check-env - 检查 SDK 环境" in result.stderr
    assert "3) install-env - 安装/修复 SDK 环境" in result.stderr
    assert "4) prepare-sdk - 准备外部SDK" in result.stderr
    assert "5) export-target - 导出EP静态库包" in result.stderr
    assert "6) build-firmware - 准备SDK、检查环境并编译固件" in result.stderr
    assert "7) full - 准备SDK、检查环境、导出EP包并编译固件" in result.stderr
    assert "已选择 target：artinchip_d12x_lubanlite_demo68_nor" in result.stdout
    assert "已选择动作：show-target" in result.stdout
