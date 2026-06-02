from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
TARGETS_DIR = REPO_ROOT / "targets"
HOST_RTOS_TARGET = TARGETS_DIR / "host_rtos_demo.yaml"
ARTINCHIP_D121_TARGET = TARGETS_DIR / "artinchip_d121_lubanlite_demo.yaml"


def _read_section_value(text: str, section: str, key: str) -> str:
    in_section = False
    for line in text.splitlines():
        if line == f"{section}:":
            in_section = True
            continue
        if line and not line.startswith(" ") and line.endswith(":"):
            in_section = False
        if in_section:
            prefix = f"  {key}:"
            if line.startswith(prefix):
                return line.split(":", 1)[1].strip()
    return ""


def test_host_rtos_demo_uses_platform_grouped_schema():
    text = HOST_RTOS_TARGET.read_text(encoding="utf-8")

    assert "target: host_rtos_demo" in text
    assert "platform:" in text
    assert _read_section_value(text, "platform", "family") == "rtos"
    assert _read_section_value(text, "platform", "vendor") == "host"
    assert _read_section_value(text, "platform", "sdk_family") == "demo"
    assert _read_section_value(text, "platform", "chip") == "host"
    assert _read_section_value(text, "platform", "board") == "rtos-demo"
    assert _read_section_value(text, "platform", "kernel") == "none"
    assert "os: rtos" not in text
    assert "\nvendor: host" not in text
    assert "\nsdk_family: demo" not in text


def test_target_file_names_match_declared_target_names():
    for target_file in sorted(TARGETS_DIR.glob("*.yaml")):
        text = target_file.read_text(encoding="utf-8")
        declared = ""
        for line in text.splitlines():
            if line.startswith("target:"):
                declared = line.split(":", 1)[1].strip()
                break

        assert declared, f"{target_file} 缺少 target 字段"
        assert target_file.stem == declared


def test_target_files_declare_required_schema_fields():
    for target_file in sorted(TARGETS_DIR.glob("*.yaml")):
        text = target_file.read_text(encoding="utf-8")

        assert _read_section_value(text, "platform", "family"), target_file
        assert _read_section_value(text, "platform", "vendor"), target_file
        assert _read_section_value(text, "platform", "sdk_family"), target_file
        assert _read_section_value(text, "platform", "chip"), target_file
        assert _read_section_value(text, "platform", "board"), target_file
        assert _read_section_value(text, "platform", "kernel"), target_file
        assert _read_section_value(text, "toolchain", "source"), target_file
        assert _read_section_value(text, "output", "ep_package"), target_file


def test_artinchip_d121_lubanlite_placeholder_target_exists():
    text = ARTINCHIP_D121_TARGET.read_text(encoding="utf-8")

    assert "target: artinchip_d121_lubanlite_demo" in text
    assert _read_section_value(text, "platform", "family") == "rtos"
    assert _read_section_value(text, "platform", "vendor") == "artinchip"
    assert _read_section_value(text, "platform", "sdk_family") == "luban-lite"
    assert _read_section_value(text, "platform", "chip") == "d121"
    assert _read_section_value(text, "platform", "kernel") == "rt-thread"
    assert _read_section_value(text, "sdk", "name") == "sdk-artinchip-luban-lite"
    assert _read_section_value(text, "output", "firmware") == (
        "out/firmware/artinchip_d121_lubanlite_demo"
    )
