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
