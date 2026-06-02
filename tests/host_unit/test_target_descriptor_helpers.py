import subprocess
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "tools" / "scripts" / "target_descriptor.sh"
TARGET_SCRIPT_NAMES = [
    "prepare_target_sdk.sh",
    "export_target.sh",
    "build_target_firmware.sh",
]


def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_target_descriptor_helper_reads_top_level_and_section_values(tmp_path):
    target_file = tmp_path / "target.yaml"
    _write_file(
        target_file,
        """target: host_rtos_demo

platform:
  family: rtos
  vendor: host

output:
  ep_package: out/ep/host_rtos_demo
""",
    )

    script = f""". '{HELPER}'
printf 'target=%s\\n' "$(td_read_top_level_value '{target_file}' target)"
printf 'family=%s\\n' "$(td_read_section_value '{target_file}' platform family)"
printf 'ep=%s\\n' "$(td_read_section_value '{target_file}' output ep_package)"
"""

    result = subprocess.run(
        ["sh", "-c", script],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr
    assert "target=host_rtos_demo" in result.stdout
    assert "family=rtos" in result.stdout
    assert "ep=out/ep/host_rtos_demo" in result.stdout


def test_target_descriptor_helper_requires_values_with_chinese_error(tmp_path):
    target_file = tmp_path / "target.yaml"
    _write_file(target_file, "target: host_rtos_demo\n")

    script = f""". '{HELPER}'
td_require_value "$(td_read_section_value '{target_file}' sdk name)" "target 描述缺少 sdk.name：{target_file}"
"""

    result = subprocess.run(
        ["sh", "-c", script],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode != 0
    assert f"target 描述缺少 sdk.name：{target_file}" in result.stderr


def test_target_scripts_reuse_shared_descriptor_helper():
    for script_name in TARGET_SCRIPT_NAMES:
        text = (REPO_ROOT / "tools" / "scripts" / script_name).read_text(
            encoding="utf-8"
        )

        assert '. "$SCRIPT_DIR/target_descriptor.sh"' in text
        assert "\ntrim() {" not in text
        assert "\nread_top_level_value() {" not in text
        assert "\nread_section_value() {" not in text
        assert "\nread_output_ep_package() {" not in text
