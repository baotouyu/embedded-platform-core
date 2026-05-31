import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_file_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    file_cmake_path = REPO_ROOT / "components/file/CMakeLists.txt"

    assert "add_subdirectory(components/file)" in root_cmake
    assert file_cmake_path.exists()

    file_cmake = file_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_file STATIC" in file_cmake
    assert "src/ep_file.c" in file_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in file_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in file_cmake
