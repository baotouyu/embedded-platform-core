import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_timer_component_is_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    timer_cmake_path = REPO_ROOT / "components/timer/CMakeLists.txt"
    host_cmake = (REPO_ROOT / "platforms/host/posix/CMakeLists.txt").read_text(
        encoding="utf-8"
    )

    assert "add_subdirectory(components/timer)" in root_cmake
    assert timer_cmake_path.exists()

    timer_cmake = timer_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_timer STATIC" in timer_cmake
    assert "src/ep_timer.c" in timer_cmake
    assert "ep_components_event" in timer_cmake
    assert "PUBLIC" in timer_cmake
    assert "ep_components_timer" in host_cmake
