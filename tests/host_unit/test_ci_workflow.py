from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_ci_runs_host_contract_tests_and_cmake_build():
    workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")

    required_terms = [
        "pytest tests/host_unit tests/api_contract -v",
        "cmake -S . -B build",
        "cmake --build build",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing CI commands: {missing}"


def test_ci_does_not_checkout_private_sdk_submodules():
    workflow = REPO_ROOT / ".github" / "workflows" / "ci.yml"
    text = workflow.read_text(encoding="utf-8")

    assert "actions/checkout@v4" in text
    assert "submodules: recursive" not in text
