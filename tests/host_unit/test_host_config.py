import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_config_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    config_cmake_path = REPO_ROOT / "components/config/CMakeLists.txt"

    assert "add_subdirectory(components/config)" in root_cmake
    assert config_cmake_path.exists()

    config_cmake = config_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_config STATIC" in config_cmake
    assert "src/ep_config.c" in config_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in config_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in config_cmake
