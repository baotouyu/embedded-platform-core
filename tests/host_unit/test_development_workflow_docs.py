from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_github_workflow_doc_exists_and_describes_pr_flow():
    doc = REPO_ROOT / "docs" / "development" / "github-workflow.md"
    text = doc.read_text(encoding="utf-8")

    required_terms = [
        "受保护主干",
        "feature/",
        "Pull Request",
        "CI",
        "Squash and merge",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing workflow terms: {missing}"


def test_testing_strategy_doc_exists_and_defines_test_layers():
    doc = REPO_ROOT / "docs" / "development" / "testing-strategy.md"
    text = doc.read_text(encoding="utf-8")

    required_terms = [
        "tests/host_unit",
        "tests/api_contract",
        "tests/integration",
        "tests/target_smoke",
        "模块化测试",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing testing strategy terms: {missing}"
