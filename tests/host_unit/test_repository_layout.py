from pathlib import Path


REQUIRED_DIRECTORIES = [
    "cmake/modules",
    "cmake/toolchains",
    "cmake/presets",
    "docs/architecture",
    "docs/porting",
    "docs/testing",
    "docs/decisions",
    "core/include",
    "core/src",
    "components/log",
    "components/event",
    "components/timer",
    "components/config",
    "components/device",
    "components/file",
    "platforms/rtos/common",
    "platforms/linux/common",
    "platforms/include",
    "vendor",
    "config/common",
    "config/feature",
    "config/profiles",
    "resources/common/images",
    "resources/common/fonts",
    "resources/common/themes",
    "resources/host/images",
    "resources/host/fonts",
    "resources/host/themes",
    "tests/host_unit",
    "tests/api_contract",
    "tools/scripts",
    "tools/ci",
    "third_party/external/EasyLogger",
    "third_party/external/cjson",
    "third_party/external/sqlite",
    "third_party/prebuilt/lvgl/host_macos",
]


REMOVED_PLACEHOLDER_DIRECTORIES = [
    "components/net",
    "examples",
    "tests/integration",
    "tests/target_smoke",
    "vendor/rtos",
]


def test_repository_layout_matches_task_requirements():
    repo_root = Path(__file__).resolve().parents[2]

    missing_directories = [
        path for path in REQUIRED_DIRECTORIES if not (repo_root / path).is_dir()
    ]

    assert not missing_directories, (
        "Missing required directories: " + ", ".join(missing_directories)
    )


def test_repository_does_not_keep_empty_future_placeholder_directories():
    repo_root = Path(__file__).resolve().parents[2]

    unexpected_directories = [
        path for path in REMOVED_PLACEHOLDER_DIRECTORIES if (repo_root / path).exists()
    ]

    assert not unexpected_directories, (
        "Unexpected empty placeholder directories: "
        + ", ".join(unexpected_directories)
    )


def test_repository_layout_document_explains_top_level_directories_in_chinese():
    repo_root = Path(__file__).resolve().parents[2]
    layout_doc = repo_root / "docs/architecture/repository-layout.md"

    assert layout_doc.is_file()

    content = layout_doc.read_text(encoding="utf-8")
    assert "仓库目录说明" in content
    assert "app/" in content
    assert "components/" in content
    assert "platforms/" in content
    assert "platforms/include/" in content
    assert "third_party/external/" in content
    assert "third_party/prebuilt/" in content
    assert "resources/" in content
    assert "平台资源路径接口" in content
    assert "vendor/" in content
    assert "不要直接修改预编译包里的 lv_conf.h" in content
    assert "不为远期想法预留空目录" in content


def test_project_overview_and_roadmap_document_current_direction():
    repo_root = Path(__file__).resolve().parents[2]
    overview_doc = repo_root / "docs/architecture/project-overview.md"
    roadmap_doc = repo_root / "docs/development/roadmap.md"

    assert overview_doc.is_file()
    assert roadmap_doc.is_file()

    overview = overview_doc.read_text(encoding="utf-8")
    assert "项目总览" in overview
    assert "跨平台嵌入式应用框架" in overview
    assert "host/macOS" in overview
    assert "平台能力注册表" in overview
    assert "设备管理组件" in overview
    assert "平台路径接口" in overview

    roadmap = roadmap_doc.read_text(encoding="utf-8")
    assert "项目路线图" in roadmap
    assert "阶段 1：host 框架跑通" in roadmap
    assert "阶段 2：平台能力注册表" in roadmap
    assert "阶段 3：设备管理组件" in roadmap
    assert "阶段 4：平台配置和资源管理" in roadmap
    assert "阶段 5：真实平台适配" in roadmap


def test_repository_does_not_keep_duplicate_legacy_third_party_roots():
    repo_root = Path(__file__).resolve().parents[2]

    assert not (repo_root / "third_party/EasyLogger").exists()
    assert not (repo_root / "third_party/lvgl").exists()


def test_repository_ignores_local_generated_files_and_macos_metadata():
    repo_root = Path(__file__).resolve().parents[2]
    gitignore = (repo_root / ".gitignore").read_text(encoding="utf-8")

    for ignored_path in [
        ".DS_Store",
        ".worktrees/",
        "__pycache__/",
        ".pytest_cache/",
        "build/",
        "out/",
    ]:
        assert ignored_path in gitignore


def test_default_host_config_profile_exists():
    repo_root = Path(__file__).resolve().parents[2]
    host_config = repo_root / "config/profiles/host.cfg"

    assert host_config.is_file()

    content = host_config.read_text(encoding="utf-8")
    assert "int log.level=3" in content
    assert "bool feature.enabled=true" in content
    assert "string device.name=host" in content
