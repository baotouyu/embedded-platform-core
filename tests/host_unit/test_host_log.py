import shutil
import subprocess
import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
COMPILER = shutil.which("clang") or shutil.which("cc")


def test_log_component_and_easylogger_are_wired_into_cmake():
    root_cmake = (REPO_ROOT / "CMakeLists.txt").read_text(encoding="utf-8")
    log_cmake_path = REPO_ROOT / "components/log/CMakeLists.txt"
    easylogger_root = REPO_ROOT / "third_party/external/EasyLogger"

    assert "add_subdirectory(components/log)" in root_cmake
    assert log_cmake_path.exists()

    log_cmake = log_cmake_path.read_text(encoding="utf-8")
    assert "add_library(ep_components_log STATIC" in log_cmake
    assert "src/ep_log.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/src/elog_utils.c" in log_cmake
    assert "third_party/external/EasyLogger/easylogger/port/elog_port.c" in log_cmake
    assert "${CMAKE_CURRENT_SOURCE_DIR}/include" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/third_party/external/EasyLogger/easylogger/inc" in log_cmake
    assert "${CMAKE_SOURCE_DIR}/osal/include" in log_cmake

    license_text = (easylogger_root / "LICENSE").read_text(encoding="utf-8")
    assert "The MIT License" in license_text
    assert "Copyright (c) 2015-2019 Armink" in license_text
