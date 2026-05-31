from pathlib import Path


def test_cmake_bootstrap_layout_matches_task_requirements():
    repo_root = Path(__file__).resolve().parents[2]
    top_level_cmake = (repo_root / "CMakeLists.txt").read_text(encoding="utf-8")

    assert "project(embedded-platform-core" in top_level_cmake
    assert "add_subdirectory(core)" in top_level_cmake
    assert "add_subdirectory(app)" in top_level_cmake
    assert "add_subdirectory(platforms)" in top_level_cmake
    assert "add_subdirectory(platforms/host/posix)" in top_level_cmake
    assert "EP_PLATFORM_FAMILY" in top_level_cmake


def test_platform_api_cmake_target_exposes_public_headers():
    repo_root = Path(__file__).resolve().parents[2]
    platform_cmake = (repo_root / "platforms/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_library(ep_platform_api INTERFACE)" in platform_cmake
    assert "target_include_directories(ep_platform_api" in platform_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in platform_cmake
