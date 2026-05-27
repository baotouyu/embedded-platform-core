from pathlib import Path


def test_cmake_bootstrap_layout_matches_task_requirements():
    repo_root = Path(__file__).resolve().parents[2]
    top_level_cmake = (repo_root / "CMakeLists.txt").read_text(encoding="utf-8")

    assert "project(embedded-platform-core" in top_level_cmake
    assert "add_subdirectory(core)" in top_level_cmake
    assert "add_subdirectory(app)" in top_level_cmake
    assert "EP_PLATFORM_FAMILY" in top_level_cmake
