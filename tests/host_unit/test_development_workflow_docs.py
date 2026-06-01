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
        "不提前保留空目录",
        "模块化测试",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing testing strategy terms: {missing}"


def test_release_packaging_doc_defines_platform_outputs():
    doc = REPO_ROOT / "docs" / "development" / "release-and-packaging.md"

    assert doc.is_file()

    text = doc.read_text(encoding="utf-8")
    required_terms = [
        "发布和打包流程",
        "host/macOS",
        "匠芯创 Luban Lite",
        "全志 Linux",
        "可执行文件",
        "配置文件",
        "资源目录",
        "third_party/prebuilt",
        "不提交大型厂商 SDK",
    ]

    missing = [term for term in required_terms if term not in text]
    assert not missing, f"Missing release packaging terms: {missing}"


def test_platform_difference_docs_define_porting_boundaries():
    docs_and_terms = {
        REPO_ROOT / "docs" / "porting" / "platform-differences.md": [
            "平台差异整理",
            "OS 差异",
            "硬件差异",
            "启动差异",
            "LVGL 差异",
            "资源路径差异",
            "能力差异",
            "配置差异",
            "厂商 SDK",
        ],
        REPO_ROOT / "docs" / "porting" / "platform-bringup-checklist.md": [
            "平台移植检查清单",
            "新建平台目录",
            "启动入口",
            "OSAL",
            "HAL",
            "平台能力表",
            "平台路径",
            "配置文件",
            "LVGL 预编译包",
            "冒烟测试",
        ],
    }

    for doc, required_terms in docs_and_terms.items():
        assert doc.is_file()
        text = doc.read_text(encoding="utf-8")
        missing = [term for term in required_terms if term not in text]
        assert not missing, f"Missing terms in {doc}: {missing}"
