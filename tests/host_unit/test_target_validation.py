import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
BUILD_SCRIPT = REPO_ROOT / "build.sh"
VALIDATE_SCRIPT = REPO_ROOT / "tools" / "scripts" / "validate_targets.sh"
D121_KI_TARGET = REPO_ROOT / "targets" / "artinchip_d12x_lubanlite_ki_141103_480p.yaml"
D121_KI_SDK_ENV = (
    REPO_ROOT
    / "third_party"
    / "sdk"
    / "sdk-artinchip-luban-lite"
    / "targets"
    / "artinchip_d12x_lubanlite_ki_141103_480p.env"
)
D121_KI_EP_DEFCONFIG = (
    REPO_ROOT
    / "third_party"
    / "sdk"
    / "sdk-artinchip-luban-lite"
    / "upstream"
    / "luban-lite"
    / "target"
    / "configs"
    / "d12x_KI-141103-480p_rt-thread_ep_app_defconfig"
)
D121_KI_EP_DEFCONFIG_NAME = "d12x_KI-141103-480p_rt-thread_ep_app_defconfig"
LUBAN_LITE_LV_DEMO_C = (
    REPO_ROOT
    / "third_party"
    / "sdk"
    / "sdk-artinchip-luban-lite"
    / "upstream"
    / "luban-lite"
    / "packages"
    / "artinchip"
    / "lvgl-ui"
    / "lv_demo.c"
)


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

ui:
  lvgl_provider: sdk
  lvgl_note: fake SDK provides LVGL

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


def _read_section_value(target_file: Path, section: str, key: str) -> str:
    in_section = False
    for line in target_file.read_text(encoding="utf-8").splitlines():
        if line == f"{section}:":
            in_section = True
            continue
        if line and not line.startswith(" ") and line.endswith(":"):
            in_section = False
        prefix = f"  {key}: "
        if in_section and line.startswith(prefix):
            return line.removeprefix(prefix)
    raise AssertionError(f"{target_file} missing {section}.{key}")


def test_artinchip_d12x_lubanlite_targets_cover_rt_thread_board_defconfigs():
    targets = sorted(REPO_ROOT.glob("targets/artinchip_d12x_lubanlite_*.yaml"))

    actual = {
        _read_section_value(target, "platform", "board"): _read_section_value(
            target, "sdk_config", "defconfig"
        )
        for target in targets
    }

    assert actual == {
        "demo68-mmc": "d12x_demo68-mmc_rt-thread_helloworld_defconfig",
        "demo68-nand": "d12x_demo68-nand_rt-thread_helloworld_defconfig",
        "demo68-nor": "d12x_demo68-nor_rt-thread_helloworld_defconfig",
        "KI-141103-480p": D121_KI_EP_DEFCONFIG_NAME,
        "hmi-nor": "d12x_hmi-nor_rt-thread_helloworld_defconfig",
    }
    assert all("baremetal_bootloader" not in defconfig for defconfig in actual.values())


def test_d121_ki_target_uses_ep_defconfig_without_luban_lite_demo():
    target_text = D121_KI_TARGET.read_text(encoding="utf-8")
    sdk_env_text = D121_KI_SDK_ENV.read_text(encoding="utf-8")

    assert (
        _read_section_value(D121_KI_TARGET, "sdk_config", "defconfig")
        == D121_KI_EP_DEFCONFIG_NAME
    )
    assert f"DEFCONFIG={D121_KI_EP_DEFCONFIG_NAME}" in sdk_env_text

    defconfig_text = D121_KI_EP_DEFCONFIG.read_text(encoding="utf-8")
    assert (
        f'CONFIG_PRJ_DEFCONFIG_FILENAME="{D121_KI_EP_DEFCONFIG_NAME}"'
        in defconfig_text
    )
    assert 'CONFIG_PRJ_APP="helloworld"' in defconfig_text
    assert "CONFIG_LPKG_USING_LVGL=y" in defconfig_text
    assert "CONFIG_LVGL_V_9=y" in defconfig_text
    assert "CONFIG_AIC_LVGL_DEMO=y" not in defconfig_text
    assert "CONFIG_AIC_LVGL_DEMO_HUB_DEMO=y" not in defconfig_text
    assert "CONFIG_AIC_STARTUP_UI_SHOW=y" not in defconfig_text
    assert D121_KI_EP_DEFCONFIG_NAME in target_text


def test_luban_lite_lvgl_user_init_runs_ep_ui_hook_without_demo_config():
    text = LUBAN_LITE_LV_DEMO_C.read_text(encoding="utf-8")
    hook_call = "ep_lubanlite_lvgl_app_ui_create() == 0"
    demo_guard = "#if defined(AIC_LVGL_DEMO) && !defined(RT_USING_MODULE)"

    assert "extern int ep_lubanlite_lvgl_app_ui_create(void) __attribute__((weak));" in text
    assert hook_call in text
    assert demo_guard in text
    assert text.index(hook_call) < text.index(demo_guard)


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


def test_validate_targets_fails_when_lvgl_provider_is_missing(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            """ui:
  lvgl_provider: sdk
  lvgl_note: fake SDK provides LVGL

""",
            "",
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
    assert "target 描述缺少 ui.lvgl_provider" in result.stderr


def test_validate_targets_fails_when_lvgl_provider_is_invalid(tmp_path):
    repo = tmp_path / "repo"
    _write_valid_target(repo)
    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "  lvgl_provider: sdk\n",
            "  lvgl_provider: bundled\n",
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
    assert "ui.lvgl_provider 只能是 sdk、component、prebuilt 或 none" in result.stderr


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


def test_validate_targets_prefers_checked_out_submodule_head_over_committed_gitlink(
    tmp_path,
):
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
    subprocess.run(["git", "commit", "-m", "add target and old sdk gitlink"], cwd=repo, check=True)

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
    submodule_head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=submodule,
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()

    target_file = repo / "targets" / "host_rtos_demo.yaml"
    target_file.write_text(
        target_file.read_text(encoding="utf-8").replace(
            "  ref: 0123456789abcdef0123456789abcdef01234567\n",
            f"  ref: {submodule_head}\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [str(VALIDATE_SCRIPT), "--repo-root", str(repo)],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "target 校验通过：1" in result.stdout
