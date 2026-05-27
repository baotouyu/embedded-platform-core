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
    "components/net",
    "platforms/rtos/common",
    "platforms/linux/common",
    "vendor/rtos",
    "config/common",
    "config/feature",
    "config/profiles",
    "tests/host_unit",
    "tests/api_contract",
    "tests/integration",
    "tests/target_smoke",
    "tools/scripts",
    "tools/ci",
    "examples",
    "third_party/external/EasyLogger",
    "third_party/external/lvgl",
]


def test_repository_layout_matches_task_requirements():
    repo_root = Path(__file__).resolve().parents[2]

    missing_directories = [
        path for path in REQUIRED_DIRECTORIES if not (repo_root / path).is_dir()
    ]

    assert not missing_directories, (
        "Missing required directories: " + ", ".join(missing_directories)
    )
