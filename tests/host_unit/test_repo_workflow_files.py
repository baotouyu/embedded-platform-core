from pathlib import Path


def test_github_workflow_files_exist():
    expected = [
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/ISSUE_TEMPLATE/feature_request.md",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        ".github/workflows/ci.yml",
        "CODEOWNERS",
    ]
    missing = [path for path in expected if not Path(path).exists()]
    assert not missing, f"Missing files: {missing}"
